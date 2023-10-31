from aiogram import Router, F
from aiogram.filters import or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from re import match

from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from geopy.adapters import AioHTTPAdapter
from datetime import datetime, date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.chat_type import ChatTypeFilter
from bot.handlers.menu import main_menu
from bot.utils.tasks import send_notification, license_control

from database import DoesNotExist
from bot.states import Introduction, UserState
from models import Data, License, Statistic, Utm, User
from settings import client_text, keyboard, f_config, tzw, scheduler

router = Router()


@router.callback_query(
    ChatTypeFilter("private"),
    F.data == "register:start",
    Introduction.Intro
)
async def preview_registration_callback_handler(call: CallbackQuery, state: FSMContext) -> None:
    """
    Preview Registration Callback Handler
    """
    # Response to the Telegram server
    await call.answer()
    # State management
    await state.set_state(Introduction.Name)
    # Data entry request
    await call.message.answer(
        text=client_text.input["REGISTRATION_NAME"]
    )


@router.message(
    ChatTypeFilter("private"),
    F.text,
    Introduction.Name
)
async def registration_name(message: Message, state: FSMContext) -> None:
    """
    Entering a name when registering
    """
    # Value validation
    result = match(r'^[a-zA-Zа-яёА-ЯЁ\s\-]+$', message.text)
    if result is not None:
        # Data storage
        await state.update_data(
            full_name=message.text
        )
        # State management
        await state.set_state(Introduction.Rules)
        # Data entry request
        await message.answer(
            text=client_text.menus["ROLES"].format(message.text),
            reply_markup=keyboard.keyboards["ROLES"]
        )
    else:
        # Input validation error
        await message.answer(
            text=client_text.errors["VALIDATION_NAME"]
        )


@router.callback_query(
    ChatTypeFilter("private"),
    F.data == "register:rules_accept",
    Introduction.Rules
)
async def registration_roles_accept(call: CallbackQuery, state: FSMContext) -> None:
    """
    Adoption of rules
    """
    # Response to the Telegram server
    await call.answer()
    # State management
    await state.set_state(Introduction.Email)
    # Data entry request
    await call.message.answer(
        text=client_text.input["REGISTRATION_EMAIL"]
    )


