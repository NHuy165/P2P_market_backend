from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from typing import Annotated
from sqlmodel import Session

from ..dependencies import get_current_user
from ..database import get_session
from ..models.users import User
from ..models.items import ItemInput, ItemOutput, ItemUpdate, ItemOutputSpecial, ItemFilterSpecial, ItemFilterPublic
from ..services.items import create_item_service, edit_item_service, get_personal_items_all_service, get_public_items_all_service, get_personal_item_specific_service, get_public_item_specific_service, delete_item_service
from ..exceptions import *

router = APIRouter()

UserDep = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[Session, Depends(get_session)]

# ----- Item listing create ----- #

@router.post("/create", response_model=ItemOutputSpecial)
def create_item(user: UserDep, session: SessionDep, item: ItemInput):
    try:
        item_listing = create_item_service(user, session, item)
        return item_listing
        
    except ExceptionTakenGeneric:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another item listing in your account with this name already exists.",
            headers={"WWW-Authenticate": "Bearer"}
        )
                
# ----- Item listing read ----- #

@router.get("/my-items/", response_model=list[ItemOutputSpecial])
def get_personal_items_all(user: UserDep, session: SessionDep):
    assert user.id is not None
    return get_personal_items_all_service(user.id, session)

@router.get("/my-items", response_model=list[ItemOutputSpecial])
def get_personal_items_all_filtered(user: UserDep, session: SessionDep, filter: Annotated[ItemFilterSpecial, Query()]):
    assert user.id is not None
    return get_personal_items_all_service(user.id, session, filter)

@router.get("/my-items/{item_id}", response_model=ItemOutputSpecial)
def get_personal_item_specific(user: UserDep, session: SessionDep, item_id: Annotated[int, Path(ge=0)]):
    try:
        assert user.id is not None
        return get_personal_item_specific_service(user.id, session, item_id)
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find item with specified id",
        )

# These functions don't require user to be logged in
@router.get("/", response_model=list[ItemOutput])
def get_public_items_all(session: SessionDep):
    return get_public_items_all_service(session)

@router.get("", response_model=list[ItemOutput])
def get_public_items_all_filtered(session: SessionDep, filter: Annotated[ItemFilterPublic, Query()]):
    return get_public_items_all_service(session, filter)

@router.get("/{item_id}", response_model=ItemOutput)
def get_public_item_specific(session: SessionDep, item_id: Annotated[int, Path(ge=0)]):
    try:
        return get_public_item_specific_service(session, item_id)
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find item with specified id",
        )

# ----- Item listing update and delete ----- #

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(user: UserDep, session: SessionDep, item_id: int):
    try:
        assert user.id is not None
        delete_item_service(user.id, session, item_id)
        
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find item with specified id",
        )
        
@router.patch("/{item_id}", response_model=ItemOutputSpecial)
def edit_item(user: UserDep, session: SessionDep, item_id: int, item_update: ItemUpdate):
    # Checks for obvious error in item_update
    
    # Entered both relative and absolute quantity
    if item_update.stock_quantity is not None and item_update.stock_quantity_relative is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enter both absolute and relative item quantity."
        )
        
    # Negative absolute quantity
    if item_update.stock_quantity is not None and item_update.stock_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item edit caused quantity to be negative.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Checks for error from service function
    try:
        assert user.id is not None
        new_item = edit_item_service(user.id, session, item_id, item_update)
        return new_item
        
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find item with specified id",
        )
        
    except ExceptionNegativeValue:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item edit caused quantity to be negative.",
            headers={"WWW-Authenticate": "Bearer"}
        )





