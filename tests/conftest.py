from decimal import Decimal

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from src.core.config import settings
from src.core.database import get_async_session
from src.core.security import get_hashed
from src.main import app
from src.models_schemas.items import Item, ItemInput, ItemStatus
from src.models_schemas.orders import OrderOutputNoType
from src.models_schemas.transactions import Transaction
from src.models_schemas.users import User, UserStatus
from src.services.transactions import read_transactions_service

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


@pytest.fixture(name="app")
async def app_fixture(session: AsyncSession):
    # Overrides get session function
    app.dependency_overrides[get_async_session] = lambda: session

    yield app

    # Cleanup (clear dependency override)
    app.dependency_overrides.clear()


@pytest.fixture(name="client")
async def client_fixture(app: FastAPI):
    transport = ASGITransport(app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ----- UTILITY FIXTURES ----- #

# === Creation utility === #


@pytest.fixture(name="create_user")
async def create_fixture(session: AsyncSession):
    async def create_user(
        username: str,
        status: UserStatus = UserStatus.ACTIVE,
        is_admin: bool = False,
        balance: Decimal = Decimal("0"),
    ) -> User:
        user = User(
            username=username,
            description=username + "-description",
            email=username + "@gmail.com",
            hashed_password=get_hashed(username + "-password"),
            status=status,
            is_admin=is_admin,
            balance=balance,
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
    async def quick_login(username: str) -> dict:
        token = await client.post(
            "/login",
            data={
                "username": username + "@gmail.com",
                "password": username + "-password",
            },
        )

        token = token.json()["access_token"]

        return {"Authorization": "Bearer " + token}

    return quick_login


@pytest.fixture(name="userA")
async def userA(create_user):
    """
    Sometimes we need the user object itself in tests.
    """

    user = await create_user("userA")

    return user


@pytest.fixture(name="authorized_client")
async def authorized_client_fixture(app: FastAPI, userA: User, quick_login):
    token = await quick_login("userA")

    transport = ASGITransport(app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers.update(token)
        yield ac


@pytest.fixture(name="admin_client")
async def authorized_admin_client_fixture(app: FastAPI, create_user, quick_login):
    await create_user("admin", is_admin=True)
    token = await quick_login("admin")

    transport = ASGITransport(app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers.update(token)
        yield ac


# === Miscellaneous utility === #


@pytest.fixture(name="change_money")
async def change_money_fixture(session: AsyncSession):
    """
    This function does not have any auto-validation mechanic.
    """

    async def change_money(user: User, amount: Decimal):
        await session.refresh(user)

        user.balance += amount

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    return change_money


@pytest.fixture(name="fetch_transactions")
async def fetch_transactions_fixture(session: AsyncSession):
    async def fetch_transactions() -> list[Transaction]:
        result = await session.execute(select(Transaction))
        transactions = result.scalars().all()

        return list(transactions)

    return fetch_transactions


@pytest.fixture(name="complete_order")
async def complete_order_fixture(admin_client: AsyncClient):
    async def complete_order(order_id: int):
        await admin_client.patch(f"/admin/orders/{order_id}/approve")
        await admin_client.patch(f"/admin/orders/{order_id}/complete")

    return complete_order


@pytest.fixture(name="quickbuy")
async def quickbuy_fixture():
    async def quickbuy(
        custom_client: AsyncClient, item_id: int, quantity: int
    ) -> OrderOutputNoType:
        order = await custom_client.post(
            "/orders/create", json={"quantity": quantity, "item_id": item_id}
        )

        return OrderOutputNoType.model_validate(order.json())

    return quickbuy
