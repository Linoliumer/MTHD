from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.filters.chat_type import ChatTypeFilter
from bot.utils.menus import register_menu
from settings import client_text

router = Router()


@router.callback_query(ChatTypeFilter("private"))
async def unknown_callback(call: CallbackQuery, state: FSMContext) -> None:
    """
    Processing an unknown or invalid action for a user
    """
    # Response to the Telegram server
    await call.answer()
    # Getting user state
    state_now = await state.get_state()
    if state_now == "UserState:Unregister":
        # Registration redirects
        await register_menu(state=state, call=call)
    else:
        # Notification of an unknown command
        await call.message.answer(
            text=client_text.messages["UNKNOWN_COMMAND"]
        )


@router.message(ChatTypeFilter("private"))
async def unknown_message(message: Message, state: FSMContext) -> None:
    """
    Processing an unknown or invalid action for a user
    """
    # Getting user state
    state_now = await state.get_state()
    print(state_now)
    if state_now == "UserState:Unregister":
        # Registration redirects
        await register_menu(state=state, message=message)
    else:
        # Notification of an unknown command
        await message.answer(
            text=client_text.messages["UNKNOWN_COMMAND"]
        )
