import logging

from fastapi import APIRouter, Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import HTMLResponse

from src.site.auth.base_config import current_active_user
from src.site.auth.models import User as UserAdmin
from database import get_async_session
from models import User
from settings import templates

router = APIRouter(prefix="/users", tags=["user"])


@router.get("/table/{number_list}", response_class=HTMLResponse)
async def users_table(
        request: Request,
        number_list: int,
        user: UserAdmin = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):

    if number_list <= 0:
        number_list = 1
    try:
        query = select(User).options(
            joinedload(User.data)
        )
        users = (await session.execute(query)).scalars().all()
        users = users[10*(number_list-1):10*number_list]
    except Exception as er:
        logging.error(f"/question/add.{er}", exc_info=True)
        return templates.TemplateResponse(
            "index_error.html", {"request": request}
        )
    else:
        return templates.TemplateResponse(
            "users_table.html", {"request": request, "users": users, "number_list": number_list}
        )
