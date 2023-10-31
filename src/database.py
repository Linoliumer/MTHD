from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from typing import AsyncGenerator

from settings import DATABASE_URL


Base = declarative_base()


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


class DoesNotExist(Exception):
    def __init__(self, message="Value not found in the table"):
        self.message = message
        super().__init__(self.message)