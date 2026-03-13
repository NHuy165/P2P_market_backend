from decimal import Decimal
from types import CoroutineType
from typing import Any, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.models_schemas.enums import CompareOperator
from src.models_schemas.items import (
    Item,
    ItemInput,
    ItemOutputPrivate,
    ItemOutputPrivateFull,
    ItemOutputPublic,
    ItemStatus,
)
from src.models_schemas.users import User, UserStatus
from tests.utils import model_validator, response_validator_single

# ----- Item create ----- #


async def test_create_item(authorized_client: AsyncClient, session: AsyncSession):
    """
    Creates an item.
    """

    item = ItemInput(
        name="userA-item1",
        price=Decimal("3.67"),
        description="userA-item1-desc",
        stock_quantity=5,
        status=ItemStatus.SUSPENDED,
    )

    session.expire_all()

    response = await authorized_client.post(
        "/items/create",
        json=item.model_dump(mode="json"),
    )
    assert response.status_code == 200

    response_validator_single(
        response, 200, ItemOutputPrivate, item.model_dump()
    )  # No need to convert to json here because the response json will get converted back to Decimal


# ----- Item read ----- #


@pytest.mark.parametrize(
    "items_list, validate_list",
    [
        (
            [("item1", ItemStatus.ACTIVE), ("item2", ItemStatus.ACTIVE)],
            [("item1", ItemStatus.ACTIVE), ("item2", ItemStatus.ACTIVE)],
        ),
        (
            [("item1", ItemStatus.SUSPENDED), ("item2", ItemStatus.SUSPENDED)],
            [("item1", ItemStatus.SUSPENDED), ("item2", ItemStatus.SUSPENDED)],
        ),
        (
            [("item1", ItemStatus.SUSPENDED), ("item2", ItemStatus.BANNED)],
            [("item1", ItemStatus.SUSPENDED), ("item2", ItemStatus.BANNED)],
        ),
        (
            [("item1", ItemStatus.SUSPENDED), ("item2", ItemStatus.DELETED)],
            [("item1", ItemStatus.SUSPENDED)],
        ),
    ],
)
async def test_read_private_items_all(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    items_list: list[tuple[str, ItemStatus]],
    validate_list: list[tuple[str, ItemStatus]],
):
    """
    Reads all self-owned items (except deleted items).
    """

    for item_name, item_status in items_list:
        await create_item(name=item_name, seller=userA, status=item_status)

    session.expire_all()

    response = await authorized_client.post("/items/my-items")

    response_validator_single(response, 200)

    response_body = response.json()

    assert len(response_body) == len(validate_list)

    for i in range(len(validate_list)):
        model_validator(
            response_body[i],
            ItemOutputPrivate,
            {"name": validate_list[i][0], "status": validate_list[i][1]},
        )


@pytest.mark.parametrize(
    "user_status, items_list",
    [
        (
            UserStatus.ACTIVE,
            [("item1", ItemStatus.ACTIVE), ("item2", ItemStatus.SUSPENDED)],
        ),
        (
            UserStatus.BANNED,
            [("item1", ItemStatus.BANNED), ("item2", ItemStatus.DELETED)],
        ),
        (
            UserStatus.DELETED,
            [("item1", ItemStatus.BANNED), ("item2", ItemStatus.DELETED)],
        ),
    ],
)
async def test_read_private_items_all_admin(
    admin_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    user_status: UserStatus,
    items_list: list[tuple[str, ItemStatus]],
):
    """
    Reads all items belonging to a user, including deleted items.
    """

    user1 = await create_user(username="user1", status=user_status)
    user1_id = user1.id

    for item_name, item_status in items_list:
        await create_item(name=item_name, seller=user1, status=item_status)

    session.expire_all()

    response = await admin_client.post(f"/admin/items/{user1_id}")

    response_validator_single(response, 200)

    response_body = response.json()

    for i in range(len(items_list)):
        model_validator(
            response_body[i],
            ItemOutputPrivate,
            {"name": items_list[i][0], "status": items_list[i][1]},
        )


