from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from ...core.database import SessionDep
from ...exceptions.core import Responses
from ...models_schemas.auth import TokenOutput
from ...services.auth import login_service

router = APIRouter()

# ----- Login for token ----- #


@router.post(
    "/login",
    response_model=TokenOutput,
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
    },
)
async def login(
    user: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
):
    access_token = await login_service(user.username, user.password, session)
    return TokenOutput(access_token=access_token, token_type="bearer")
