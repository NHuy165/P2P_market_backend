import pytest
from httpx import AsyncClient
from pydantic import EmailStr

from src.exceptions.core import ExceptionResponse, ExceptionType
from src.models_schemas.users import (
    PasswordUpdate,
    User,
    UserInput,
    UserStatus,
)
from tests.utils import validator

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
    create_user,
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

    response = await client.post("/users/register", json=user.model_dump())

    validator(
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
    create_user,
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

    response = await client.post(
        "/login",
        data={"username": username, "password": password},
    )

    validator(
        response,
        status_code,
        ExceptionResponse,
        {"exception_type": exception_type.value},
    )


# ----- User read ----- #


async def test_read_user_admin(authorized_client: AsyncClient):
    """
    Tries to access an admin endpoint as a normal user.
    """

    response = await authorized_client.get("/admin/users/me")

    validator(
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
async def test_update_user(authorized_client: AsyncClient, update: dict):
    """
    Fails to edit profile with erroneous values.
    """

    response = await authorized_client.patch("/users/update", json=update)

    validator(
        response,
        400,
        ExceptionResponse,
        {"exception_type": ExceptionType.REQUEST.value},
    )


async def test_update_password(authorized_client: AsyncClient):
    """
    Tries changing password using wrong credentials.
    """
    update = PasswordUpdate(
        old_password="userA-wrong-password",
        new_password="userA-new-password",
    )

    response = await authorized_client.patch(
        "/users/change_password", json=update.model_dump()
    )

    validator(
        response,
        401,
        ExceptionResponse,
        {"exception_type": ExceptionType.AUTHENTICATION.value},
    )


# ----- User delete ----- #


async def test_delete_user(authorized_client: AsyncClient):
    """
    Tries deleting account using wrong credentials.
    """

    response = await authorized_client.post(
        "/users/delete",
        json="userA-wrong-password",
    )

    validator(
        response,
        401,
        ExceptionResponse,
        {"exception_type": ExceptionType.AUTHENTICATION.value},
    )


@pytest.mark.parametrize(
    "status_code, user_status, is_admin",
    [
        (403, UserStatus.ACTIVE, True),  # ban
        (409, UserStatus.BANNED, False),  # ban
        (409, UserStatus.ACTIVE, False),  # unban
        (409, UserStatus.DELETED, False),  # ban
    ],
)
async def test_delete_user_admin(
    admin_client: AsyncClient,
    create_user,
    status_code: int,
    user_status: UserStatus,
    is_admin: bool,
):
    """
    Fails to ban an admin account.
    Fails to ban an already banned account.
    Fails to unban an active account.
    Fails to ban a deleted account.
    """

    user1 = await create_user("user1", status=user_status, is_admin=is_admin)
    assert isinstance(user1, User)
    user1_id = user1.id

    if user_status == UserStatus.ACTIVE and not is_admin:
        response = await admin_client.post(f"/admin/users/{user1_id}")
    else:
        response = await admin_client.delete(f"/admin/users/{user1_id}")

    # Return model contents
    if status_code == 403:
        validator(
            response,
            403,
            ExceptionResponse,
            {"exception_type": ExceptionType.MODIFIED_ADMIN.value},
        )

    else:
        validator(
            response,
            409,
            ExceptionResponse,
            {"exception_type": ExceptionType.INVALID_STATUS.value},
        )
