from fastapi import APIRouter, status, HTTPException, Path, Query
from typing import Annotated

from src.core.dependencies import UserDep

from ...core.database import SessionDep
from ...models_schemas.items import ItemInput, ItemOutput, ItemUpdate, ItemOutputPrivate, ItemSortFilterPrivate, ItemSortFilterPublic
from ...services.items.core import create_item_service, delete_items_all_service, restore_item_service, update_item_service, read_private_items_many_service, read_public_items_many_service, read_private_item_one_service, read_public_item_one_service, delete_item_service
from ...models_schemas.exceptions import *

router = APIRouter()

# ----- Item create ----- #

@router.post("/create", response_model=ItemOutputPrivate,
             responses={
                 401: Responses.RESPONSE_401_UNAUTHORIZED,
                 403: Responses.RESPONSE_403_FORBIDDEN,
                 409: Responses.RESPONSE_409_CONFLICT
             })
def create_item(user: UserDep, session: SessionDep, item: ItemInput):
    item_listing = create_item_service(user, session, item)
    return item_listing
                
# ----- Item read ----- #

@router.get("/my-items/", response_model=list[ItemOutputPrivate],
            responses={
                401: Responses.RESPONSE_401_UNAUTHORIZED,
                403: Responses.RESPONSE_403_FORBIDDEN,
            })
def read_private_items_all(user: UserDep, session: SessionDep):
    return read_private_items_many_service(user, session)

@router.get("/my-items", response_model=list[ItemOutputPrivate],
            responses={
                401: Responses.RESPONSE_401_UNAUTHORIZED,
                403: Responses.RESPONSE_403_FORBIDDEN,
            })
def read_private_items_sort_filter(user: UserDep, session: SessionDep, sort_filter: Annotated[ItemSortFilterPrivate, Query()]):
    return read_private_items_many_service(user, session, sort_filter)

@router.get("/my-items/{item_id}", response_model=ItemOutputPrivate,
            responses={
                401: Responses.RESPONSE_401_UNAUTHORIZED,
                403: Responses.RESPONSE_403_FORBIDDEN,
                404: Responses.RESPONSE_404_NOT_FOUND
            })
def read_private_item_one(user: UserDep, session: SessionDep, item_id: Annotated[int, Path(ge=0)]):
    return read_private_item_one_service(user, session, item_id)

# These functions below don't require user to be logged in

@router.get("/", response_model=list[ItemOutput])
def read_public_items_all(session: SessionDep):
    return read_public_items_many_service(session)

@router.get("", response_model=list[ItemOutput])
def read_public_items_sort_filter(session: SessionDep, sort_filter: Annotated[ItemSortFilterPublic, Query()]):
    return read_public_items_many_service(session, sort_filter)

@router.get("/{item_id}", response_model=ItemOutput,
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND
            })
def read_public_item_one(session: SessionDep, item_id: Annotated[int, Path(ge=0)]):
    return read_public_item_one_service(session, item_id)


# ----- Item update ----- #
        
@router.patch("/{item_id}", response_model=ItemOutputPrivate,
              responses={
                  400: Responses.RESPONSE_400_BAD_REQUEST,
                  401: Responses.RESPONSE_401_UNAUTHORIZED,
                  403: Responses.RESPONSE_403_FORBIDDEN,
                  404: Responses.RESPONSE_404_NOT_FOUND,
                  409: Responses.RESPONSE_409_CONFLICT,
              })
def update_item(user: UserDep, session: SessionDep, item_id: int, item_update: ItemUpdate):
    # Checks for obvious error in item_update
    
    # Entered both relative and absolute quantity
    if item_update.stock_quantity is not None and item_update.stock_quantity_relative is not None:
        raise ExceptionRelativeAbsolute_400()
        
    # Negative absolute quantity
    if item_update.stock_quantity is not None and item_update.stock_quantity < 0:
        raise ExceptionInvalidValue_409("Item stock quantity", item_update.stock_quantity)

    assert user.id is not None
    new_item = update_item_service(user, session, item_id, item_update)
    return new_item
        
# ----- Item delete ----- #

@router.delete("/{item_id}", response_model=ItemOutputPrivate,
               responses={
                   401: Responses.RESPONSE_401_UNAUTHORIZED,
                   403: Responses.RESPONSE_403_FORBIDDEN,
                   404: Responses.RESPONSE_404_NOT_FOUND
               })
def delete_item(user: UserDep, session: SessionDep, item_id: int):
    """
    Soft delete, preventing the item from getting ordered. Its owner can still restore it.
    """
    item_deleted = delete_item_service(user, session, item_id)
    return item_deleted

@router.delete("/", response_model=list[ItemOutputPrivate],
               responses={
                   401: Responses.RESPONSE_401_UNAUTHORIZED,
                   403: Responses.RESPONSE_403_FORBIDDEN,
               })
def delete_items_all(user: UserDep, session: SessionDep):
    """
    Mainly used when users are about to delete their account. So their items do not get ordered anymore.
    """
    items_deleted = delete_items_all_service(user, session)
    return items_deleted
        
@router.post("/{item_id}", response_model=ItemOutputPrivate,
             responses={
                 401: Responses.RESPONSE_401_UNAUTHORIZED,
                 403: Responses.RESPONSE_403_FORBIDDEN,
             })
def restore_item(user: UserDep, session: SessionDep, item_id: int):
    item_restored = restore_item_service(user, session, item_id)
    return item_restored



