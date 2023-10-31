from fastapi import APIRouter, Request, Depends
from starlette.responses import HTMLResponse

from src.site.auth.models import User as UserAdmin
from src.site.auth.base_config import current_active_user
from settings import templates

router = APIRouter(prefix="/statistic", tags=["statistic"])


@router.get("/", response_class=HTMLResponse)
async def statistic_html(request: Request, user: UserAdmin = Depends(current_active_user)):

    return templates.TemplateResponse(
        "statistic.html", {"request": request}
    )