@pytest.mark.parametrize(
    "item_status",
    [
        ItemStatus.ACTIVE,
        ItemStatus.SUSPENDED,
        ItemStatus.BANNED,
    ],
)
async def test_read_private_item_one(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    item_status: ItemStatus,
):
    """
    Reads one self-owned item.
    """

    item = await create_item(name="item1", seller=userA, status=item_status)
    item_id = item.id

    session.expire_all()

    response = await authorized_client.get(f"/items/my-items/{item_id}")

    response_validator_single(
        response, 200, ItemOutputPrivateFull, {"name": "item1", "status": item_status}
    )


@pytest.mark.parametrize(
    "item_status",
    [
        ItemStatus.ACTIVE,
        ItemStatus.SUSPENDED,
        ItemStatus.BANNED,
        ItemStatus.DELETED,
    ],
)
async def test_read_private_item_one_admin(
    admin_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    item_status: ItemStatus,
):
    """
    Reads one item from the market, including deleted items.
    """

    user1 = await create_user("user1")

    item = await create_item(name="item1", seller=user1, status=item_status)
    item_id = item.id

    session.expire_all()

    response = await admin_client.get(f"/admin/items/{item_id}")

    response_validator_single(
        response, 200, ItemOutputPrivateFull, {"name": "item1", "status": item_status}
    )


async def test_read_public_items_all(
    client: AsyncClient,
    session: AsyncSession,
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    quick_login: Callable[..., CoroutineType[Any, Any, None]],
):
    """
    Reads all publicly listed items as a guest and as a logged in user.
    """

    user1 = await create_user("user1")

    await create_item(name="item1", seller=user1, status=ItemStatus.ACTIVE)
    await create_item(name="item2", seller=user1, status=ItemStatus.ACTIVE)
    await create_item(name="item3", seller=user1, status=ItemStatus.SUSPENDED)
    await create_item(name="item4", seller=user1, status=ItemStatus.BANNED)
    await create_item(name="item5", seller=user1, status=ItemStatus.DELETED)

    user2 = await create_user("user2")

    await create_item(name="item6", seller=user2, status=ItemStatus.ACTIVE)
    await create_item(name="item7", seller=user2, status=ItemStatus.SUSPENDED)

    # === Viewing as a guest === #

    session.expire_all()

    response1 = await client.post("items")

    response_validator_single(response1, 200)

    response1_body = response1.json()

    result1 = set()
    for item in response1_body:
        validated_item = ItemOutputPublic.model_validate(item)
        result1.add(validated_item.name)

    assert result1 == set(("item1", "item2", "item6"))

    # === Viewing as user1 === #

    token = await quick_login("user1")
    client.headers.update(token)

    session.expire_all()

    response2 = await client.post("items")

    response_validator_single(response2, 200)

    response2_body = response2.json()

    result2 = set()
    for item in response2_body:
        validated_item = ItemOutputPublic.model_validate(item)
        result2.add(validated_item.name)

    assert result2 == set(("item1", "item2", "item6"))


async def test_read_public_item_one(
    client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    quick_login: Callable[..., CoroutineType[Any, Any, None]],
):
    """
    Reads one item as a guest and as a logged in user.
    """

    user1 = await create_user("user1")
    item1 = await create_item(name="item1", seller=user1, status=ItemStatus.ACTIVE)
    item1_id = item1.id

    user2 = await create_user("user2")
    item2 = await create_item(name="item2", seller=user2, status=ItemStatus.ACTIVE)
    item2_id = item2.id

    # === Viewing as a guest === #

    session.expire_all()

    response1 = await client.get(f"/items/{item1_id}")

    response_validator_single(response1, 200, ItemOutputPublic, {"name": "item1"})

    # === Viewing user1's item1 as user1 === #

    token = await quick_login("user1")
    client.headers.update(token)

    session.expire_all()

    response2 = await client.get(f"/items/{item1_id}")

    response_validator_single(response2, 200, ItemOutputPublic, {"name": "item1"})

    # === Viewing item2 as user1 === #

    session.expire_all()

    response3 = await client.get(f"/items/{item2_id}")

    response_validator_single(response3, 200, ItemOutputPublic, {"name": "item2"})


