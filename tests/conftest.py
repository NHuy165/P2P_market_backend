import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from src.core.config import settings
from src.core.database import get_async_session
from src.core.security import get_hashed
from src.main import app
from src.models_schemas.users import User, UserStatus

# ----- ESSENTIAL DATABASE SETUP ----- #

engine = create_async_engine(
    str(settings.POSTGRES_URL_TEST), poolclass=NullPool, echo=True
)


async def create_db_and_tables():
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def reset_database():
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(name="session")
async def session_fixture():
    # Setup
    await create_db_and_tables()

    async with AsyncSession(engine) as session:
        yield session

    # Cleanup
    await reset_database()


@pytest.fixture(name="client")
async def client_fixture(session: AsyncSession):
    # Overrides get session function
    def get_async_session_override():
        return session

    app.dependency_overrides[get_async_session] = get_async_session_override

    transport = ASGITransport(app)
    # Returns the async client
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup (clear dependency override)
    app.dependency_overrides.clear()


# ----- UTILITY FIXTURES ----- #


@pytest.fixture(name="create_user")
async def create_fixture(session: AsyncSession):
    async def create_user(
        username: str, status: UserStatus = UserStatus.ACTIVE, is_admin: bool = False
    ) -> User:
        user = User(
            username=username,
            description=username + "-description",
            email=username + "@gmail.com",
            hashed_password=get_hashed(username + "-password"),
            status=status,
            is_admin=is_admin,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    return create_user


@pytest.fixture(name="authorized_client")
async def authorized_client_fixture(client: AsyncClient, create_user):
    await create_user("userA")

    token = await client.post(
        "/login",
        data={"username": "userA@gmail.com", "password": "userA-password"},
    )

    token = token.json()["access_token"]

    client.headers.update({"Authorization": "Bearer " + token})

    return client


@pytest.fixture(name="admin_client")
async def authorized_admin_client_fixture(client: AsyncClient, create_user):
    await create_user("admin", is_admin=True)

    token = await client.post(
        "/login",
        data={"username": "admin@gmail.com", "password": "admin-password"},
    )

    token = token.json()["access_token"]

    client.headers.update({"Authorization": "Bearer " + token})

    return client
