from aiogram import Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.chat_type import ChatTypeFilter
from bot.states import UserState, Change
from bot.utils.menus import profile_menu
from bot.utils.statistic import form_statistic, Statistic
from models import Data
from settings import client_text, keyboard, scheduler

router = Router()


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("profile:"),
    or_f(UserState.SubscriberActive, UserState.TrialPeriodActive)
)
async def profile_callback_handler(call: CallbackQuery, state: FSMContext) -> None:
    """
    Processing callback query menu "Profile"
    """
    # Response to the Telegram server
    await call.answer()
    # Retrieving a command from a callback
    command = str(call.data).split(':')[1]
    if command == "change_notification_time":
        # Changing notification times
        await start_change_notification(call=call, state=state)


async def start_change_notification(
        state: FSMContext,
        call: CallbackQuery = None,
        message: Message = None
) -> None:
    """
    Starting a chain of inputs to change alert times
    """
    #  Defining (the type of update)&(a user's telegram id)
    if call is None:
        obj_for_answer = message
    else:
        obj_for_answer = call.message
    # Calling the desired state
    await state.set_state(Change.ChangeNotification)
    await obj_for_answer.answer(
        text=client_text.menus["SET_NOTIFICATION"],
        reply_markup=keyboard.keyboards["SET_NOTIFICATION"]
    )


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("time:"),
    Change.ChangeNotification,
    flags={"db_connect": True}
)
async def change_notification(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    """
    Handling input time notification
    """
    # Response to the Telegram server
    await call.answer()
    # Retrieving a command from a callback
    hour = int(str(call.data).split(':')[1])
    # Value validation
    user = (await state.get_data())["user_obj"]
    await state.clear()
    # Creating a new job
    job = scheduler.get_job(
        job_id=f"{call.from_user.id}_notification"
    )
    job.reschedule(
        trigger="cron",
        hour=hour, timezone=user.data.time_zone,
    )
    # Saving the received information
    user.data.notification = f"{hour}:00"
    query = update(Data). \
        where(Data.telegram_id == int(user.user_id)). \
        values(notification=f"{hour}:00")
    await session.execute(query)
    await session.commit()
    # Calling the profile menu
    await profile_menu(call=call, user=user)


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("statistic:"),
    UserState.SubscriberActive
)
async def profile_callback_handler(call: CallbackQuery, state: FSMContext) -> None:
    """
    Processing callback query menu "Profile"
    """
    # Response to the Telegram server
    await call.answer()
    try:
        stat_obj = (await state.get_data())["statistic"]
    except KeyError:
        stat_obj = await form_statistic(call.from_user.id)
        await state.update_data(statistic=stat_obj)
    # Retrieving a command from a callback
    command = str(call.data).split(':')[1]
    if command == "1":
        await statistic_section(
            statistic=stat_obj,
            section=1,
            call=call
        )
    elif command == "2":
        await statistic_section(
            statistic=stat_obj,
            section=2,
            call=call
        )
    elif command == "3":
        await statistic_section(
            statistic=stat_obj,
            section=3,
            call=call
        )
    elif command == "4":
        await statistic_section(
            statistic=stat_obj,
            section=4,
            call=call
        )
    elif command == "5":
        await statistic_section(
            statistic=stat_obj,
            section=5,
            call=call
        )


async def statistic_section(
    statistic: Statistic,
    section: int,
    call: CallbackQuery = None,
    message: Message = None
) -> None:
    if call is None:
        # If the function is called by the trigger on the message
        obj_for_answer = message
    else:
        # If the function is called callback
        obj_for_answer = call.message

    section_obj = statistic.sections[section-1]

    elements = ""
    i = 1
    for element in section_obj.elements:
        elements += client_text.messages["ELEMENT_TEMPLATE"].format(
            i, element.name, element.total, f"{int(element.interest*100)}%"
        )
        i += 1

    await obj_for_answer.answer(
        text=client_text.menus["STATISTIC_SECTION"].format(
            section, section_obj.total,
            f"{int(section_obj.interest*100)}%",
            elements
        ),
        reply_markup=keyboard.keyboards["STATISTIC_SECTION"]
    )
