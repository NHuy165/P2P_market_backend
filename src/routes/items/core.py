from typing import Annotated

from fastapi import APIRouter, Path

from ...core.database import SessionDep
from ...core.dependencies import UserDep
from ...exceptions.core import (
    ExceptionInvalidValue_409,
    ExceptionRelativeAbsolute_400,
    Responses,
)
from ...models_schemas.items import (
    ItemInput,
    ItemOutputPrivate,
    ItemOutputPrivateFull,
    ItemOutputPublic,
    ItemUpdate,
)
from ...repository.core import CriterionInput
from ...services.items import (
    create_item_service,
    delete_item_service,
    read_private_item_one_service,
    read_private_items_many_service,
    read_public_item_one_service,
    read_public_items_many_service,
    suspend_items_all_service,
    update_item_service,
)

router = APIRouter()

# ----- Item create ----- #


@router.post(
    "/create",
    response_model=ItemOutputPrivate,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
        409: Responses.RESPONSE_409_CONFLICT,
    },
)
async def create_item(user: UserDep, session: SessionDep, item: ItemInput):
    item_listing = await create_item_service(user, session, item)
    return item_listing


# ----- Item read ----- #


@router.post(
    "/my-items",
    response_model=list[ItemOutputPrivate],
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
    },
)
async def read_private_items_many(
    user: UserDep, session: SessionDep, criteria: list[CriterionInput] = []
):
    return await read_private_items_many_service(user, session, criteria)


@router.get(
    "/my-items/{item_id}",
    response_model=ItemOutputPrivateFull,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
        404: Responses.RESPONSE_404_NOT_FOUND,
    },
)
async def read_private_item_one(user: UserDep, session: SessionDep, item_id: int):
    return await read_private_item_one_service(user, session, item_id)


# Publicly reading items doesn't require users to be logged in


@router.post("", response_model=list[ItemOutputPublic])
async def read_public_items_many(
    session: SessionDep, criteria: list[CriterionInput] = []
):
    return await read_public_items_many_service(session, criteria)


@router.get(
    "/{item_id}",
    response_model=ItemOutputPublic,
    responses={404: Responses.RESPONSE_404_NOT_FOUND},
)
async def read_public_item_one(
    session: SessionDep, item_id: Annotated[int, Path(ge=0)]
):
    return await read_public_item_one_service(session, item_id)


# ----- Item update ----- #


@router.patch(
    "/{item_id}",
    response_model=ItemOutputPrivateFull,
    responses={
        400: Responses.RESPONSE_400_BAD_REQUEST,
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
        404: Responses.RESPONSE_404_NOT_FOUND,
        409: Responses.RESPONSE_409_CONFLICT,
    },
)
async def update_item(
    user: UserDep, session: SessionDep, item_id: int, item_update: ItemUpdate
):
    # Checks for obvious error in item_update

    # Entered both relative and absolute quantity
    if (
        item_update.stock_quantity is not None
        and item_update.stock_quantity_relative is not None
    ):
        raise ExceptionRelativeAbsolute_400()

    # Negative absolute quantity
    if item_update.stock_quantity is not None and item_update.stock_quantity < 0:
        raise ExceptionInvalidValue_409(
            "Item stock quantity", item_update.stock_quantity
        )

    assert user.id is not None
    new_item = await update_item_service(user, session, item_id, item_update)
    return new_item


@router.patch(
    "/",
    response_model=list[ItemOutputPrivate],
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
    },
)
async def suspend_items_all(user: UserDep, session: SessionDep):
    """
    Mainly used when users are about to delete their account. So their items do not get ordered anymore.
    """
    items_suspended = await suspend_items_all_service(user, session)
    return items_suspended


# ----- Item delete ----- #


@router.delete(
    "/{item_id}",
    response_model=ItemOutputPrivate,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
        404: Responses.RESPONSE_404_NOT_FOUND,
    },
)
async def delete_item(user: UserDep, session: SessionDep, item_id: int):
    item_deleted = await delete_item_service(user, session, item_id)
    return item_deleted