# ----- Item update ----- #


@pytest.mark.parametrize(
    "item_update, item_validator",
    [
        (
            {"name": "item2", "price": "6.57"},
            {"name": "item2", "price": Decimal("6.57")},
        ),
        ({"status": ItemStatus.SUSPENDED.value}, {"status": ItemStatus.SUSPENDED}),
        ({"stock_quantity": 0}, {"stock_quantity": 0}),
        ({"stock_quantity_relative": -10}, {"stock_quantity": 0}),
    ],
)
async def test_update_item(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    item_update: dict,
    item_validator: dict,
):
    """
    Updates an item.
    """

    item1 = await create_item(
        name="item1",
        seller=userA,
        price=Decimal("10"),
        stock_quantity=10,
        status=ItemStatus.ACTIVE,
    )
    item1_id = item1.id

    session.expire_all()

    response = await authorized_client.patch(f"/items/{item1_id}", json=item_update)

    response_validator_single(response, 200, ItemOutputPrivateFull, item_validator)


@pytest.mark.parametrize(
    "items_list, validate_list",
    [
        (
            [("item1", ItemStatus.ACTIVE), ("item2", ItemStatus.ACTIVE)],
            [("item1", ItemStatus.SUSPENDED), ("item2", ItemStatus.SUSPENDED)],
        ),
        (
            [("item1", ItemStatus.ACTIVE), ("item2", ItemStatus.SUSPENDED)],
            [("item1", ItemStatus.SUSPENDED)],
        ),
    ],
)
async def test_suspend_all_items(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    items_list: list[tuple[str, ItemStatus]],
    validate_list: list[tuple[str, ItemStatus]],
):
    """
    Use the suspend-all-item functionality (normally used when deleting account).
    """

    for item_name, item_status in items_list:
        await create_item(name=item_name, seller=userA, status=item_status)

    session.expire_all()

    response = await authorized_client.patch("/items/")

    response_validator_single(response, 200)

    response_body = response.json()

    assert len(response_body) == len(validate_list)

    for i in range(len(validate_list)):
        model_validator(
            response_body[i],
            ItemOutputPrivate,
            {"name": validate_list[i][0], "status": validate_list[i][1]},
        )


# ----- Item delete ----- #


@pytest.mark.parametrize(
    "item_status",
    [
        ItemStatus.ACTIVE,
        ItemStatus.SUSPENDED,
    ],
)
async def test_delete_item(
    authorized_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    item_status: ItemStatus,
):
    """
    Deletes an item.
    """

    item1 = await create_item(name="item1", seller=userA, status=item_status)
    item1_id = item1.id

    session.expire_all()

    response = await authorized_client.delete(f"/items/{item1_id}")

    response_validator_single(
        response,
        200,
        ItemOutputPrivate,
        {"status": ItemStatus.DELETED, "deleted_at": (None, CompareOperator.NE)},
    )


@pytest.mark.parametrize(
    "item_status",
    [
        ItemStatus.ACTIVE,
        ItemStatus.SUSPENDED,
    ],
)
async def test_ban_item(
    admin_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
    item_status: ItemStatus,
):
    """
    Bans an item.
    """

    user1 = await create_user("user1")
    item1 = await create_item(name="item1", seller=user1, status=item_status)
    item1_id = item1.id

    session.expire_all()

    response = await admin_client.post(f"/admin/items/{item1_id}/ban")

    response_validator_single(
        response,
        200,
        ItemOutputPrivateFull,
        {"status": ItemStatus.BANNED, "banned_at": (None, CompareOperator.NE)},
    )


async def test_unban_item(
    admin_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    create_item: Callable[..., CoroutineType[Any, Any, Item]],
):
    """
    Unbans an item.
    """

    user1 = await create_user("user1")
    item1 = await create_item(name="item1", seller=user1, status=ItemStatus.BANNED)
    item1_id = item1.id

    session.expire_all()

    response = await admin_client.post(f"/admin/items/{item1_id}/unban")

    response_validator_single(
        response,
        200,
        ItemOutputPrivateFull,
        {"status": ItemStatus.SUSPENDED, "banned_at": None},
    )
