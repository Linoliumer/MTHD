from fastapi import APIRouter, Request, Depends
from starlette.responses import HTMLResponse
from src.site.auth.models import User as UserAdmin
from src.site.auth.base_config import current_active_user

from settings import templates

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/", response_class=HTMLResponse)
async def index_html(request: Request, user: UserAdmin = Depends(current_active_user)):

    return templates.TemplateResponse(
        "index.html", {"request": request, "user": UserAdmin, "endpoint": "main"}
    )


@router.get("/error", response_class=HTMLResponse)
async def main_html(request: Request, user: UserAdmin = Depends(current_active_user)):

    return templates.TemplateResponse(
        "index_error.html", {"request": request, "user": UserAdmin}
    )