from httpx import AsyncClient

from src.exceptions.core import ExceptionResponse, ExceptionType
from src.models_schemas.users import UserInput, UserOutputPrivate


async def test_register_user(client: AsyncClient):
    request_body = UserInput(
        username="user1",
        description="user1",
        email="user1@gmail.com",
        password="user1-password",
    )

    response = await client.post("/users/register", json=request_body.model_dump())

    assert response.status_code == 200
    validated_response_body = UserOutputPrivate.model_validate(response.json())

    assert request_body.model_dump(
        include={"username", "description", "email"}
    ) == validated_response_body.model_dump(
        include={"username", "description", "email"}
    )


async def test_register_duplicate_name(client: AsyncClient, create_user):
    await create_user("user1")

    request_body = UserInput(
        username="user1",
        description="user1",
        email="user1@gmail.com",
        password="user1-password",
    )

    response = await client.post("/users/register", json=request_body.model_dump())

    assert response.status_code == 409

    response_body = response.json()
    validated_response_body = ExceptionResponse.model_validate(response_body)

    assert validated_response_body.exception_type == ExceptionType.TAKEN_USER_NAME.value


async def test_register_duplicate_email(client: AsyncClient, create_user):
    await create_user("user1")

    request_body = UserInput(
        username="user2",
        description="user2",
        email="user1@gmail.com",
        password="user1-password",
    )

    response = await client.post("/users/register", json=request_body.model_dump())

    assert response.status_code == 409

    response_body = response.json()
    validated_response_body = ExceptionResponse.model_validate(response_body)

    assert (
        validated_response_body.exception_type == ExceptionType.TAKEN_USER_EMAIL.value
    )
