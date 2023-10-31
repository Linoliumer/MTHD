from aiogram import Router, F
from aiogram.filters import Command, or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.chat_type import ChatTypeFilter
from bot.states import FormingReport, UserState
from bot.utils.menus import report_menu
from models import Question, Report
from settings import MAX_LEN_INPUT, client_text, MAX_LEN_TEXT, keyboard

router = Router()


@router.message(
    ChatTypeFilter("private"),
    Command("cancel"),
    StateFilter(FormingReport)
)
async def cancel_report(message: Message, state: FSMContext) -> None:
    """
    Canceling report status
    """
    # Deleting temporary data | Disabling state
    await state.clear()
    # Calling the report menu
    await report_menu(message=message)


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("report:"),
    or_f(
        or_f(UserState.SubscriberInactive, UserState.SubscriberActive),
        or_f(UserState.TrialPeriodInactive, UserState.TrialPeriodActive)
    )
)
async def report_callback_handler(call: CallbackQuery, state: FSMContext) -> None:
    """
    Processing callback query menu "Report"
    """
    # Response to the Telegram server
    await call.answer()
    # Retrieving a command from a callback
    command = str(call.data).split(':')[1]
    if command == "question":
        # Calling the desired state
        await state.set_state(FormingReport.IdQuestion)
        await call.message.answer(
            text=client_text.input["QUESTION_ID"]
        )


@router.message(
    ChatTypeFilter("private"),
    F.text,
    FormingReport.IdQuestion,
    flags={"db_connect": True}
)
async def report_id(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Handling input id questions
    """
    # Input validation by number of characters
    if len(message.text) <= MAX_LEN_INPUT:
        try:
            # Attempting to convert to int
            question_id = int(message.text)
        except Exception:
            # Object cannot be converted to int
            await message.answer(
                text=client_text.errors["VALIDATION_REPORT_ID"]
            )
            return
        query = select(Question).where(Question.question_id == question_id)
        question = (await session.execute(query)).scalars().first()
        if question is None:
            # Record not found
            await message.answer(
                text=client_text.errors["VALIDATION_REPORT_ID"]
            )
        else:
            # Writing to temporary memory
            await state.update_data(
                question=question
            )
            # Calling the desired state
            await state.set_state(FormingReport.TextReport)
            await message.answer(
                text=client_text.input["REPORT_TEXT"]
            )
    else:
        # Input validation error
        await message.answer(
            text=client_text.errors["LEN_TEXT"]
        )


@router.message(
    ChatTypeFilter("private"),
    F.text,
    FormingReport.TextReport,
    flags={"db_connect": True}
)
async def report_text(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Processing text input
    """
    # Input validation by number of characters
    if len(message.text) <= MAX_LEN_TEXT:
        # Getting temporal data
        data = await state.get_data()
        # Deleting temporary data | Disabling state
        await state.clear()
        session.add(
            Report(
                question_id=data["question"],
                text=message.text
            )
        )
        await session.commit()
        # Notification of a successfully created record
        await message.answer(
            text=client_text.messages["REPORT_ACCEPT"],
            reply_markup=keyboard.keyboards["REPORT"]
        )
    else:
        # Input validation error
        await message.answer(
            text=client_text.errors["LEN_TEXT"]
        )
