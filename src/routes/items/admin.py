from typing import Annotated
from fastapi import APIRouter, Path

from src.models_schemas.items import ItemOutputPrivate
from src.repository.core import CriterionInput
from ...core.database import SessionDep
from ...services.items import change_item_ban_status_service, read_private_item_one_admin_service, read_private_items_many_admin_service
from ...exceptions.core import Responses  

router = APIRouter()

# ----- Item read (ADMIN) ----- #

@router.post("/{user_id}", response_model=list[ItemOutputPrivate],
            responses={
                401: Responses.RESPONSE_401_UNAUTHORIZED,
                403: Responses.RESPONSE_403_FORBIDDEN,
                404: Responses.RESPONSE_404_NOT_FOUND
            })
def read_private_items_many_admin(session: SessionDep, user_id: int, criteria: list[CriterionInput] = []):
    return read_private_items_many_admin_service(session, user_id, criteria)

@router.get("/{item_id}", response_model=ItemOutputPrivate, 
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND
            })
def read_private_item_one_admin(session: SessionDep, item_id: int):
    return read_private_item_one_admin_service(session, item_id)

# ----- Item update (ADMIN) ----- #

@router.delete("/{item_id}", response_model=ItemOutputPrivate, 
               responses={
                   404: Responses.RESPONSE_404_NOT_FOUND,
                   409: Responses.RESPONSE_409_CONFLICT
               })
def ban_item(session: SessionDep, item_id: Annotated[int, Path()]):
    return change_item_ban_status_service(session, item_id, True)

@router.post("/{item_id}", response_model=ItemOutputPrivate, 
             responses={
                 404: Responses.RESPONSE_404_NOT_FOUND,
                 409: Responses.RESPONSE_409_CONFLICT
             })
def unban_item(session: SessionDep, item_id: Annotated[int, Path()]):
    return change_item_ban_status_service(session, item_id, False)