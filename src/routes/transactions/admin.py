
from typing import Annotated

from fastapi import APIRouter, Query

from src.core.database import SessionDep
from src.models_schemas.exceptions import Responses
from src.models_schemas.transactions import TransactionInput, TransactionOutput, TransactionSearchSortFilter, TransactionType
from src.services.transactions.core import change_money_admin, read_transactions_admin_service


router = APIRouter()

# ----- Transaction create (ADMIN) ----- #

router.post("/{user_id}/add", response_model=TransactionOutput,
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND,
            })
def add_money(session: SessionDep, user_id: int, inp: TransactionInput):
    return change_money_admin(session, user_id, inp, TransactionType.ADMIN_ADD)

router.post("/{user_id}/subtract", response_model=TransactionOutput,
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND,
                409: Responses.RESPONSE_409_CONFLICT,
            })
def subtract_money(session: SessionDep, user_id: int, inp: TransactionInput):
    return change_money_admin(session, user_id, inp, TransactionType.ADMIN_SUBTRACT)

# ----- Transaction read (ADMIN) ----- #

router.get("/{user_id}", response_model=list[TransactionOutput],
           responses={
               404: Responses.RESPONSE_404_NOT_FOUND
           })
def read_transactions_admin(session: SessionDep, user_id: int, sort_filter: Annotated[TransactionSearchSortFilter, Query()]):
    return read_transactions_admin_service(session, user_id, sort_filter)
    
