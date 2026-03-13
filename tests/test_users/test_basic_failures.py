from types import CoroutineType
from typing import Any, Callable

import pytest
from httpx import AsyncClient
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.core import ExceptionResponse, ExceptionType
from src.models_schemas.users import (
    PasswordUpdate,
    User,
    UserInput,
    UserStatus,
)
from tests.utils import response_validator_single

# ----- User create and login ----- #


@pytest.mark.parametrize(
    "username, email, exception_type",
    [
        ("user1", "user1@gmail.com", ExceptionType.TAKEN_USER_NAME),
        ("user2", "user1@gmail.com", ExceptionType.TAKEN_USER_EMAIL),
    ],
)
async def test_register_user(
    client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    username: str,
    email: EmailStr,
    exception_type: ExceptionType,
):
    """
    Fails to register a user using a taken name
    Fails to register a user using a taken email.
    """

    await create_user("user1")

    user = UserInput(
        username=username,
        description="user1",
        email=email,
        password="user1-password",
    )

    session.expire_all()

    response = await client.post("/users/register", json=user.model_dump())

    response_validator_single(
        response, 409, ExceptionResponse, {"exception_type": exception_type.value}
    )


@pytest.mark.parametrize(
    "username, password, status_code, exception_type, user_status",
    [
        (
            "user2@gmail.com",
            "user1-password",
            401,
            ExceptionType.AUTHENTICATION,
            UserStatus.ACTIVE,
        ),
        (
            "user1@gmail.com",
            "user2-password",
            401,
            ExceptionType.AUTHENTICATION,
            UserStatus.ACTIVE,
        ),
        (
            "userB@gmail.com",
            "userB-password",
            403,
            ExceptionType.INVALID_ACCOUNT,
            UserStatus.BANNED,
        ),
    ],
)
async def test_login(
    client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    username: str,
    password: str,
    status_code: int,
    exception_type: ExceptionType,
    user_status: UserStatus,
):
    """
    Fails to log in using an incorrect email.
    Fails to log in using an incorrect password.
    Fails to log into a banned account.
    """

    await create_user("user1")
    await create_user("userB", status=user_status)

    session.expire_all()

    response = await client.post(
        "/login",
        data={"username": username, "password": password},
    )

    response_validator_single(
        response,
        status_code,
        ExceptionResponse,
        {"exception_type": exception_type.value},
    )


# ----- User read ----- #


async def test_read_user_admin(authorized_client: AsyncClient, session: AsyncSession):
    """
    Tries to access an admin endpoint as a normal user.
    """

    session.expire_all()

    response = await authorized_client.get("/admin/users/me")

    response_validator_single(
        response,
        403,
        ExceptionResponse,
        {"exception_type": ExceptionType.NOT_ADMIN.value},
    )


# ----- User update ----- #


@pytest.mark.parametrize(
    "update",
    [
        {"username": None, "email": None},
        {"username": None},
        {"email": None},
        {"username": ""},
        {"email": ""},
        {"email": "gibberish"},
    ],
)
async def test_update_user(
    authorized_client: AsyncClient, session: AsyncSession, update: dict
):
    """
    Fails to edit profile with erroneous values.
    """

    session.expire_all()

    response = await authorized_client.patch("/users/update", json=update)

    response_validator_single(
        response,
        400,
        ExceptionResponse,
        {"exception_type": ExceptionType.REQUEST.value},
    )


async def test_update_password(authorized_client: AsyncClient, session: AsyncSession):
    """
    Tries changing password using wrong credentials.
    """
    update = PasswordUpdate(
        old_password="userA-wrong-password",
        new_password="userA-new-password",
    )

    session.expire_all()

    response = await authorized_client.patch(
        "/users/change_password", json=update.model_dump()
    )

    response_validator_single(
        response,
        401,
        ExceptionResponse,
        {"exception_type": ExceptionType.AUTHENTICATION.value},
    )


# ----- User delete ----- #


async def test_delete_user(authorized_client: AsyncClient, session: AsyncSession):
    """
    Tries deleting account using wrong credentials.
    """

    session.expire_all()

    response = await authorized_client.post(
        "/users/delete",
        json="userA-wrong-password",
    )

    response_validator_single(
        response,
        401,
        ExceptionResponse,
        {"exception_type": ExceptionType.AUTHENTICATION.value},
    )


@pytest.mark.parametrize(
    "user_status, is_admin, status_code, exception_type",
    [
        (UserStatus.ACTIVE, True, 403, ExceptionType.MODIFIED_ADMIN),
        (UserStatus.BANNED, False, 409, ExceptionType.INVALID_STATUS),
        (UserStatus.DELETED, False, 409, ExceptionType.INVALID_STATUS),
    ],
)
async def test_ban_user(
    admin_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
    user_status: UserStatus,
    is_admin: bool,
    status_code: int,
    exception_type: ExceptionType,
):
    """
    Fails to ban an admin account.
    Fails to ban an already banned account.
    Fails to ban a deleted account.
    """

    user1 = await create_user("user1", status=user_status, is_admin=is_admin)
    user1_id = user1.id

    session.expire_all()

    response = await admin_client.post(f"/admin/users/{user1_id}/ban")

    response_validator_single(
        response,
        status_code,
        ExceptionResponse,
        {"exception_type": exception_type.value},
    )


async def test_unban_user(
    admin_client: AsyncClient,
    session: AsyncSession,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
):
    """
    Fails to unban an active account.
    """

    user1 = await create_user("user1")
    user1_id = user1.id

    session.expire_all()

    response = await admin_client.post(f"/admin/users/{user1_id}/unban")

    response_validator_single(
        response,
        409,
        ExceptionResponse,
        {"exception_type": ExceptionType.INVALID_STATUS.value},
    )
