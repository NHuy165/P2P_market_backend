from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from src.repository.users import GetUser

from ..exceptions.core import (
    ExceptionAuthentication_401,
    ExceptionInvalidAccount_403,
    ExceptionNotAdmin_403,
)
from ..models_schemas.auth import TokenInput
from ..models_schemas.users import User, UserStatus
from .config import settings
from .database import SessionDep

# Using auto_error=False so we handle the errors by ourselves
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

# ----- Token verification ----- #


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
) -> User:
    # No token
    if token is None:
        raise ExceptionAuthentication_401()

    # Checks if the token actually works
    try:
        contents = jwt.decode(
            token, key=settings.SECRET_KEY, algorithms=[settings.TOKEN_ENCODE_ALGORITHM]
        )
        contents_model = TokenInput.model_validate(contents)

    # JWT can't decode token
    except jwt.InvalidTokenError:
        raise ExceptionAuthentication_401()

    # Token validation failed
    except ValidationError:
        raise ExceptionAuthentication_401()

    # Checks if the user is legit
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("id", contents_model.sub)

    user = await get_user.get_one(session)

    # User data received is invalid
    if user is None:
        raise ExceptionAuthentication_401()

    # User account is invalid
    if user.status is UserStatus.BANNED or user.status is UserStatus.DELETED:
        raise ExceptionInvalidAccount_403(user.status)

    return user


UserDep = Annotated[User, Depends(get_current_user)]


def verify_admin(user: UserDep) -> None:
    if user.is_admin is False:
        raise ExceptionNotAdmin_403()
