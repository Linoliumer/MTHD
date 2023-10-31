import logging
from datetime import datetime, timedelta
from pytz import timezone
from enum import Enum
from random import choice

from aiogram import Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.chat_type import ChatTypeFilter
from bot.states import UserState, SessionUser, Processing
from bot.utils.answer_check import answer_check
from bot.utils.menus import error_menu
from bot.utils.save_session import save_session
from bot.utils.tasks import none_func
from database import async_session_maker
from models import Statistic, Question, Session
from settings import scheduler, client_text, keyboard, TIME_AFK_SESSION, COUNT_QUESTIONS


class TypeSession(Enum):
    Regular = 1
    Mistakes = 2


class NotEnough(Exception):
    pass


router = Router()


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("session:"),
    or_f(UserState.SubscriberActive, UserState.TrialPeriodActive),
    flags={"db_connect": True}
)
async def session_callback_handler(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    # Response to the Telegram server
    await call.answer()
    state_now = await state.get_state()
    # Retrieving a command from a callback
    command = str(call.data).split(':')[1]
    if state_now == "UserState:TrialPeriodActive":
        job = scheduler.get_job(
            job_id=f"{call.from_user.id}_block_session"
        )
        if job is not None:
            await call.message.answer(
                text=client_text.menus["SUBSCRIBE_INACTIVE"],
                reply_markup=keyboard.keyboards["SUBSCRIBE_INACTIVE"]
            )
            return
    await state.set_state(SessionUser.Active)
    if command == "start":
        try:
            # Getting the need
            await get_questions(state=state, type_session=TypeSession.Regular, session=session)
        except NotEnough:
            # Error Logging
            logging.error(
                f"session_callback_handler | user: {call.from_user.id}| NotEnough",
                exc_info=True
            )
            # Deleting temporary data | Disabling state
            await state.clear()
            # Calling the error menu
            await call.message.answer(
                text=client_text.errors["NOT_ENOUGH"],
                reply_markup=keyboard.keyboards["NOT_ENOUGH_QUESTIONS"]
            )
            return
        except Exception as e:
            # Error Logging
            logging.error(
                f"session_callback_handler | user: {call.from_user.id}\n{str(e)}",
                exc_info=True
            )
            # Deleting temporary data | Disabling state
            await state.clear()
            # Calling the error menu
            await error_menu(call=call)
            return
    elif command == "mistakes":
        try:
            # Getting the need
            await get_questions(state=state, type_session=TypeSession.Mistakes, session=session)
        except NotEnough:
            # Error Logging
            logging.error(
                f"session_callback_handler | user: {call.from_user.id}| NotEnough",
                exc_info=True
            )
            # Deleting temporary data | Disabling state
            await state.clear()
            # Calling the error menu
            await call.message.answer(
                text=client_text.errors["NOT_ENOUGH_MISTAKES"],
                reply_markup=keyboard.keyboards["NOT_ENOUGH_QUESTIONS"]
            )
            return
        except Exception as e:
            # Error Logging
            logging.error(
                f"session_callback_handler | user: {call.from_user.id}\n{str(e)}",
                exc_info=True
            )
            # Deleting temporary data | Disabling state
            await state.clear()
            # Calling the error menu
            await error_menu(call=call)
            return
    else:
        return
    # Update the task of tracking user activity
    scheduler.reschedule_job(
        job_id=f"{call.from_user.id}_active",
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=TIME_AFK_SESSION)
    )
    if state_now == "UserState:TrialPeriodActive":
        user_time_zone = (await state.get_data())["user_obj"].data.time_zone
        tomorrow = (
                datetime.now(tz=timezone(user_time_zone)) + timedelta(days=1)
        ).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        scheduler.add_job(
            none_func,
            id=f"{call.from_user.id}_block_session",
            trigger="date",
            run_date=tomorrow
        )
    # Sending the first question
    await send_questions(message=call.message, state=state)


