from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
from sqlmodel import Session
from enum import Enum

from ..services.transactions import *
from ..database import get_session
from ..models.schemas import TransactionType, UserOutput, TranstionOutput
from ..models.users import User
from ..dependencies import get_current_user

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

@router.post("/deposit", response_model=UserOutput)
def deposit(amount: float, session: SessionDep, user: Annotated[User, Depends(get_current_user)]):
    user = change_money(amount, user, TransactionType.DEPOSIT, session)
    return user
        
@router.post("/withdraw", response_model=UserOutput)
def withdraw(amount: float, session: SessionDep, user: Annotated[User, Depends(get_current_user)]):
    try:
        user = change_money(amount, user, TransactionType.WITHDRAWAL, session)
        return user
    except ExceptionNegativeBalance:
        raise HTTPException(
            status_code=status.HTTP_409_BAD_REQUEST,
            detail="Withdrawal amount higher than current balance",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
@router.get("/history", response_model=list[TranstionOutput])
def display_history(session: SessionDep, user: Annotated[User, Depends(get_current_user)]):
    assert user.id is not None
    return display_history_service(user.id, session)
        
        
    
        
        