@router.message(
    ChatTypeFilter("private"),
    F.text,
    Introduction.Email,
    flags={"db_connect": True}
)
async def registration_email(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Entering email when registering
    """
    # Value validation
    result = match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", message.text)
    if result is not None:
        # Checking email uniqueness
        try:
            # Database query
            query = select(Data).where(Data.email == str(message))
            data = (await session.execute(query)).scalars().first()
            if data is None:
                # Email is unique
                raise DoesNotExist
        except DoesNotExist:
            # Data storage
            await state.update_data(
                email=message.text
            )
            # State management
            await state.set_state(Introduction.Category)
            # Data entry request
            await message.answer(
                text=client_text.input["REGISTRATION_CATEGORY"],
                reply_markup=keyboard.select["CATEGORY"]
            )
        else:
            # Email is not unique
            await message.answer(
                text=client_text.errors["EMAIL_IS_BUSY"]
            )
    else:
        # Input validation error
        await message.answer(
            text=client_text.errors["VALIDATION_EMAIL"]
        )


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("category:"),
    Introduction.Category
)
async def registration_category(call: CallbackQuery, state: FSMContext) -> None:
    """
    Selecting category when registering
    """
    # Response to the Telegram server
    await call.answer()
    # Retrieving a command from a callback
    category = int(str(call.data).split(':')[1])
    # Data storage
    await state.update_data(
        category=f_config.text["KEYBOARDS_SELECT"]["CATEGORY"][category]
    )
    # State management
    await state.set_state(Introduction.Location)
    # Data entry request
    await call.message.answer(
        text=client_text.input["SET_LOCATION"],
        reply_markup=keyboard.geo
    )


@router.message(
    ChatTypeFilter("private"),
    F.location,
    Introduction.Location
)
async def registration_location(message: Message, state: FSMContext) -> None:
    """
    Set location when registering. Data from Telegram
    """
    # Defining the time zone by geolocation
    time_zone = tzw.timezone_at(lng=message.location.longitude, lat=message.location.latitude)
    # Data storage
    await state.update_data(
        time_zone=time_zone
    )
    # Removing the keyboard "geo"
    await message.answer("Отлично", reply_markup=ReplyKeyboardRemove())
    # State management
    await state.set_state(Introduction.NotificationTime)
    # Data entry request
    await message.answer(
        text=client_text.menus["SET_NOTIFICATION"],
        reply_markup=keyboard.keyboards["SET_NOTIFICATION"]
    )


@router.message(
    ChatTypeFilter("private"),
    F.text,
    Introduction.Location
)
async def registration_location_city(message: Message, state: FSMContext) -> None:
    """
    Set location when registering. Manual entry of the name.
    """
    # Determining the time zone by place name
    async with Nominatim(
            user_agent="ExamBotTest",
            adapter_factory=AioHTTPAdapter,
    ) as geolocator:
        try:
            geo = await geolocator.geocode(message.text)
        except GeocoderTimedOut:
            geo = None
    if geo is None:
        # Location is found
        await message.answer(
            text=client_text.errors["VALIDATION_LOCATION"]
        )
    else:
        # The place is set.
        # Defining the time zone by geolocation
        timezone_str = tzw.timezone_at(lat=geo.latitude, lng=geo.longitude)
        # Data storage
        await state.update_data(
            time_zone=timezone_str
        )
        # Removing the keyboard "geo"
        await message.answer("Отлично", reply_markup=ReplyKeyboardRemove())
        # State management
        await state.set_state(Introduction.NotificationTime)
        # Data entry request
        await message.answer(
            text=client_text.menus["SET_NOTIFICATION"],
            reply_markup=keyboard.keyboards["SET_NOTIFICATION"]
        )


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("time:"),
    Introduction.NotificationTime
)
async def registration_notification(call: CallbackQuery, state: FSMContext) -> None:
    """
    Set notification when registering
    """
    # Response to the Telegram server
    await call.answer()
    # Retrieving a command from a callback
    hour = int(str(call.data).split(':')[1])
    # Data storage
    await state.update_data(
        notification=f"{hour}:00"
    )
    # State management
    await state.set_state(Introduction.TrialPeriod)
    # Data entry request
    await call.message.answer(
        text=client_text.menus["TRIAL_PERIOD"],
        reply_markup=keyboard.keyboards["TRIAL_PERIOD"]
    )


@router.callback_query(
    ChatTypeFilter("private"),
    F.data == "trial_period_accept",
    Introduction.TrialPeriod,
    flags={"db_connect": True}
)
async def registration_trial_period_accept(
        call: CallbackQuery,
        state: FSMContext,
        session: AsyncSession
) -> None:
    """
    Accept Trial Period When Registering
    """
    # Response to the Telegram server
    await call.answer()
    # Getting data
    data = await state.get_data()
    # Deleting data & Disabling state
    await state.clear()

    # Creating or editing a new user record
    license_new = License(
        type=1,
        telegram_id=call.from_user.id,
        duration=3,
        name="Trial Period"
    )
    data_t = Data(
        telegram_id=call.from_user.id,
        date_registered=date.today(),
        date_last_activity=date.today(),
        last_session=date(year=2019, month=3, day=2),
        count_session=0,
        full_name=data["full_name"],
        notification=data["notification"],
        email=data["email"],
        category=data["category"],
        time_zone=data["time_zone"],
    )
    statistics = Statistic(
        telegram_id=call.from_user.id,
        summary=f_config.text["STATISTIC_TEMPLATE"],
        incorrect=f_config.text["INCORRECT_TEMPLATE"]
    )
    utm = Utm(
        telegram_id=call.from_user.id,
        utm=data["utm"],
        registered=True,
        date_time=data["date"]
    )
    user = User(
        user_id=call.from_user.id,
        license=license_new,
        utm=utm,
        data=data_t,
        statistic=statistics
    )
    session.add_all([license_new, data_t, statistics, utm, user])
    await session.commit()
    # Creating a job to notify the user
    time = data["notification"].split(":")
    time_now = datetime.now()
    scheduler.add_job(
        send_notification,
        "cron",
        id=f"{call.from_user.id}_notification",
        hour=time[0], minute=time[1], timezone=data["time_zone"],
        args=(call.from_user.id,)
    )
    scheduler.add_job(
        license_control,
        "cron",
        id=f"{call.from_user.id}_license_control",
        hour=time_now.hour, minute=time_now.minute, timezone=data["time_zone"],
        args=(call.from_user.id,)
    )
    await call.message.answer(
        text=client_text.menus["FIRST_SESSION"],
        reply_markup=keyboard.keyboards["FIRST_SESSION"]
    )


@router.callback_query(
    ChatTypeFilter("private"),
    F.data.startswith("first_session:"),
    or_f(UserState.TrialPeriodActive, UserState.SubscriberActive)
)
async def first_session_handler(call: CallbackQuery) -> None:
    """
    First Session Callback Handler
    """
    # Response to the Telegram server
    await call.answer()
    # Retrieving a command from a callback
    command = str(call.data).split(':')[1]
    if command == "start":
        pass
        # Start of session
        # await session_menu(call=call)
    elif command == "skip":
        # Calling the main menu
        await main_menu(call=call)


@router.callback_query(
    ChatTypeFilter("private"),
    StateFilter(Introduction)
)
async def surprise_signal_processing(call: CallbackQuery) -> None:
    # Response to the Telegram server
    await call.answer()
