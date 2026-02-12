from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated
from sqlmodel import Session

from ..dependencies import get_current_user
from ..database import get_session
from ..models.users import User
from ..models.schemas import ItemInput, ItemOutput, ItemUpdate, ItemOutputSpecial
from ..services.items import create_item_service, edit_item_service, get_personal_items_service, get_public_items_service, delete_item_service
from ..exceptions import *

router = APIRouter()

UserDep = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[Session, Depends(get_session)]

# ----- Item listing creation ----- #

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
        
# ----- Item listing edit ----- #

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(user: UserDep, session: SessionDep, item_id: int):
    try:
        delete_item_service(user, session, item_id)
        
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
        new_item = edit_item_service(user, session, item_id, item_update)
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
        
        
# ----- Item listing display ----- #

@router.get("/my-items", response_model=list[ItemOutputSpecial])
def get_personal_items(user: UserDep, session: SessionDep):
    return get_personal_items_service(user, session)

# This function doesn't require user to be logged in
@router.get("/all", response_model=list[ItemOutput])
def get_public_items(session: SessionDep):
    return get_public_items_service(session)





