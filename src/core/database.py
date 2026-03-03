from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from .security import settings

engine = create_async_engine(str(settings.POSTGRES_URL), echo=True)


async def create_db_and_tables():
    # Initiates connection to database.
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
        # Runs the table creation function (sync) with run_sync.


async def dispose():
    await engine.dispose()


async def get_async_session():
    async with AsyncSession(engine) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
