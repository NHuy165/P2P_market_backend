from fastapi import APIRouter, status, HTTPException

from src.repository.core import CriterionInput

from ...exceptions.core import Responses
from ...core.dependencies import UserDep
from ...core.database import SessionDep
from ...services.transactions import change_money, read_transactions_service  
from ...models_schemas.transactions import TransactionType, TransactionOutput, TransactionInput

router = APIRouter()

# ----- Transaction create (dummy functions) ----- #

@router.post("/deposit", response_model=TransactionOutput,
             responses={
                 401: Responses.RESPONSE_401_UNAUTHORIZED,
                 403: Responses.RESPONSE_403_FORBIDDEN,
                 404: Responses.RESPONSE_404_NOT_FOUND
             })
def deposit(user: UserDep, session: SessionDep, inp: TransactionInput):
    trans = change_money(user, session, inp, TransactionType.DEPOSIT)
    return trans

        
@router.post("/withdraw", response_model=TransactionOutput,
             responses={
                 401: Responses.RESPONSE_401_UNAUTHORIZED,
                 403: Responses.RESPONSE_403_FORBIDDEN,
                 404: Responses.RESPONSE_404_NOT_FOUND,
                 409: Responses.RESPONSE_409_CONFLICT
             })
def withdraw(user: UserDep, session: SessionDep, inp: TransactionInput):
    trans = change_money(user, session, inp, TransactionType.WITHDRAWAL)
    return trans
        
# Transactions related to orders are created on orders' side.

# ----- Transaction read ----- #

@router.post("", response_model=list[TransactionOutput],
             responses={
                 401: Responses.RESPONSE_401_UNAUTHORIZED,
                 403: Responses.RESPONSE_403_FORBIDDEN,
             })
def read_transactions(user: UserDep, session: SessionDep, criteria: list[CriterionInput] = []):
    return read_transactions_service(user, session, criteria)
        
        
    
        
        