from typing import Callable, Union, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message, CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):

    def __init__(self, storage: RedisStorage):
        self.storage = storage

    async def __call__(
            self,
            handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
            event: Union[Message, CallbackQuery],
            data: Dict[str, Any]
    ) -> Any:
        # Defining user's telegram_id
        if type(event) is Message:
            user_id = event.from_user.id
        elif type(event) is CallbackQuery:
            user_id = event.from_user.id
        else:
            return await handler(event, data)
        user = f"user_{user_id}"

        check_user = await self.storage.redis.get(name=user)

        if check_user:
            if int(check_user.decode()) == 1:
                await self.storage.redis.set(name=user, value=1, ex=10)
            else:
                return
        else:
            await self.storage.redis.set(name=user, value=1, ex=10)
