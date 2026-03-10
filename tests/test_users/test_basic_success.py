from types import CoroutineType
from typing import Any, Callable

import pytest
from httpx import AsyncClient

from src.models_schemas.auth import TokenOutput
from src.models_schemas.users import (
    PasswordUpdate,
    User,
    UserInput,
    UserOutput,
    UserOutputPrivate,
    UserStatus,
)
from tests.utils import response_validator_single

# ----- User create and login ----- #


async def test_register_user(client: AsyncClient):
    """
    Registers a user successfully.
    """

    user = UserInput(
        username="user1",
        description="user1",
        email="user1@gmail.com",
        password="user1-password",
    )

    response = await client.post("/users/register", json=user.model_dump())

    response_validator_single(
        response,
        200,
        UserOutputPrivate,
        user.model_dump(include={"username", "description", "email"}),
    )


async def test_login(
    client: AsyncClient, create_user: Callable[..., CoroutineType[Any, Any, User]]
):
    """
    Logs in successfully.
    """

    await create_user("user1")

    response = await client.post(
        "/login",
        data={"username": "user1@gmail.com", "password": "user1-password"},
    )

    response_validator_single(response, 200, TokenOutput, {"token_type": "bearer"})


# ----- User read ----- #


async def test_read_user(
    authorized_client: AsyncClient,
    create_user: Callable[..., CoroutineType[Any, Any, User]],
):
    """
    Views own profile using a logged in user.
    Views another profile using a logged in user.
    """

    # === View private profile === #

    response1 = await authorized_client.get(
        "/users/me",
    )

    response_validator_single(response1, 200, UserOutputPrivate, {"username": "userA"})

    # === View others' profiles === #

    user1 = await create_user("user1")
    assert isinstance(user1, User)
    user1_id = user1.id

    response2 = await authorized_client.get(f"/users/{user1_id}")

    response_validator_single(
        response2,
        200,
        UserOutput,
        user1.model_dump(include=set(UserOutput.model_fields.keys())),
    )


async def test_read_user_admin(
    admin_client: AsyncClient, create_user: Callable[..., CoroutineType[Any, Any, User]]
):
    """
    Views a deleted profile as an admin.
    """

    user1 = await create_user("user1", status=UserStatus.DELETED)
    user1_id = user1.id

    response = await admin_client.get(f"/admin/users/{user1_id}")

    response_validator_single(response, 200, UserOutputPrivate, {"username": "user1"})


# ----- User update ----- #


@pytest.mark.parametrize(
    "update",
    [
        {"username": "userB"},
        {"email": "userB@gmail.com"},
        {"username": "userB", "email": "userB@gmail.com"},
    ],
)
async def test_update_user(authorized_client: AsyncClient, update: dict):
    """
    Edits private profile.
    """

    response = await authorized_client.patch("/users/update", json=update)

    response_validator_single(response, 200, UserOutputPrivate, update)


async def test_update_password(authorized_client: AsyncClient):
    """
    Changes account password.
    """

    # === Change password === #

    update = PasswordUpdate(
        old_password="userA-password", new_password="userA-new-password"
    )

    response1 = await authorized_client.patch(
        "/users/change_password", json=update.model_dump()
    )

    response_validator_single(response1, 204)

    # === Log in with new password === #

    response2 = await authorized_client.post(
        "/login",
        data={"username": "userA@gmail.com", "password": "userA-new-password"},
    )

    response_validator_single(response2, 200, TokenOutput, {"token_type": "bearer"})


# ----- User delete ----- #


async def test_delete_user(authorized_client: AsyncClient):
    """
    Deletes account without any items or orders.
    """

    response = await authorized_client.post(
        "/users/delete",
        json="userA-password",
    )

    response_validator_single(
        response, 200, UserOutputPrivate, {"status": UserStatus.DELETED}
    )


async def test_ban_user(
    admin_client: AsyncClient, create_user: Callable[..., CoroutineType[Any, Any, User]]
):
    """
    Bans a user who has no item or order.
    """

    user1 = await create_user("user1")
    user1_id = user1.id

    response1 = await admin_client.post(f"/admin/users/{user1_id}/ban")

    response_validator_single(
        response1,
        200,
        UserOutputPrivate,
        {"status": UserStatus.BANNED.value},
    )


async def test_unban_user(
    admin_client: AsyncClient, create_user: Callable[..., CoroutineType[Any, Any, User]]
):
    """
    Unbans a user who has no item or order.
    """

    user1 = await create_user("user1", status=UserStatus.BANNED)
    user1_id = user1.id

    response1 = await admin_client.post(f"/admin/users/{user1_id}/unban")

    response_validator_single(
        response1,
        200,
        UserOutputPrivate,
        {"status": UserStatus.ACTIVE.value},
    )
