import aiofiles
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse

from database import get_async_session
from src.site.auth.base_config import current_active_user
from src.site.auth.models import User as UserAdmin

from models import Utm, User
from settings import BASE_DIR

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/utm", response_class=FileResponse)
async def download_stats_utm(
        user: UserAdmin = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):

    utm_list = (await session.execute(select(Utm))).scalars().all()
    result = ""
    template = "{};{};{};{};{}\n"
    async with aiofiles.open(f"{BASE_DIR}/temp/temp.csv", mode="w") as file:
        for utm in utm_list:
            result += template.format(
                utm.utm_id,
                utm.telegram_id,
                utm.utm,
                utm.registered,
                utm.date_time
            )
        await file.write(result)
        return FileResponse(
            path=f'{BASE_DIR}/temp/temp.csv',
            filename='MTHD_UTM_STATS.csv',
            media_type='multipart/form-data'
        )


@router.get("/users", response_class=FileResponse)
async def download_stats_utm(
        user: UserAdmin = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):

    users = (await session.execute(select(User))).scalars().all()
    result = ""
    template = "{};{};{};{};{}\n"
    async with aiofiles.open(f"{BASE_DIR}/temp/temp.csv", mode="w") as file:
        for user in users:
            result += template.format(
                user.user_id,
                user.license_id,
                user.utm_id,
                user.data_id,
                user.statistic_id
            )
        await file.write(result)
        return FileResponse(
            path=f'{BASE_DIR}/temp/temp.csv',
            filename='MTHD_USERS_STATS.csv',
            media_type='multipart/form-data'
        )


@router.get("/logs", response_class=FileResponse)
async def download_logs(user: UserAdmin = Depends(current_active_user)):

    return FileResponse(
        path=f'{BASE_DIR}/logs/logs.txt',
        filename='LOGS.txt',
        media_type='multipart/form-data'
    )
