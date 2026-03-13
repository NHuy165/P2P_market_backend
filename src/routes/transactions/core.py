from fastapi import APIRouter

from ...core.database import SessionDep
from ...core.dependencies import UserDep
from ...exceptions.core import Responses
from ...models_schemas.transactions import (
    TransactionInput,
    TransactionOutput,
    TransactionType,
)
from ...repository.core import CriterionInput
from ...services.transactions import change_money_service, read_transactions_service

router = APIRouter()

# ----- Transaction create (dummy functions) ----- #


@router.post(
    "/deposit",
    response_model=TransactionOutput,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
        404: Responses.RESPONSE_404_NOT_FOUND,
    },
)
async def deposit(user: UserDep, session: SessionDep, inp: TransactionInput):
    trans = await change_money_service(user, session, inp, TransactionType.DEPOSIT)
    return trans


@router.post(
    "/withdraw",
    response_model=TransactionOutput,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
        404: Responses.RESPONSE_404_NOT_FOUND,
        409: Responses.RESPONSE_409_CONFLICT,
    },
)
async def withdraw(user: UserDep, session: SessionDep, inp: TransactionInput):
    trans = await change_money_service(user, session, inp, TransactionType.WITHDRAWAL)
    return trans


# Transactions related to orders are created on orders' side.

# ----- Transaction read ----- #


@router.post(
    "",
    response_model=list[TransactionOutput],
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
    },
)
async def read_transactions(
    user: UserDep, session: SessionDep, criteria: list[CriterionInput] = []
):
    return await read_transactions_service(user, session, criteria)
