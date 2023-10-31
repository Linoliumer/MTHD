from aiogram import F, Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.filters.chat_type import ChatTypeFilter
from bot.states import UserState
from bot.utils.menus import main_menu, profile_menu, info_menu, profile_statistic, report_menu, session_menu

router = Router()


@router.callback_query(
    ChatTypeFilter("private"),
    F.data == "menu",
    or_f(
        or_f(UserState.SubscriberInactive, UserState.TrialPeriodInactive),
        or_f(UserState.SubscriberActive, UserState.TrialPeriodActive)
    )
)
async def menu_callback_handler(call: CallbackQuery) -> None:
    """
    Main Menu Callback Handler
    """
    # Response to the Telegram server
    await call.answer()
    # Calling the main menu
    await main_menu(call=call)


@router.message(
    ChatTypeFilter("private"),
    or_f(Command("menu"), Command("start")),
    or_f(
        or_f(UserState.SubscriberInactive, UserState.TrialPeriodInactive),
        or_f(UserState.SubscriberActive, UserState.TrialPeriodActive)
    )
)
async def menu_message_handler(message: Message) -> None:
    """
    Call the main menu with the command
    """
    await main_menu(message=message)


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("menu:"),
    or_f(
        or_f(UserState.SubscriberInactive, UserState.TrialPeriodInactive),
        or_f(UserState.SubscriberActive, UserState.TrialPeriodActive)
    )
)
async def main_menus_callback_handler(call: CallbackQuery, state: FSMContext) -> None:
    """
    Main Callback Handler
    """
    # Response to the Telegram server
    await call.answer()
    # Retrieving a command from a callback
    command = str(call.data).split(':')[1]
    if command == "profile":
        # Calling the profile menu
        await profile_menu(call=call, state=state)
    elif command == "info":
        # Calling the info menu
        await info_menu(call=call)
    elif command == "statistic":
        await profile_statistic(call=call, state=state)
    elif command == "report":
        # Calling the report menu
        await report_menu(call=call)
    elif command == "session":
        # Calling the session menu
        await session_menu(call=call)
