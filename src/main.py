import logging
import uvicorn

from aiogram import types
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from bot.middlewares.determination import DeterminationMiddleware
from bot.middlewares.db_connection import DbSessionMiddleware
from database import engine, Base, async_session_maker
from settings import BASE_DIR, bot, WEBHOOK_URL, WEBHOOK_PATH, dp, WEBAPP_HOST, WEBAPP_PORT, scheduler
from bot.handlers.registration import router as registration_router
from bot.handlers.unknown import router as unknown_router
from bot.handlers.menu import router as menu_router
from bot.handlers.profile import router as profile_router
from bot.handlers.report import router as report_router
from bot.handlers.session import router as session_router
from bot.handlers.payments import router as payments_router
from bot.handlers.inactive import router as inactive_router
from src.site.auth.base_config import fastapi_users, auth_backend
from src.site.auth.schemas import UserRead, UserCreate

from src.site.routers.auth import router as f_auth_router
from src.site.routers.download import router as f_download_router
from src.site.routers.index import router as f_index_router
from src.site.routers.question import router as f_question_router
from src.site.routers.statistic import router as f_statistic_router
from src.site.routers.user import router as f_user_router


app = FastAPI()

# Registering static files

app.mount(
    "/static",
    StaticFiles(directory=f"{BASE_DIR}/src/site/static/"),
    name="static",
)

app.include_router(f_auth_router)
app.include_router(f_download_router)
app.include_router(f_question_router)
app.include_router(f_statistic_router)
app.include_router(f_index_router)
app.include_router(f_user_router)


# Connecting routers of the authorization module
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)


@app.on_event("startup")
async def on_startup() -> None:
    """
    Launching the FastAPI application and presetting
    :return:
    """
    # Create table in database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Connecting routers
    dp.include_routers(
        registration_router,
        menu_router,
        profile_router,
        report_router,
        session_router,
        payments_router,
        inactive_router,
        unknown_router
    )
    # Including middlewares
    temp = DbSessionMiddleware(session_pool=async_session_maker)
    dp.message.outer_middleware(DeterminationMiddleware())
    dp.callback_query.outer_middleware(DeterminationMiddleware())
    dp.message.middleware(temp)
    dp.callback_query.middleware(temp)
    dp.pre_checkout_query.middleware(temp)
    # Running the task manager
    scheduler.start()
    # Setting url for webhooks
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True
        )
        logging.info("WEBHOOK SET")
    logging.info("WEBHOOK DETECTED")


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict) -> None:
    """
    Processing POST request data from telegram server
    :return:
    """
    telegram_update = types.Update(**update)
    try:
        await dp.feed_update(bot=bot, update=telegram_update)
    except Exception as error:
        logging.error(f"{error}", exc_info=True)


@app.on_event("shutdown")
async def on_shutdown() -> None:

    """
    Stopping FastAPI and related applications
    :return:
    """
    # Receiving and closing the current session
    await bot.session.close()
    await engine.dispose()


if __name__ == "__main__":
    # Running the server
    uvicorn.run(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
