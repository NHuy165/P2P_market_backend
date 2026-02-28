
from typing import Annotated

from fastapi import APIRouter, Query

from ...core.database import SessionDep
from ...exceptions.core import Responses
from ...models_schemas.orders import OrderOutput
from ...repository.core import CriterionInput
from ...services.orders import approve_order_service, complete_order_service, delete_order_admin_service, read_orders_admin_service


router = APIRouter()

# ----- Order read (ADMIN) ----- #

@router.post("/{user_id}", response_model=list[OrderOutput],
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND
            })
def read_orders_admin(session: SessionDep, user_id: int, type: Annotated[bool | None, Query()] = None, criteria: list[CriterionInput] = []):
    return read_orders_admin_service(session, user_id, type, criteria)
    
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
            