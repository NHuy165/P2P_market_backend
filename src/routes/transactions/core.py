from fastapi import APIRouter, status, HTTPException

from ...models_schemas.exceptions import Responses
from ...core.dependencies import UserDep
from ...core.database import SessionDep
from ...services.transactions.core import change_money, read_transactions_service  
from ...models_schemas.transactions import TransactionSearchSortFilter, TransactionType, TransactionOutput, TransactionInput

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

@router.get("/", response_model=list[TransactionOutput])
def read_transactions_all(user: UserDep, session: SessionDep):
    return read_transactions_service(user, session)

@router.get("", response_model=list[TransactionOutput])
def read_transactions_sort_filter(user: UserDep, session: SessionDep, sort_filter: TransactionSearchSortFilter):
    return read_transactions_service(user, session, sort_filter)
        
        
    
        
        