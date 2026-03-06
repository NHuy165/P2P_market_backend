from typing import Annotated

from fastapi import APIRouter, Body, status

from ...core.database import SessionDep
from ...core.dependencies import UserDep
from ...exceptions.core import Responses
from ...models_schemas.users import (
    PasswordUpdate,
    UserInput,
    UserOutput,
    UserOutputPrivate,
    UserUpdate,
)
from ...services.users import (
    delete_user_service,
    read_user_service,
    register_user_service,
    update_account_service,
    update_password_service,
)

router = APIRouter()

# ----- User create ----- #


@router.post(
    "/register",
    response_model=UserOutputPrivate,
    responses={409: Responses.RESPONSE_409_CONFLICT},
)
async def register_user(user: UserInput, session: SessionDep):
    user_output = await register_user_service(user, session)

    return user_output


# ----- User read ----- #


@router.get(
    "/me",
    response_model=UserOutputPrivate,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
    },
)
def read_my_account(user: UserDep):
    return user


@router.get(
    "/{user_id}",
    response_model=UserOutput,
    responses={404: Responses.RESPONSE_404_NOT_FOUND},
)
async def read_user(session: SessionDep, user_id: int):
    result = await read_user_service(session, user_id)
    return result


# ----- User update ----- #


@router.patch(
    "/update",
    response_model=UserOutputPrivate,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
    },
)
async def update_account(user: UserDep, session: SessionDep, update_info: UserUpdate):
    result = await update_account_service(user, session, update_info)

    return result


@router.patch(
    "/change_password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
    },
)
async def update_password(
    user: UserDep, session: SessionDep, update_info: PasswordUpdate
):
    await update_password_service(user, session, update_info)


# ----- User delete ----- #


@router.post(
    "/delete",
    response_model=UserOutputPrivate,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
        409: Responses.RESPONSE_409_CONFLICT,
    },
)
async def delete_user(
    user: UserDep, session: SessionDep, password: Annotated[str, Body(min_length=1)]
):
    user_deleted = await delete_user_service(user, session, password)
    return user_deleted
