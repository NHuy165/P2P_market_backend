from decimal import Decimal
from types import CoroutineType
from typing import Any, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models_schemas.enums import (
    CompareOperator,
    OrderStatus,
    TransactionStatus,
    TransactionType,
)
from src.models_schemas.items import Item
from src.models_schemas.orders import OrderInput, OrderOutput, OrderOutputNoType
from src.models_schemas.transactions import Transaction
from src.models_schemas.users import User
from tests.utils import response_validator_single, validate_results

# ----- Order create ----- #


async def test_create_finish_order(
    authorized_client: AsyncClient,
    userA: User,
    admin_client: AsyncClient,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    change_money: Callable[..., CoroutineType[Any, Any, User]],
    fetch_transactions: Callable[..., CoroutineType[Any, Any, list[Transaction]]],
):
    """
    Creates an order, validating contents and statuses of the orders and transactions.
    Approving and finishing the order via admin endpoints, validating final balance results.
    """
    # === Validate order === #

    await change_money(user=userA, amount=Decimal("10.00"))

    user1 = await create_user("user1")
    item1 = await create_item(
        name="item1", seller=user1, price=Decimal("5"), stock_quantity=2
    )
    item1_id = item1.id
    assert item1_id is not None

    order = OrderInput(quantity=2, item_id=item1_id)

    response1 = await authorized_client.post("orders/create", json=order.model_dump())

    validate = {"price_per_item": Decimal("5")}
    validate.update(order.model_dump())

    response_validator_single(
        response1,
        200,
        OrderOutputNoType,
        validate,
    )

    # === Validate transactions === #

    order_id = response1.json()["id"]

    trans = await fetch_transactions()

    validate_results(
        trans,
        ["order_id", "user_id", "type", "status", "amount"],
        {
            frozenset(
                (
                    order_id,
                    userA.id,
                    TransactionType.PURCHASE,
                    TransactionStatus.SUCCESS,
                    Decimal("10"),
                )
            ),
            frozenset(
                (
                    order_id,
                    user1.id,
                    TransactionType.SALE,
                    TransactionStatus.ON_HOLD,
                    Decimal("10"),
                )
            ),
        },
    )

    assert userA.balance == Decimal("0")
    assert user1.balance == Decimal("0")

    # === Validate balance after order completion === #

    response2 = await admin_client.patch(f"/admin/orders/{order_id}/approve")

    response_validator_single(
        response2, 200, OrderOutputNoType, {"status": OrderStatus.SHIPPED}
    )

    response3 = await admin_client.patch(f"/admin/orders/{order_id}/complete")

    response_validator_single(
        response3,
        200,
        OrderOutputNoType,
        {"status": OrderStatus.DELIVERED, "finished_at": (None, CompareOperator.NE)},
    )

    assert user1.balance == Decimal("10")


# ----- Order read ----- #


