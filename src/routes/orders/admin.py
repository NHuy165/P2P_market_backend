
from typing import Annotated

from fastapi import APIRouter, Query

from src.core.database import SessionDep
from src.models_schemas.exceptions import Responses
from src.models_schemas.items import ItemOutputPrivate, ItemSearch, ItemSortFilterPrivate
from src.models_schemas.orders import OrderOutput, OrderSearchSortFilter
from src.services.orders.core import approve_order_service, complete_order_service, delete_order_admin_service, read_orders_admin_service


router = APIRouter()

# ----- Order read (ADMIN) ----- #

@router.get("/{user_id}", response_model=list[OrderOutput],
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND
            })
def read_orders_many_admin(session: SessionDep, user_id: int, sort_filter: Annotated[OrderSearchSortFilter, Query()]):
    return read_orders_admin_service(session, user_id, sort_filter)
    
# ----- Order update (ADMIN) ----- #

@router.patch("/{order_id}/approve", response_model=OrderOutput,
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND
            })
def approve_order(session: SessionDep, order_id: int):
    return approve_order_service(session, order_id)

@router.patch("/{order_id}/complete", response_model=OrderOutput,
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND,
            })
def complete_order(session: SessionDep, order_id: int):
    return complete_order_service(session, order_id)

# ----- Order delete (ADMIN) ----- #

@router.delete("/{order_id}", response_model=OrderOutput,
               responses={
                   404: Responses.RESPONSE_404_NOT_FOUND,
                   409: Responses.RESPONSE_409_CONFLICT
               })
def delete_order_admin(session: SessionDep, order_id: int):
    order_deleted = delete_order_admin_service(session, order_id)
    return order_deleted
            