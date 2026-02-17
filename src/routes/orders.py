from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from typing import Annotated
from sqlmodel import Session

from ..exceptions import ExceptionConflict, ExceptionNegativeValue, ExceptionNotFound, ExceptionTimeOut
from ..database import get_session
from ..dependencies import get_current_user
from ..models.orders import OrderInput, OrderOutput, OrderOutputWithType, OrderSortFilter, OrderUpdate
from ..models.users import User
from ..services.orders.core import create_order_service, delete_order_service, read_orders_services, update_order_service

router = APIRouter()

UserDep = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[Session, Depends(get_session)]

# ----- Order create ----- #

router.post("/create", response_model=OrderOutput)
def create_order(user: User, session: SessionDep, order_inp: OrderInput):
    try:
        assert user.id is not None
        order_out = create_order_service(user, session, order_inp)
        return order_out
        
    except ExceptionNotFound as e1:
        if str(e1) == "Item":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couldn't find item."
            )
        elif str(e1) == "User":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couldn't find user."
            )
        
    except ExceptionConflict:
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot buy your own items."
        )
        
    except ExceptionNegativeValue as e2:
        if str(e2) == "Negative stock":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot order more items than there are in stock."
            )
        elif str(e2) == "Negative balance":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Insufficient funds."
            )
            
# ----- Order read ----- #

@router.get("/", response_model=list[OrderOutputWithType])
def read_orders_all(user: UserDep, session: SessionDep):
    return read_orders_services(user, session)

@router.get("", response_model=list[OrderOutputWithType])
def read_orders_sort_filter(user: UserDep, session: SessionDep, sort_filter: Annotated[OrderSortFilter, Query()]):
    return read_orders_services(user, session, sort_filter)
    
# ----- Order update ----- #

@router.patch("/{order_id}", response_model=OrderOutput)
def update_order(user: UserDep, session: SessionDep, order_id: int, order_upd: OrderUpdate):
    if order_upd.quantity is not None and order_upd.quantity_relative is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enter both absolute and relative quantity."
        )
    
    try:
        new_order = update_order_service(user, session, order_id, order_upd)
        return new_order
    
    except ExceptionNotFound as e1:
        if str(e1) == "User":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couldn't find user."
            )
        elif str(e1) == "Order":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couldn't find item."
            )
        elif str(e1) == "Item":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couldn't find item."
            )
            
    except ExceptionNegativeValue as e2:
        if str(e2) == "Item":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid item quantity."
            )
        elif str(e2) == "User":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Insufficient funds."
            )
            
    except ExceptionTimeOut:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot edit order outside 10 minutes of creation."
        )
        
    except ExceptionConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot edit non-pending items."
        )
        
# ----- Order delete ----- #

@router.delete("/{order_id}", response_model=OrderOutput)
def delete_order(user: UserDep, session: SessionDep, order_id: int):
    try:
        order_deleted = delete_order_service(user, session, order_id)
        return order_deleted
        
    except ExceptionNotFound as e:
        if str(e) == "User":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couldn't find user."
            )
        elif str(e) == "Order":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couldn't find any pending order with the provided information."
            )
            
            
            
        
        
        