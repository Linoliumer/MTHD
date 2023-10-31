from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: Union[str, list]):
        self.chat_type = chat_type

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:

        # Defining user's telegram_id
        if type(event) is Message:
            obj = event
        elif type(event) is CallbackQuery:
            obj = event.message
        else:
            return False
        if isinstance(self.chat_type, str):
            return obj.chat.type == self.chat_type
        else:
            return obj.chat.type in self.chat_type
