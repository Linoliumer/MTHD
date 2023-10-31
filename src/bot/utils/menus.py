from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.states import Introduction
from bot.utils.statistic import form_statistic
from models import User
from settings import client_text, keyboard


async def register_menu(
        state: FSMContext,
        call: CallbackQuery = None,
        message: Message = None
) -> None:
    """
    Displaying the "Registration" menu
    """
    # Label Definition (UNLABELLED)
    try:
        utm = message.text.split(" ")[1]
    except:
        utm = "None"
    # Defining (the type of update)&(a user's telegram id)
    if call is None:
        obj_for_answer = message
    else:
        obj_for_answer = call.message
    # Data storage
    await state.update_data(
        utm=utm,
        date=datetime.now()
    )
    # State management
    await state.set_state(Introduction.Intro)
    # Calling the continued dating menu
    await obj_for_answer.answer(
        text=client_text.menus["REGISTER"],
        reply_markup=keyboard.keyboards["REGISTER"]
    )


async def main_menu(call: CallbackQuery = None, message: Message = None) -> None:
    """
    Displaying the "Main" menu
    """
    #  Defining (the type of update)&(a user's telegram id)
    if call is None:
        obj_for_answer = message
    else:
        obj_for_answer = call.message

    # Calling the main menu
    await obj_for_answer.answer(
        text=client_text.menus["MAIN"],
        reply_markup=keyboard.keyboards["MAIN"]
    )


async def profile_menu(
        state: FSMContext = None,
        call: CallbackQuery = None,
        message: Message = None,
        user: User = None
) -> None:
    """
    Displaying the "Profile" menu
    """
    if call is None:
        # If the function is called by the trigger on the message
        obj_for_answer = message
    else:
        # If the function is called callback
        obj_for_answer = call.message
    if user is None:
        # Getting a user record
        user = (await state.get_data())["user_obj"]
    # Calling the profile menu
    await obj_for_answer.answer(
        text=client_text.menus["PROFILE"].format(
            user.data.full_name,
            user.data.email,
            user.data.count_session,
            user.data.last_session,
            user.data.notification
        ),
        reply_markup=keyboard.keyboards["PROFILE"]
    )


async def info_menu(call: CallbackQuery = None, message: Message = None) -> None:
    """
    Displaying the "Info" menu
    """
    if call is None:
        # If the function is called by the trigger on the message
        obj_for_answer = message
    else:
        # If the function is called callback
        obj_for_answer = call.message

    # Calling the info menu
    await obj_for_answer.answer(
        text=client_text.menus["INFO"],
        reply_markup=keyboard.keyboards["INFO"]
    )


async def profile_statistic(
        call: CallbackQuery = None,
        message: Message = None,
        state: FSMContext = None
) -> None:
    """
    Displaying the "Statistic"
    """
    if call is None:
        # If the function is called by the trigger on the message
        obj_for_answer = message
        user_id = message.from_user.id
    else:
        # If the function is called callback
        obj_for_answer = call.message
        user_id = call.from_user.id
    try:
        stat_obj = (await state.get_data())["statistic"]
    except KeyError:
        stat_obj = await form_statistic(user_id)
        await state.update_data(statistic=stat_obj)
    sections = ""
    i = 1
    for section in stat_obj.sections:
        sections += client_text.messages["ELEMENT_TEMPLATE"].format(
            i, section.name, section.total, f"{int(section.interest*100)}%"
        )
        i += 1
    # Calling the statistic
    await obj_for_answer.answer(
        text=client_text.menus["STATISTIC"].format(
            stat_obj.total,
            f"{int(stat_obj.interest * 100)}%",
            sections
        ),
        reply_markup=keyboard.keyboards["STATISTIC"]
    )


async def report_menu(call: CallbackQuery = None, message: Message = None) -> None:
    """
    Displaying the "Report" menu
    """
    if call is None:
        # If the function is called by the trigger on the message
        obj_for_answer = message
    else:
        # If the function is called callback
        obj_for_answer = call.message

    # Calling the report menu
    await obj_for_answer.answer(
        text=client_text.menus["REPORT"],
        reply_markup=keyboard.keyboards["REPORT"]
    )


async def session_menu(call: CallbackQuery = None, message: Message = None) -> None:
    """
    Displaying the "Session" menu
    """
    if call is None:
        # If the function is called by the trigger on the message
        obj_for_answer = message
    else:
        # If the function is called callback
        obj_for_answer = call.message

    # Calling the session menu
    await obj_for_answer.answer(
        text=client_text.menus["SESSION"],
        reply_markup=keyboard.keyboards["SESSION"]
    )


async def error_menu(call: CallbackQuery = None, message: Message = None) -> None:
    """
    Displaying the "Error" menu
    """
    if call is None:
        # If the function is called by the trigger on the message
        obj_for_answer = message
    else:
        # If the function is called callback
        obj_for_answer = call.message

    # Calling the profile menu
    await obj_for_answer.answer(
        text=client_text.menus["ERROR"],
        reply_markup=keyboard.keyboards["ERROR"]
    )
