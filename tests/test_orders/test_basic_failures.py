from decimal import Decimal
from types import CoroutineType
from typing import Any, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.exceptions.core import ExceptionResponse, ExceptionType
from src.models_schemas.enums import ItemStatus
from src.models_schemas.items import Item
from src.models_schemas.orders import OrderInput, OrderOutputNoType
from src.models_schemas.users import User
from tests.utils import response_validator_single

# ----- Order create ----- #


@pytest.mark.parametrize(
    "item_status, quantity, status_code, exception_type",
    [
        (ItemStatus.ACTIVE, 3, 409, ExceptionType.INVALID_VALUE),
        (ItemStatus.SUSPENDED, 2, 404, ExceptionType.NOT_FOUND),
    ],
)
async def test_create_order(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    change_money: Callable[..., CoroutineType[Any, Any, User]],
    item_status: ItemStatus,
    quantity: int,
    status_code: int,
    exception_type: ExceptionType,
):
    """
    Fails to create an order with insufficient money.
    Fails to create an order for a suspended item.
    """

    await change_money(user=userA, amount=Decimal("10.00"))

    user1 = await create_user("user1")
    item1 = await create_item(
        name="item1",
        seller=user1,
        price=Decimal("5"),
        stock_quantity=3,
        status=item_status,
    )
    item1_id = item1.id
    assert item1_id is not None

    order = OrderInput(quantity=quantity, item_id=item1_id)

    session.expire_all()

    response = await authorized_client.post("orders/create", json=order.model_dump())

    response_validator_single(
        response,
        status_code,
        ExceptionResponse,
        {"exception_type": exception_type},
    )


# ----- Order read ----- #


# ----- Order update ----- #


@pytest.mark.parametrize(
    "action",
    [
        "approve",
        "complete",
    ],
)
async def test_approve_complete_order(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    admin_client: AsyncClient,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    change_money: Callable[..., CoroutineType[Any, Any, User]],
    complete_order: Callable[..., CoroutineType[Any, Any, None]],
    quickbuy: Callable[..., CoroutineType[Any, Any, OrderOutputNoType]],
    action: str,
):
    """
    Fails to approve an order not of PENDING state.
    Fails to complete an order not of SHIPPED state.
    """

    await change_money(user=userA, amount=Decimal("10"))

    user1 = await create_user("user1")
    item1 = await create_item(
        "item1", seller=user1, price=Decimal("5"), stock_quantity=2
    )
    item1_id = item1.id
    assert item1_id is not None

    order = await quickbuy(
        custom_client=authorized_client, item_id=item1_id, quantity=2
    )
    order_id = order.id

    await complete_order(order_id=order_id)

    session.expire_all()

    response = await admin_client.patch(f"/admin/orders/{order_id}/{action}")

    response_validator_single(
        response,
        409,
        ExceptionResponse,
        {"exception_type": ExceptionType.INVALID_STATUS},
    )


# ----- Order delete ----- #


@pytest.mark.parametrize("admin", [False, True])
async def test_delete_order(
    authorized_client: AsyncClient,
    admin_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    change_money: Callable[..., CoroutineType[Any, Any, User]],
    complete_order: Callable[..., CoroutineType[Any, Any, None]],
    quickbuy: Callable[..., CoroutineType[Any, Any, OrderOutputNoType]],
    admin: bool,
):
    """
    Fails to delete a non-pending order as a user and as an admin.
    """

    await change_money(user=userA, amount=Decimal("10"))

    user1 = await create_user("user1")
    item1 = await create_item(
        "item1", seller=user1, price=Decimal("5"), stock_quantity=2
    )
    item1_id = item1.id
    assert item1_id is not None

    order = await quickbuy(
        custom_client=authorized_client, item_id=item1_id, quantity=2
    )
    order_id = order.id

    await complete_order(order_id=order_id)

    session.expire_all()

    if admin:
        response = await admin_client.delete(f"/admin/orders/{order_id}")
    else:
        response = await authorized_client.delete(f"/orders/{order_id}")

    response_validator_single(
        response,
        409,
        ExceptionResponse,
        {"exception_type": ExceptionType.INVALID_STATUS},
    )
