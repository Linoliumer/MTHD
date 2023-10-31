import logging

from aiogram import Router, F, Bot
from aiogram.enums import ContentType
from aiogram.filters import or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery, Message
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.chat_type import ChatTypeFilter
from bot.states import UserState
from bot.utils.menus import error_menu
from models import User, Order, License
from settings import f_config, client_text, keyboard

router = Router()


@router.callback_query(
    ChatTypeFilter("private"),
    F.data == "payment_start",
    or_f(
        or_f(UserState.SubscriberInactive, UserState.TrialPeriodInactive),
        UserState.TrialPeriodActive
    )
)
async def start_payment(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await call.answer()
    await state.clear()
    await bot.send_invoice(
        call.from_user.id,
        title=f_config.text["PAYMENTS"]["SUBSCRIBE"]["TITLE"],
        description=f_config.text["PAYMENTS"]["SUBSCRIBE"]["DESCRIPTION"],
        provider_token=f_config.text["PAYMENTS"]["TOKEN"],
        currency=f_config.text["PAYMENTS"]["SUBSCRIBE"]["CURRENCY"],
        photo_url=f_config.text["PAYMENTS"]["SUBSCRIBE"]["PHOTO"],
        photo_height=f_config.text["PAYMENTS"]["SUBSCRIBE"]["PHOTO_HEIGHT"],  # !=0/None or picture won't be shown
        photo_width=f_config.text["PAYMENTS"]["SUBSCRIBE"]["PHOTO_WIDTH"],
        is_flexible=False,  # True If you need to set up Shipping Fee
        prices=[
            LabeledPrice(
                label=f_config.text["PAYMENTS"]["SUBSCRIBE"]["LABEL"],
                amount=f_config.text["PAYMENTS"]["SUBSCRIBE"]["PRICE"]*100
            )
        ],
        protect_content=True,
        payload="test-invoice-payload"
    )


@router.pre_checkout_query(
    StateFilter(None),
    flags={"db_connect": True}
)
async def checkout(pre_checkout_query: PreCheckoutQuery, session: AsyncSession, bot: Bot):
    ok = True
    try:
        query = select(User).where(User.user_id == pre_checkout_query.from_user.id)
        user = (await session.execute(query)).scalars().first()
        if user is None:
            ok = False
        else:
            order = Order(
                user_id=user.user_id,
                result=False
            )
            session.add(order)
            await session.commit()
    except Exception as error:
        logging.error(f"Working with database | {str(error)}")
        ok = False
    try:
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=ok
        )
    except Exception as er:
        logging.error(f"{str(er)}")


@router.message(
    F.content_type == ContentType.SUCCESSFUL_PAYMENT,
    or_f(
        or_f(UserState.SubscriberInactive, UserState.TrialPeriodInactive),
        UserState.TrialPeriodActive
    ),
    flags={"db_connect": True}
)
async def got_payment(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    try:
        query = update(License). \
            where(License.telegram_id == int(message.from_user.id)). \
            values(
                type=2,
                duration=30,
                name="Subscribe"
            )
        await session.execute(query)
        query = update(Order). \
            where(
                Order.user_id == int(message.from_user.id),
                Order.result == bool(False)
            ). \
            values(
                result=True
            )
        await session.execute(query)
        await session.commit()
    except Exception:
        await error_menu(message=message)
        return
    await state.clear()
    await bot.send_message(
        message.chat.id,
        text=client_text.menus["SUCCESSFUL_PAYMENT"],
        reply_markup=keyboard.keyboards["SUCCESSFUL_PAYMENT"]
    )
