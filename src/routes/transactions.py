from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated
from sqlmodel import Session

from ..services.transactions.core import *
from ..database import get_session
from ..models.transactions import TransactionType, TransactionOutput, TransactionInput
from ..models.users import User
from ..dependencies import get_current_user
from ..exceptions import *

router = APIRouter()

UserDep = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[Session, Depends(get_session)]

# ----- Transaction create (dummy functions) ----- #

@router.post("/deposit", response_model=TransactionOutput)
def deposit(user: UserDep, session: SessionDep, inp: TransactionInput):
    try:
        trans = change_money(user, session, inp, TransactionType.DEPOSIT)
        return trans
    except ExceptionNotFound:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couldn't find user."
            )
        
@router.post("/withdraw", response_model=TransactionOutput)
def withdraw(user: UserDep, session: SessionDep, inp: TransactionInput):
    try:
        trans = change_money(user, session, inp, TransactionType.WITHDRAWAL)
        return trans
    except ExceptionNegativeValue:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Withdrawal amount higher than current balance"
        )
    except ExceptionNotFound:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Couldn't find user."
            )
        
# Transactions related to orders are created on orders' side.

# ----- Transaction read ----- #

@router.get("/", response_model=list[TransactionOutput])
def read_transactions_all(user: UserDep, session: SessionDep):
    return read_transactions_service(user, session)

@router.get("", response_model=list[TransactionOutput])
def read_transactions_sort_filter(user: UserDep, session: SessionDep, sort_filter: TransactionSortFilter):
    return read_transactions_service(user, session, sort_filter)
        
        
    
        
        