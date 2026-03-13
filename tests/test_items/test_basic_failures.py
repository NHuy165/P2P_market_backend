from decimal import Decimal
from types import CoroutineType
from typing import Any, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.exceptions.core import ExceptionResponse, ExceptionType
from src.models_schemas.items import Item, ItemStatus
from src.models_schemas.users import User
from tests.utils import response_validator_single

# ----- Item create ----- #


@pytest.mark.parametrize(
    "item_name, item_status, status_code, exception_type",
    [
        ("", "ACTIVE", 400, ExceptionType.REQUEST),
        ("item1", "ACTIVE", 409, ExceptionType.TAKEN_ITEM_NAME),
        ("item2", "BANNED", 400, ExceptionType.REQUEST),
    ],
)
async def test_create_item(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    item_name: str,
    item_status: str,
    status_code: int,
    exception_type: ExceptionType,
):
    """
    Fails to create an item using an empty name.
    Fails to create an item with a taken name.
    Fails to create an item with an invalid status.
    """

    await create_item(name="item1", seller=userA, status=ItemStatus.ACTIVE)

    item = {
        "name": item_name,
        "price": 10,
        "stock_quantity": 5,
        "status": item_status,
    }

    session.expire_all()

    response = await authorized_client.post("/items/create", json=item)

    response_validator_single(
        response,
        status_code,
        ExceptionResponse,
        {"exception_type": exception_type.value},
    )


# ----- Item read ----- #


async def test_read_private_item_one(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    create_user: Callable[..., CoroutineType[Any, Any, User]],
):
    """
    Fails to read a deleted item and fails to read another user's item.
    """

    # === Reads own deleted item === #

    item1 = await create_item(name="item1", seller=userA, status=ItemStatus.DELETED)
    item1_id = item1.id

    session.expire_all()

    response1 = await authorized_client.get(f"/items/my-items/{item1_id}")

    response_validator_single(response1, 404)

    # === Reads another user's item in private view === #

    user1 = await create_user("user1")
    item2 = await create_item(name="item2", seller=user1)
    item2_id = item2.id

    session.expire_all()

    response2 = await authorized_client.get(f"/items/my-items/{item2_id}")

    response_validator_single(response2, 404)


async def test_read_public_item_one(
    client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
):
    """
    Fails to read a suspended item by another user.
    """

    user1 = await create_user("user1")
    item1 = await create_item(name="item1", seller=user1, status=ItemStatus.SUSPENDED)
    item1_id = item1.id

    session.expire_all()

    response = await client.get(f"/items/{item1_id}")

    response_validator_single(
        response,
        404,
        ExceptionResponse,
        {"exception_type": ExceptionType.NOT_FOUND.value},
    )


# ----- Item update ----- #


@pytest.mark.parametrize(
    "item_status, update_info, status_code, exception_type",
    [
        (ItemStatus.BANNED, {}, 409, ExceptionType.INVALID_STATUS),
        (ItemStatus.ACTIVE, {"name": ""}, 400, ExceptionType.REQUEST),
        (ItemStatus.ACTIVE, {"name": None}, 400, ExceptionType.REQUEST),
        (
            ItemStatus.ACTIVE,
            {"stock_quantity_relative": -11},
            409,
            ExceptionType.INVALID_VALUE,
        ),
        (
            ItemStatus.ACTIVE,
            {"stock_quantity": 5, "stock_quantity_relative": -10},
            400,
            ExceptionType.RELATIVE_ABSOLUTE,
        ),
        (ItemStatus.ACTIVE, {"status": "BANNED"}, 400, ExceptionType.REQUEST),
    ],
)
async def test_update_item(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    item_status: ItemStatus,
    update_info: dict,
    status_code: int,
    exception_type: ExceptionType,
):
    """
    Fails to update a banned item.
    Fails to update an item with an empty name.
    Fails to update an item with a null name.
    Fails to update an item with a relative stock quantity resulting in a negative stock quantity.
    Fails to update an item while specifying both an absolute and a relative stock quantity.
    Fails to update an item with by setting its status to BANNED.
    """

    item1 = await create_item(
        name="item1",
        seller=userA,
        price=Decimal("10"),
        stock_quantity=10,
        status=item_status,
    )
    item1_id = item1.id

    session.expire_all()

    response = await authorized_client.patch(f"/items/{item1_id}", json=update_info)

    response_validator_single(
        response,
        status_code,
        ExceptionResponse,
        {"exception_type": exception_type.value},
    )


async def test_update_another_user_item(
    authorized_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
):
    """
    Fails to update another user's item.
    """

    user1 = await create_user("user1")
    item1 = await create_item(name="item1", seller=user1)
    item1_id = item1.id

    session.expire_all()

    response = await authorized_client.patch(
        f"/items/{item1_id}", json={"name": "item2"}
    )

    response_validator_single(
        response,
        404,
        ExceptionResponse,
        {"exception_type": ExceptionType.NOT_FOUND.value},
    )


# ----- Item delete ----- #


async def test_delete_item(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
):
    """
    Fails to delete a banned item.
    Fails to delete another user's item
    """

    # === Deletes own banned item === #

    item1 = await create_item(name="item1", seller=userA, status=ItemStatus.BANNED)
    item1_id = item1.id

    session.expire_all()

    response1 = await authorized_client.delete(f"/items/{item1_id}")

    response_validator_single(
        response1,
        409,
        ExceptionResponse,
        {"exception_type": ExceptionType.INVALID_STATUS.value},
    )

    # === Deletes another user's item === #

    user1 = await create_user("user1")
    item2 = await create_item(name="item1", seller=user1, status=ItemStatus.BANNED)
    item2_id = item2.id

    session.expire_all()

    response2 = await authorized_client.delete(f"/items/{item2_id}")

    response_validator_single(
        response2,
        404,
        ExceptionResponse,
        {"exception_type": ExceptionType.NOT_FOUND.value},
    )


@pytest.mark.parametrize("item_status", [ItemStatus.BANNED, ItemStatus.DELETED])
async def test_ban_item(
    admin_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    item_status: ItemStatus,
):
    """
    Fails to ban a banned item.
    Fails to ban a deleted item.
    """

    user1 = await create_user("user1")
    item1 = await create_item(name="item1", seller=user1, status=item_status)
    item1_id = item1.id

    session.expire_all()

    response = await admin_client.post(f"/admin/items/{item1_id}/ban")

    response_validator_single(
        response,
        409,
        ExceptionResponse,
        {"exception_type": ExceptionType.INVALID_STATUS.value},
    )


@pytest.mark.parametrize("item_status", [ItemStatus.ACTIVE, ItemStatus.DELETED])
async def test_unban_item(
    admin_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    item_status: ItemStatus,
):
    """
    Fails to unban an active item.
    Fails to unban a deleted item.
    """

    user1 = await create_user("user1")
    item1 = await create_item(name="item1", seller=user1, status=item_status)
    item1_id = item1.id

    session.expire_all()

    response = await admin_client.post(f"/admin/items/{item1_id}/unban")

    response_validator_single(
        response,
        409,
        ExceptionResponse,
        {"exception_type": ExceptionType.INVALID_STATUS.value},
    )
