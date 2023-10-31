from typing import Callable, Union, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker


class DbSessionMiddleware(BaseMiddleware):

    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        db_connect = get_flag(data, "db_connect")
        if db_connect:
            async with self.session_pool() as session:
                data.update({"session": session})
                result = await handler(event, data)
                try:
                    await session.close()
                    await data["session"].close()
                except:
                    pass
                return result
        else:
            return await handler(event, data)
