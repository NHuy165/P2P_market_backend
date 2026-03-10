from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions.core import (
    ExceptionInvalidStatus_409,
    ExceptionInvalidValue_409,
    ExceptionNotFound_404,
    ExceptionTakenItemName_409,
    ObjectType,
)
from ..models_schemas.items import (
    Item,
    ItemInput,
    ItemStatus,
    ItemUpdate,
)
from ..models_schemas.users import User
from ..repository.core import CriterionInput
from ..repository.items import GetItem
from ..repository.users import GetUser

# ----- Item create ----- #


async def create_item_service(
    user: User, session: AsyncSession, item: ItemInput
) -> Item:
    # Checks for overlapping names
    get_item = GetItem()
    get_item.base_private()
    get_item.get_by("seller_id", user.id)
    get_item.get_by("name", item.name)

    existing = await get_item.get_one(session)

    if existing is not None:
        raise ExceptionTakenItemName_409()

    listing = Item(**item.model_dump(), seller=user)

    session.add(listing)
    await session.commit()
    await session.refresh(listing, attribute_names=["seller"])

    return listing


# ----- Item read ----- #


async def read_private_items_many_service(
    user: User, session: AsyncSession, criteria: list[CriterionInput] = []
) -> list[Item]:
    get_item = GetItem()
    get_item.base_existing()
    get_item.eager_load(["seller"])
    get_item.get_by("seller_id", user.id)

    items = await get_item.get_many(session, criteria)
    return items


async def read_private_items_many_admin_service(
    session: AsyncSession, user_id: int, criteria: list[CriterionInput] = []
) -> list[Item]:
    user_get = GetUser()
    user_get.base_all()
    user_get.get_by("id", user_id)

    user = await user_get.get_one(session)

    if user is None:
        raise ExceptionNotFound_404(ObjectType.USER, user_id)

    get_item = GetItem()
    get_item.base_all()
    get_item.eager_load(["seller"])
    get_item.get_by("seller_id", user.id)

    items = await get_item.get_many(session, criteria)
    return items


async def read_private_item_one_service(
    user: User, session: AsyncSession, item_id: int
) -> Item | None:
    get_item = GetItem()
    get_item.base_existing()
    get_item.eager_load_all()
    get_item.get_by("seller_id", user.id)
    get_item.get_by("id", item_id)

    item = await get_item.get_one(session)

    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)

    return item


async def read_private_item_one_admin_service(
    session: AsyncSession, item_id: int
) -> Item | None:
    get_item = GetItem()
    get_item.base_all()
    get_item.eager_load_all()
    get_item.get_by("id", item_id)

    item = await get_item.get_one(session)

    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)

    return item


async def read_public_items_many_service(
    session: AsyncSession, criteria: list[CriterionInput] = []
) -> list[Item]:
    get_item = GetItem()
    get_item.base_public()
    get_item.eager_load(["seller"])

    items = await get_item.get_many(session, criteria)
    return items


async def read_public_item_one_service(
    session: AsyncSession, item_id: int
) -> Item | None:
    get_item = GetItem()
    get_item.base_public()
    get_item.eager_load(["seller"])
    get_item.get_by("id", item_id)

    item = await get_item.get_one(session)

    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)

    return item


# ----- Item update ----- #


async def update_item_service(
    user: User, session: AsyncSession, item_id: int, item_update: ItemUpdate
) -> Item:
    # Cannot edit banned and deleted items.
    get_item = GetItem()
    get_item.base_existing()
    get_item.get_by("seller_id", user.id)
    get_item.get_by("id", item_id)

    item = await get_item.get_one(session, with_for_update=True)

    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)

    if item.status is ItemStatus.BANNED:
        raise ExceptionInvalidStatus_409(ObjectType.ITEM, ItemStatus.BANNED)

    # Negative relative quantity
    if (
        item_update.stock_quantity_relative is not None
        and item_update.stock_quantity_relative + item.stock_quantity < 0
    ):
        raise ExceptionInvalidValue_409(
            "Item stock quantity",
            item_update.stock_quantity_relative + item.stock_quantity,
        )

    # Activate/suspend overlap
    if item_update.status == item.status:
        raise ExceptionInvalidStatus_409(ObjectType.ITEM, item.status.value)

    # Actual update code
    update_data = item_update.model_dump(exclude_unset=True)

    if item_update.stock_quantity_relative is not None:
        update_data["stock_quantity"] = (
            item.stock_quantity + item_update.stock_quantity_relative
        )

    item.sqlmodel_update(update_data)

    session.add(item)
    await session.commit()
    await session.refresh(item, attribute_names=["seller", "orders"])

    return item


# Used for when you want to delete your account
async def suspend_items_all_service(user: User, session: AsyncSession) -> list[Item]:
    get_item = GetItem()
    get_item.base_public()  # Only fetches active items
    get_item.get_by("seller_id", user.id)

    items = await get_item.get_many(session, with_for_update=True)

    for item in items:
        item.status = ItemStatus.SUSPENDED

    session.add_all(items)
    await session.commit()
    for item in items:
        await session.refresh(item)

    return items


# ----- Item delete ----- #


async def delete_item_service(user: User, session: AsyncSession, item_id: int) -> Item:
    get_item = GetItem()
    get_item.base_existing()
    get_item.get_by("seller_id", user.id)
    get_item.get_by("id", item_id)

    item = await get_item.get_one(session, with_for_update=True)

    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)

    if item.status is ItemStatus.BANNED:
        raise ExceptionInvalidStatus_409(ObjectType.ITEM, ItemStatus.BANNED)

    # Soft delete so pending orders still have to get delivered.
    item.status = ItemStatus.DELETED
    item.deleted_at = datetime.now(timezone.utc)

    session.add(item)
    await session.commit()
    await session.refresh(item, attribute_names=["seller"])

    return item


async def delete_items_all_service(user: User, session: AsyncSession) -> list[Item]:
    """
    This function is automatically called upon user deletion.
    """
    get_item = GetItem()
    get_item.base_existing()
    get_item.get_by("seller_id", user.id)

    items = await get_item.get_many(session, with_for_update=True)

    for item in items:
        if item.status is ItemStatus.BANNED:
            raise ExceptionInvalidStatus_409(ObjectType.ITEM, ItemStatus.BANNED)
        item.status = ItemStatus.DELETED
        item.deleted_at = datetime.now(timezone.utc)

    session.add_all(items)
    await session.commit()
    for item in items:
        await session.refresh(item, attribute_names=["seller"])

    return items


async def change_item_ban_status_service(
    session: AsyncSession, item_id: int, ban: bool
) -> Item:
    get_item = GetItem()
    get_item.base_all()
    get_item.get_by("id", item_id)

    item = await get_item.get_one(session, with_for_update=True)

    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)

    if item.status is ItemStatus.DELETED:
        raise ExceptionInvalidStatus_409(ObjectType.ITEM, ItemStatus.DELETED.value)

    if (item.status is ItemStatus.BANNED and ban is True) or (
        item.status is not ItemStatus.BANNED and ban is False
    ):
        raise ExceptionInvalidStatus_409(ObjectType.ITEM, item.status.value)

    if item.status is ItemStatus.BANNED:
        item.status = ItemStatus.SUSPENDED
        item.banned_at = None
    else:
        item.status = ItemStatus.BANNED
        item.banned_at = datetime.now(timezone.utc)

    session.add(item)
    await session.commit()
    await session.refresh(item, attribute_names=["seller", "orders"])

    return item
