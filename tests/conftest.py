from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from src.core.config import settings
from src.core.database import get_async_session
from src.core.security import get_hashed
from src.main import app
from src.models_schemas.items import Item, ItemInput, ItemStatus
from src.models_schemas.users import User, UserStatus
from src.services.items import create_item_service

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

# === Creation utility === #


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


@pytest.fixture(name="create_item")
async def create_item_fixture(session: AsyncSession):
    async def create_item(
        name: str,
        seller: User,
        price: Decimal = Decimal("10"),
        description: str = "description",
        stock_quantity: int = 0,
        status: ItemStatus = ItemStatus.ACTIVE,
    ) -> Item:
        item = Item(
            name=name,
            price=price,
            description=description,
            stock_quantity=stock_quantity,
            status=status,
            seller=seller,
        )

        session.add(item)
        await session.commit()
        await session.refresh(item)

        return item

    return create_item


# === Auto login utility === #


@pytest.fixture(name="quick_login")
async def quick_login_fixture(client: AsyncClient):
    async def quick_login(username: str) -> None:
        token = await client.post(
            "/login",
            data={
                "username": username + "@gmail.com",
                "password": username + "-password",
            },
        )

        token = token.json()["access_token"]

        client.headers.update({"Authorization": "Bearer " + token})

    return quick_login


@pytest.fixture(name="userA")
async def userA(create_user):
    user = await create_user("userA")

    return user


@pytest.fixture(name="authorized_client")
async def authorized_client_fixture(client: AsyncClient, userA: User, quick_login):
    await quick_login("userA")

    return client


@pytest.fixture(name="admin_client")
async def authorized_admin_client_fixture(
    client: AsyncClient, create_user, quick_login
):
    await create_user("admin", is_admin=True)
    await quick_login("admin")

    return client


# === Scenario utility === #


@pytest.fixture(name="users_with_items")
async def users_with_items_fixture(client: AsyncClient, create_user, create_item):
    async def users_with_items(
        n_users: int = 1,
        n_items: int = 1,
    ):
        """
        Creates n_users users for each user status and n_items items for each item status for each user.
        """

        users = []

        for user_status in UserStatus:
            # Creates n_users for each user status
            for i in range(1, n_users + 1):
                user = await create_user(
                    username=f"user{i}-{user_status.value}", status=user_status
                )

                users.append(user)

                # All users
                for item_status in (ItemStatus.BANNED, ItemStatus.DELETED):
                    for j in range(1, n_items + 1):
                        await create_item(
                            name=f"item{j}-{i}-{item_status.value}",
                            seller=user,
                            status=item_status,
                        )

                # BANNED users or ACTIVE users
                if user_status == UserStatus.ACTIVE or user_status == UserStatus.BANNED:
                    for j in range(1, n_items + 1):
                        await create_item(
                            name=f"item{j}-{i}-{ItemStatus.SUSPENDED.value}",
                            seller=user,
                            status=ItemStatus.SUSPENDED,
                        )

                # Only ACTIVE users
                if user_status == UserStatus.ACTIVE:
                    for j in range(1, n_items + 1):
                        await create_item(
                            name=f"item{j}-{i}-{ItemStatus.ACTIVE.value}",
                            seller=user,
                            status=ItemStatus.ACTIVE,
                        )

        return users

    return users_with_items
