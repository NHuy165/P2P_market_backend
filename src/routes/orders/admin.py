from typing import Annotated

from fastapi import APIRouter, Query

from ...core.database import SessionDep
from ...exceptions.core import Responses
from ...models_schemas.orders import OrderOutput, OrderOutputNoType
from ...repository.core import CriterionInput
from ...services.orders import (
    approve_order_service,
    complete_order_service,
    delete_order_admin_service,
    read_orders_admin_service,
)

router = APIRouter()

# ----- Order read (ADMIN) ----- #


@router.post(
    "/{user_id}",
    response_model=list[OrderOutput],
    responses={404: Responses.RESPONSE_404_NOT_FOUND},
)
async def read_orders_admin(
    session: SessionDep,
    user_id: int,
    type: Annotated[bool | None, Query()] = None,
    criteria: list[CriterionInput] = [],
):
    return await read_orders_admin_service(session, user_id, type, criteria)


# ----- Order update (ADMIN) ----- #


@router.patch(
    "/{order_id}/approve",
    response_model=OrderOutputNoType,
    responses={404: Responses.RESPONSE_404_NOT_FOUND},
)
async def approve_order(session: SessionDep, order_id: int):
    return await approve_order_service(session, order_id)


@router.patch(
    "/{order_id}/complete",
    response_model=OrderOutputNoType,
    responses={
        404: Responses.RESPONSE_404_NOT_FOUND,
    },
)
async def complete_order(session: SessionDep, order_id: int):
    return await complete_order_service(session, order_id)


# ----- Order delete (ADMIN) ----- #


@router.delete(
    "/{order_id}",
    response_model=OrderOutputNoType,
    responses={
        404: Responses.RESPONSE_404_NOT_FOUND,
        409: Responses.RESPONSE_409_CONFLICT,
    },
)
async def delete_order_admin(session: SessionDep, order_id: int):
    order_deleted = await delete_order_admin_service(session, order_id)
    return order_deleted
