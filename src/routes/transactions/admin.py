from fastapi import APIRouter

from src.core.database import SessionDep
from src.exceptions.core import Responses
from src.models_schemas.transactions import (
    TransactionInput,
    TransactionOutput,
    TransactionType,
)
from src.repository.core import CriterionInput
from src.services.transactions import (
    change_money_admin_service,
    read_transactions_admin_service,
)

router = APIRouter()

# ----- Transaction create (ADMIN) ----- #


@router.post(
    "/{user_id}/add",
    response_model=TransactionOutput,
    responses={
        404: Responses.RESPONSE_404_NOT_FOUND,
    },
)
async def add_money(session: SessionDep, user_id: int, inp: TransactionInput):
    return await change_money_admin_service(
        session, user_id, inp, TransactionType.ADMIN_ADD
    )


@router.post(
    "/{user_id}/subtract",
    response_model=TransactionOutput,
    responses={
        404: Responses.RESPONSE_404_NOT_FOUND,
        409: Responses.RESPONSE_409_CONFLICT,
    },
)
async def subtract_money(session: SessionDep, user_id: int, inp: TransactionInput):
    return await change_money_admin_service(
        session, user_id, inp, TransactionType.ADMIN_SUBTRACT
    )


# ----- Transaction read (ADMIN) ----- #


@router.post(
    "/{user_id}",
    response_model=list[TransactionOutput],
    responses={404: Responses.RESPONSE_404_NOT_FOUND},
)
async def read_transactions_admin(
    session: SessionDep, user_id: int, criteria: list[CriterionInput] = []
):
    return await read_transactions_admin_service(session, user_id, criteria)