async def get_questions(state: FSMContext, type_session: TypeSession, session: AsyncSession) -> None:
    user = (await state.get_data())["user_obj"]
    query = select(Statistic).where(Statistic.telegram_id == int(user.user_id))
    statistic = (await session.execute(query)).scalars().one()
    questions_session = []
    if type_session == TypeSession.Regular:
        for i in range(1, COUNT_QUESTIONS+1):
            query = select(Question).where(Question.type == i)
            questions = (await session.execute(query)).scalars().all()
            while True:
                if questions:
                    entry = choice(questions)
                    if entry.question_id in statistic.incorrect:
                        questions.remove(entry)
                    else:
                        break
                else:
                    raise NotEnough
            questions_session.append(entry)
    elif type_session == TypeSession.Mistakes:
        if len(statistic.incorrect) >= COUNT_QUESTIONS:
            i = 0
            del_answers = []
            for question_id in statistic.incorrect:
                query = select(Question).where(Question.question_id == int(question_id))
                question = (await session.execute(query)).scalars().one()
                questions_session.append(question)
                del_answers.append(question_id)
                i += 1
                if i == COUNT_QUESTIONS:
                    break
            temp = set(statistic.incorrect)
            temp ^= set(del_answers)
            query = update(Statistic).where(Statistic.telegram_id == int(user.user_id)).values(
                incorrect=list(temp)
            )
            await session.execute(query)
        else:
            raise NotEnough
        await session.commit()
    await state.update_data(
        telegram_id=user.user_id,
        session=Session(
            session_id=int(f"{user.user_id}{user.data.count_session}"),
            statistic_id=statistic.statistic_id,
            date_session=datetime.today(),
            duration=0,
            status=0
        ),
        questions=questions_session,
        stage=0,
        answers=[]
    )


async def end_session(data: dict, state: FSMContext = None, message: Message = None) -> None:
    # Deleting temporary data | Disabling state
    await state.clear()
    async with async_session_maker() as session:
        session_statistic = await save_session(data=data, status=1, session=session)
    # Calling session end notification
    await message.answer(
        text=client_text.menus["SESSION_END"].format(
            session_statistic.total,
            session_statistic.total_questions,
            session_statistic.correct
        ),
        reply_markup=keyboard.keyboards["SESSION_END"]
    )


async def send_questions(state: FSMContext, message: Message = None):
    """
    Send Question
    :param message:
    :param state:
    :return:
    """
    await state.set_state(Processing.Active)
    # Getting temporal data
    data = await state.get_data()
    # Checking for the end of the session
    if data["stage"] == COUNT_QUESTIONS:
        try:
            # End of session
            await end_session(state=state, message=message, data=data)
        except Exception as e:
            # Event Logging
            logging.error(f"send_questions\n{str(e)}", exc_info=True)
            # Deleting temporary data | Disabling state
            await state.clear()
            # Calling error menu
            await error_menu(message=message)
        return
    await state.set_state(SessionUser.Active)
    # Writing to temporary memory
    await state.update_data(
        time=datetime.today(),
        stage=data["stage"] + 1
    )
    text = client_text.input["GET_ANSWER"].format(
               data["questions"][data["stage"]].type,
               data["questions"][data["stage"]].question_id,
               data["questions"][data["stage"]].section,
               data["questions"][data["stage"]].element,
               data["questions"][data["stage"]].question_text
            )
    # Sending a previously generated job
    if data["questions"][data["stage"]].link != "None":
        await message.answer_photo(
            photo=data["questions"][data["stage"]].link,
            caption=text
        )
    else:
        await message.answer(
           text=text
        )


@router.message(
    ChatTypeFilter("private"),
    F.text,
    SessionUser.Active
)
async def answer_processing(message: Message, state: FSMContext):
    # Getting temporal data
    data = await state.get_data()
    # Writing to temporary memory
    try:
        int(message.text)
    except:
        await message.answer(text=client_text.errors["VALIDATION_ANSWER"])
    else:
        result = await answer_check(message.text, data["questions"][data["stage"]-1])
        text = client_text.messages["ANSWER_ACCEPT"]
        data["answers"].append(result)
        await message.answer(
            text=text
        )
        await state.update_data(
            answers=data["answers"]
        )
        # Send next question
        await send_questions(message=message, state=state)
