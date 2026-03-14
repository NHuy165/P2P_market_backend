from decimal import Decimal
from types import CoroutineType
from typing import Any, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.models_schemas.enums import TransactionStatus, TransactionType
from src.models_schemas.items import Item
from src.models_schemas.orders import OrderOutputNoType
from src.models_schemas.transactions import TransactionInput, TransactionOutput
from src.models_schemas.users import User
from tests.utils import response_validator_single, validate_results

# ----- Transaction create ----- #


@pytest.mark.parametrize(
    "action, trans_type, final_balance",
    [
        ("deposit", TransactionType.DEPOSIT, Decimal("20")),
        ("withdraw", TransactionType.WITHDRAWAL, Decimal("0")),
    ],
)
async def test_deposit_withdraw(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    change_money: Callable[..., CoroutineType[Any, Any, User]],
    action: str,
    trans_type: TransactionType,
    final_balance: Decimal,
):
    """
    Deposits and withdraws money.
    """

    await change_money(user=userA, amount=Decimal("10"))

    inp = TransactionInput(
        amount=Decimal("10"),
    )

    session.expire_all()

    response = await authorized_client.post(
        f"/transactions/{action}", json=inp.model_dump(mode="json")
    )

    response_validator_single(
        response,
        200,
        TransactionOutput,
        {
            "user_id": userA.id,
            "type": trans_type,
            "status": TransactionStatus.SUCCESS,
            "amount": Decimal("10"),
        },
    )

    assert userA.balance == final_balance


@pytest.mark.parametrize(
    "action, trans_type, final_balance",
    [
        ("add", TransactionType.ADMIN_ADD, Decimal("20")),
        ("subtract", TransactionType.ADMIN_SUBTRACT, Decimal("0")),
    ],
)
async def test_add_subtract_admin(
    admin_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    action: str,
    trans_type: TransactionType,
    final_balance: Decimal,
):
    """
    Adds and subtracts money to and from an account as an admin.
    """

    user1 = await create_user("user1", balance=Decimal("10"))
    user1_id = user1.id

    inp = TransactionInput(
        amount=Decimal("10"),
    )

    session.expire_all()

    response = await admin_client.post(
        f"/admin/transactions/{user1_id}/{action}", json=inp.model_dump(mode="json")
    )

    response_validator_single(
        response,
        200,
        TransactionOutput,
        {
            "user_id": user1_id,
            "type": trans_type,
            "status": TransactionStatus.SUCCESS,
            "amount": Decimal("10"),
        },
    )

    assert user1.balance == final_balance


# ----- Transaction read ----- #


async def test_read_transactions(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    change_money: Callable[..., CoroutineType[Any, Any, User]],
    quickbuy: Callable[..., CoroutineType[Any, Any, OrderOutputNoType]],
    complete_order: Callable[..., CoroutineType[Any, Any, None]],
    cancel_order: Callable[..., CoroutineType[Any, Any, None]],
    quick_login: Callable[..., CoroutineType[Any, Any, dict]],
):
    """
    Reads transactions after an order gets created and after an order completes (either by cancelling or finishing).
    """

    # Setup: userA will make 1 successful buy order, 1 cancelled buy order and have 1 successful sell order, 1 cancelled sell order.

    # Users
    user1 = await create_user("user1")

    await change_money(user=userA, amount=Decimal("3.00"))
    await change_money(user=user1, amount=Decimal("7.00"))

    # Items
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

    item4 = await create_item(
        name="item4",
        seller=userA,
        price=Decimal("4"),
        stock_quantity=1,
    )
    item4_id = item4.id

    # Orders
    order1 = await quickbuy(
        custom_client=authorized_client,
        item_id=item1_id,
        quantity=1,
    )
    order1_id = order1.id

    order2 = await quickbuy(
        custom_client=authorized_client,
        item_id=item2_id,
        quantity=1,
    )
    order2_id = order2.id

    token = await quick_login("user1")
    authorized_client.headers.update(token)

    order3 = await quickbuy(
        custom_client=authorized_client,
        item_id=item3_id,
        quantity=1,
    )
    order3_id = order3.id

    order4 = await quickbuy(
        custom_client=authorized_client,
        item_id=item4_id,
        quantity=1,
    )
    order4_id = order4.id

    token = await quick_login("userA")
    authorized_client.headers.update(token)

    # === Validate after order creation === #

    session.expire_all()

    response1 = await authorized_client.post("/transactions")

    response_validator_single(response1, 200)

    response1_body = response1.json()

    validate_results(
        response1_body,
        ["order_id", "user_id", "type", "status", "amount"],
        {
            (
                order1_id,
                userA.id,
                TransactionType.PURCHASE,
                TransactionStatus.SUCCESS,
                Decimal("1"),
            ),
            (
                order2_id,
                userA.id,
                TransactionType.PURCHASE,
                TransactionStatus.SUCCESS,
                Decimal("2"),
            ),
            (
                order3_id,
                userA.id,
                TransactionType.SALE,
                TransactionStatus.ON_HOLD,
                Decimal("3"),
            ),
            (
                order4_id,
                userA.id,
                TransactionType.SALE,
                TransactionStatus.ON_HOLD,
                Decimal("4"),
            ),
        },
        TransactionOutput,
    )

    # Completing and cancelling:

    await complete_order(order1_id)
    await cancel_order(order2_id)
    await complete_order(order3_id)
    await cancel_order(order4_id)

    # === Validate after order completion === #

    session.expire_all()

    response2 = await authorized_client.post("/transactions")

    response_validator_single(response2, 200)

    response2_body = response2.json()

    validate_results(
        response2_body,
        ["order_id", "user_id", "type", "status", "amount"],
        {
            (
                order1_id,
                userA.id,
                TransactionType.PURCHASE,
                TransactionStatus.SUCCESS,
                Decimal("1"),
            ),
            (
                order2_id,
                userA.id,
                TransactionType.PURCHASE,
                TransactionStatus.SUCCESS,
                Decimal("2"),
            ),
            (
                order2_id,
                userA.id,
                TransactionType.REFUND,
                TransactionStatus.SUCCESS,
                Decimal("2"),
            ),
            (
                order3_id,
                userA.id,
                TransactionType.SALE,
                TransactionStatus.SUCCESS,
                Decimal("3"),
            ),
            (
                order4_id,
                userA.id,
                TransactionType.SALE,
                TransactionStatus.FAILED,
                Decimal("4"),
            ),
        },
        TransactionOutput,
    )


# ----- Transaction update ----- #


# ----- Transaction delete ----- #
