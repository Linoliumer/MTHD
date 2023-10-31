import logging
from sqlalchemy import select
from datetime import date

from sqlalchemy.orm import joinedload

from bot.utils.save_session import save_session
from settings import bot, client_text, keyboard, dp, scheduler
from models import Utm, User
from database import async_session_maker


async def afk(user_id: int) -> None:
    """
    The end of states due to inactivity of the user for a certain period of time
    """
    # Getting the current user state
    state = dp.fsm.resolve_context(bot, chat_id=user_id, user_id=user_id)
    state_now = await state.get_state()

    async with async_session_maker() as session:
        query = select(User).where(User.user_id == user_id)
        user = (await session.execute(query)).scalars().first()
        if user is not None:
            user.date_last_activity = date.today()
            await session.commit()

    if state_now is not None:
        if state_now == "SessionUser:Active":
            # Ending and saving session data
            try:
                data = await state.get_data()
                session = await save_session(data=data, status=2)
                await bot.send_message(
                    chat_id=user_id,
                    text=client_text.menus["SESSION_END"].format(
                        session.total,
                        session.total_questions,
                        session.correct
                    ),
                    reply_markup=keyboard.keyboards["SESSION_END"]
                )
            except Exception as e:
                logging.error(f"afk\n{str(e)}", exc_info=True)
        elif (state_now == "UserCondition:Unregister") or ("Introduction" in state_now):
            data = await state.get_data()
            try:
                async with async_session_maker() as session:
                    session.add(
                        Utm(
                            telegram_id=user_id,
                            utm=data["utm"],
                            date_time=data["date"],
                            registered=False
                        )
                    )
                    await session.commit()
            except Exception as e:
                logging.error(f"afk\n{str(e)}", exc_info=True)
        await state.clear()


async def send_notification(user_id: int) -> None:
    """
    Notification to the user about the possibility of starting a session
    """
    # Getting the current user state
    state = dp.fsm.resolve_context(bot, chat_id=user_id, user_id=user_id)
    state_now = await state.get_state()
    if state_now != "SessionUser:Active":
        job = scheduler.get_job(job_id=f"{user_id}_block_session")
        if job is None:
            try:
                # Sending notification
                await bot.send_message(
                    chat_id=user_id,
                    text=client_text.messages["NOTIFICATION"],
                    reply_markup=keyboard.keyboards["GO_TO_SESSION"]
                )
            except Exception as e_n:
                # Error
                logging.error(
                    f"send_notification.\n{str(e_n)}",
                    exc_info=True
                )


async def license_control(user_id: int) -> None:
    """
    The end of states due to inactivity of the user for a certain period of time
    """
    # Getting the current user state
    try:
        async with async_session_maker() as session:
            query = select(User).where(User.user_id == user_id).options(joinedload(User.license))
            user = (await session.execute(query)).scalars().first()
            if user is None:
                job = scheduler.get_job(job_id=f"{user_id}_license_control")
                if job is None:
                    return
                else:
                    job.remove()
            else:
                if user.license.duration == 0:
                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text=client_text.messages["SUBSCRIBE_EXPIRED"],
                            reply_markup=keyboard.keyboards["GO_TO_OFFER"]
                        )
                    except:
                        logging.error(f"Can't send notification to user_id {user.user_id}")
                else:
                    user.license.duration -= 1
                    if user.license.duration == 0:
                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text=client_text.messages["SUBSCRIBE_EXPIRED"],
                                reply_markup=keyboard.keyboards["GO_TO_OFFER"]
                            )
                        except:
                            logging.error(f"2Can't send notification to user_id {user.user_id}")
                    elif 1 <= user.license.duration <= 3:
                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text=client_text.messages["LICENSE_CONTROL"].format(user.license.duration)
                            )
                        except:
                            logging.error(f"3Can't send notification to user_id {user.user_id}")
                    await session.commit()
    except Exception as err:
        logging.error(
            f"license_control.\n{err}",
            exc_info=True
        )


async def none_func() -> None:
    return
