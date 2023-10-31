import datetime
import logging

from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from bot.states import UserState
from bot.utils.tasks import afk
from models import User
from database import DoesNotExist, async_session_maker

from settings import TIME_AFK, TIME_AFK_SESSION, scheduler, client_text


class DeterminationMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        # Defining user's telegram_id
        if type(event) is Message:
            obj_for_answer = event
            user_id = event.from_user.id
        elif type(event) is CallbackQuery:
            user_id = event.from_user.id
            obj_for_answer = event.message
        else:
            return await handler(event, data)
        # Getting the current user state
        state: FSMContext = data["state"]
        state_now = await state.get_state()
        if state_now is None:
            # Issue a state to the user depending on the state of the possible license
            # Receiving a task that tracks user activity
            job = scheduler.get_job(job_id=f"{user_id}_active")
            if job is None:
                # If there is no task, we create
                job = scheduler.add_job(
                    id=f"{user_id}_active",
                    func=afk,
                    trigger="date",
                    run_date=datetime.datetime.now() + datetime.timedelta(seconds=TIME_AFK),
                    args=(user_id,)
                )
            else:
                # If there is a task, update it
                job.reschedule(
                    trigger="date",
                    run_date=datetime.datetime.now() + datetime.timedelta(seconds=TIME_AFK)
                )
            async with async_session_maker() as session:
                try:
                    query = select(User).where(User.user_id == user_id).options(
                        joinedload(User.license),
                        joinedload(User.data)
                    )
                    user = (await session.execute(query)).scalars().first()
                    if user is None:
                        raise DoesNotExist
                except DoesNotExist:
                    # If there is no record of the user, we give the registration status
                    await state.set_state(UserState.Unregister)
                    user = None
                except Exception as err:
                    # Error handling
                    logging.error(f"on_pre_process_message.\n{str(err)}", exc_info=True)
                    # Error notification
                    await obj_for_answer.answer(
                        text=client_text.errors["SOME_ERROR"]
                    )
                    # Removing user activity tracking to avoid possible errors
                    job.remove()
                    return
                else:
                    # If the user record is found, we give the status depending on the state of the license
                    license_active = True
                    if user.license.duration == 0:
                        license_active = False
                    if user.license.type == 1:
                        if license_active:
                            await state.set_state(UserState.TrialPeriodActive)
                        else:
                            await state.set_state(UserState.TrialPeriodInactive)
                    else:
                        if license_active:
                            await state.set_state(UserState.SubscriberActive)
                        else:
                            await state.set_state(UserState.SubscriberInactive)
                # Add a user record for further quick access
                await state.update_data(user_obj=user)
                data.update({"state": state, "raw_state": await state.get_state()})
        else:
            # Update the task of tracking user activity
            time = TIME_AFK
            if state_now == "SessionUser:Active":
                time = TIME_AFK_SESSION
            scheduler.reschedule_job(
                job_id=f"{user_id}_active",
                trigger="date",
                run_date=datetime.datetime.now() + datetime.timedelta(seconds=time)
            )
        return await handler(event, data)
