from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated
from sqlmodel import Session

from ..services.transactions import *
from ..database import get_session
from ..models.transactions import TransactionType, TransactionOutput, TransactionInput
from ..models.users import User
from ..dependencies import get_current_user
from ..exceptions import *

router = APIRouter()

UserDep = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[Session, Depends(get_session)]

# ----- Deposit and withdraw (dummy functions) ----- #

@router.post("/deposit", response_model=TransactionOutput)
def deposit(user: UserDep, session: SessionDep, inp: TransactionInput):
    trans = change_money(inp, user, TransactionType.DEPOSIT, session)
    return trans
        
@router.post("/withdraw", response_model=TransactionOutput)
def withdraw(user: UserDep, session: SessionDep, inp: TransactionInput):
    try:
        trans = change_money(inp, user, TransactionType.WITHDRAWAL, session)
        return trans
    except ExceptionNegativeValue:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Withdrawal amount higher than current balance",
            headers={"WWW-Authenticate": "Bearer"}
        )

# ----- Display transactions history ----- #

@router.get("/history", response_model=list[TransactionOutput])
def display_history(user: UserDep, session: SessionDep):
    assert user.id is not None
    return display_history_service(user.id, session)
        
        
    
        
        