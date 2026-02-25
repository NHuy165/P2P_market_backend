from fastapi import APIRouter, status, HTTPException, Query
from typing import Annotated

from ...core.dependencies import UserDep
from ...models_schemas.exceptions import ExceptionRelativeAbsolute_400, Responses 
from ...core.database import SessionDep
from ...models_schemas.orders import OrderInput, OrderOutputNoType, OrderOutput, OrderSearchSortFilter, OrderUpdate
from ...services.orders.core import create_order_service, delete_order_service, read_orders_services, update_order_service

router = APIRouter()

# ----- Order create ----- #

@router.post("/create", response_model=OrderOutputNoType,
             responses={
                 401: Responses.RESPONSE_401_UNAUTHORIZED,
                 403: Responses.RESPONSE_403_FORBIDDEN,
                 404: Responses.RESPONSE_404_NOT_FOUND,
                 409: Responses.RESPONSE_409_CONFLICT
             })
def create_order(user: UserDep, session: SessionDep, order_inp: OrderInput):
    order_out = create_order_service(user, session, order_inp)
    return order_out
            
# ----- Order read ----- #

@router.get("", response_model=list[OrderOutput])
def read_orders(user: UserDep, session: SessionDep, sort_filter: Annotated[OrderSearchSortFilter, Query()]):
    return read_orders_services(user, session, sort_filter)
    
# ----- Order update ----- #

@router.patch("/{order_id}", response_model=OrderOutput,
              responses={
                  400: Responses.RESPONSE_400_BAD_REQUEST,
                  401: Responses.RESPONSE_401_UNAUTHORIZED,
                  403: Responses.RESPONSE_403_FORBIDDEN,
                  404: Responses.RESPONSE_404_NOT_FOUND,
                  409: Responses.RESPONSE_409_CONFLICT
              })
def update_order(user: UserDep, session: SessionDep, order_id: int, order_upd: OrderUpdate):
    if order_upd.quantity is not None and order_upd.quantity_relative is not None:
        raise ExceptionRelativeAbsolute_400()
    
    new_order = update_order_service(user, session, order_id, order_upd)
    return new_order
        
# ----- Order delete ----- #

@router.delete("/{order_id}", response_model=OrderOutput,
               responses={
                   401: Responses.RESPONSE_401_UNAUTHORIZED,
                   403: Responses.RESPONSE_403_FORBIDDEN,
                   404: Responses.RESPONSE_404_NOT_FOUND,
                   409: Responses.RESPONSE_409_CONFLICT
               })
def delete_order(user: UserDep, session: SessionDep, order_id: int):
    order_deleted = delete_order_service(user, session, order_id)
    return order_deleted
            
            
            
        
        
        