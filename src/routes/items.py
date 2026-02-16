from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from typing import Annotated
from sqlmodel import Session

from ..dependencies import get_current_user
from ..database import get_session
from ..models.users import User
from ..models.items import ItemInput, ItemOutput, ItemUpdate, ItemOutputPrivate, ItemSortFilterPrivate, ItemSortFilterPublic
from ..services.items.core import create_item_service, edit_item_service, get_personal_item_many_service, get_public_item_many_service, get_personal_item_one_service, get_public_item_one_service, delete_item_service
from ..exceptions import *

router = APIRouter()

UserDep = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[Session, Depends(get_session)]

# ----- Item create ----- #

@router.post("/create", response_model=ItemOutputPrivate)
def create_item(user: UserDep, session: SessionDep, item: ItemInput):
    try:
        item_listing = create_item_service(user, session, item)
        return item_listing
        
    except ExceptionTakenGeneric:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another item listing in your account with this name already exists."
        )
                
# ----- Item read ----- #

@router.get("/my-items/", response_model=list[ItemOutputPrivate])
def get_personal_item_all(user: UserDep, session: SessionDep):
    assert user.id is not None
    return get_personal_item_many_service(user, session)

@router.get("/my-items", response_model=list[ItemOutputPrivate])
def get_personal_item_with_constraint(user: UserDep, session: SessionDep, filter: Annotated[ItemSortFilterPrivate, Query()]):
    assert user.id is not None
    return get_personal_item_many_service(user, session, filter)

@router.get("/my-items/{item_id}", response_model=ItemOutputPrivate)
def get_personal_item_one(user: UserDep, session: SessionDep, item_id: Annotated[int, Path(ge=0)]):
    try:
        assert user.id is not None
        return get_personal_item_one_service(user, session, item_id)
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find item",
        )

# These functions below don't require user to be logged in

@router.get("/", response_model=list[ItemOutput])
def get_public_items_all(session: SessionDep):
    return get_public_item_many_service(session)

@router.get("", response_model=list[ItemOutput])
def get_public_items_with_constraint(session: SessionDep, filter: Annotated[ItemSortFilterPublic, Query()]):
    return get_public_item_many_service(session, filter)

@router.get("/{item_id}", response_model=ItemOutput)
def get_public_item_one(session: SessionDep, item_id: Annotated[int, Path(ge=0)]):
    try:
        return get_public_item_one_service(session, item_id)
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find item",
        )

# ----- Item update ----- #
        
@router.patch("/{item_id}", response_model=ItemOutputPrivate)
def edit_item(user: UserDep, session: SessionDep, item_id: int, item_update: ItemUpdate):
    # Checks for obvious error in item_update
    
    # Entered both relative and absolute quantity
    if item_update.stock_quantity is not None and item_update.stock_quantity_relative is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enter both absolute and relative quantity."
        )
        
    # Negative absolute quantity
    if item_update.stock_quantity is not None and item_update.stock_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item edit caused quantity to be negative."
        )
    
    # Checks for error from service function
    try:
        assert user.id is not None
        new_item = edit_item_service(user, session, item_id, item_update)
        return new_item
        
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find item",
        )
        
    except ExceptionNegativeValue:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item edit caused quantity to be negative."
        )
        
# ----- Item delete ----- #

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(user: UserDep, session: SessionDep, item_id: int):
    try:
        assert user.id is not None
        delete_item_service(user, session, item_id)
        
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find item",
        )