@pytest.mark.parametrize(
    "admin, type",
    [
        (False, None),
        (False, True),
        (False, False),
        (True, None),
        (True, True),
        (True, False),
    ],
)
async def test_read_orders(
    authorized_client: AsyncClient,
    admin_client: AsyncClient,
    userA: User,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    change_money: Callable[..., CoroutineType[Any, Any, User]],
    quick_login: Callable[..., CoroutineType[Any, Any, dict]],
    quickbuy: Callable[..., CoroutineType[Any, Any, OrderOutputNoType]],
    admin: bool,
    type: bool | None,
):
    """
    Reads private buy orders and sell orders as a user and as an admin.
    """

    # Setup: user1 has item1 and item2, userA has item3. Each user buys everything from the other one.

    user1 = await create_user("user1")

    userA = await change_money(user=userA, amount=Decimal("3"))
    user1 = await change_money(user=user1, amount=Decimal("3"))

    item1 = await create_item(
        name="item1",
        seller=user1,
        price=Decimal("1"),
        stock_quantity=1,
    )
    item1_id = item1.id

    item2 = await create_item(
        name="item2",
        seller=user1,
        price=Decimal("2"),
        stock_quantity=1,
    )
    item2_id = item2.id

    item3 = await create_item(
        name="item3",
        seller=userA,
        price=Decimal("3"),
        stock_quantity=1,
    )
    item3_id = item3.id

    await quickbuy(custom_client=authorized_client, item_id=item1_id, quantity=1)
    await quickbuy(custom_client=authorized_client, item_id=item2_id, quantity=1)

    token = await quick_login("user1")
    authorized_client.headers.update(token)

    await quickbuy(custom_client=authorized_client, item_id=item3_id, quantity=1)

    token = await quick_login("userA")
    authorized_client.headers.update(token)

    # Validate

    if admin:
        response = await admin_client.post(
            f"/admin/orders/{userA.id}{'?type=' + str(type) if isinstance(type, bool) else ''}"
        )
    else:
        response = await authorized_client.post(
            f"/orders{'?type=' + str(type) if isinstance(type, bool) else ''}"
        )

    response_validator_single(response, 200)

    response_body = response.json()

    correct = set()
    if type is True:
        correct.add(frozenset(("SELL", userA.id, user1.id, item3.id, Decimal("3"))))
    elif type is False:
        correct.add(frozenset(("BUY", user1.id, userA.id, item1.id, Decimal("1"))))
        correct.add(frozenset(("BUY", user1.id, userA.id, item2.id, Decimal("2"))))
    else:
        correct.add(frozenset(("SELL", userA.id, user1.id, item3.id, Decimal("3"))))
        correct.add(frozenset(("BUY", user1.id, userA.id, item1.id, Decimal("1"))))
        correct.add(frozenset(("BUY", user1.id, userA.id, item2.id, Decimal("2"))))

    validate_results(
        response_body,
        ["type", "seller_id", "buyer_id", "item_id", "price_per_item"],
        correct,
        validate=OrderOutput,
    )


# ----- Order update ----- #

# ----- Order delete ----- #


@pytest.mark.parametrize("admin", [False, True])
async def test_delete_order(
    authorized_client: AsyncClient,
    admin_client: AsyncClient,
    userA: User,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    change_money: Callable[..., CoroutineType[Any, Any, User]],
    quickbuy: Callable[..., CoroutineType[Any, Any, OrderOutputNoType]],
    fetch_transactions: Callable[[], CoroutineType[Any, Any, list[Transaction]]],
    admin: bool,
):
    """
    Deletes a pending order as a user and as an admin.
    """

    # === Validate order === #

    await change_money(user=userA, amount=Decimal("10.00"))

    user1 = await create_user("user1")
    item1 = await create_item(
        name="item1", seller=user1, price=Decimal("5"), stock_quantity=2
    )
    item1_id = item1.id

    order = await quickbuy(
        custom_client=authorized_client, item_id=item1_id, quantity=2
    )
    order_id = order.id

    if admin:
        response = await admin_client.delete(f"/admin/orders/{order_id}")
    else:
        response = await authorized_client.delete(f"/orders/{order_id}")

    response_validator_single(
        response,
        200,
        OrderOutputNoType,
        {
            "id": order_id,
            "status": OrderStatus.CANCELLED,
            "finished_at": (None, CompareOperator.NE),
        },
    )

    # === Validate transactions === #

    trans = await fetch_transactions()

    validate_results(
        trans,
        ["order_id", "user_id", "type", "status", "amount"],
        {
            frozenset(
                (
                    order_id,
                    userA.id,
                    TransactionType.PURCHASE,
                    TransactionStatus.SUCCESS,
                    Decimal("10"),
                )
            ),
            frozenset(
                (
                    order_id,
                    userA.id,
                    TransactionType.REFUND,
                    TransactionStatus.SUCCESS,
                    Decimal("10"),
                )
            ),
            frozenset(
                (
                    order_id,
                    user1.id,
                    TransactionType.SALE,
                    TransactionStatus.FAILED,
                    Decimal("10"),
                )
            ),
        },
    )

    assert userA.balance == Decimal("10")
    assert user1.balance == Decimal("0")
