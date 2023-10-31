from aiogram import Router, F
from aiogram.filters import or_f
from aiogram.types import CallbackQuery

from settings import client_text, keyboard
from bot.states import UserState
from bot.filters.chat_type import ChatTypeFilter

router = Router()


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("statistic:"),
    or_f(
        or_f(UserState.SubscriberInactive, UserState.TrialPeriodInactive),
        UserState.TrialPeriodActive
    )
)
@router.callback_query(
    ChatTypeFilter("private"),
    F.data == "buy_subscribe",
    or_f(
        or_f(UserState.SubscriberInactive, UserState.TrialPeriodInactive),
        UserState.TrialPeriodActive
    )
)
@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("profile:"),
    or_f(UserState.SubscriberInactive, UserState.TrialPeriodInactive)
)
@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("session:"),
    or_f(UserState.SubscriberInactive, UserState.TrialPeriodInactive)
)
async def inactive(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.answer(
        text=client_text.menus["SUBSCRIBE_INACTIVE"],
        reply_markup=keyboard.keyboards["SUBSCRIBE_INACTIVE"]
    )
