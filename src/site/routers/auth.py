from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from settings import templates

router = APIRouter(prefix="/login", tags=["auth"])


@router.get("/", response_class=HTMLResponse)
async def auth_html(request: Request):
    return templates.TemplateResponse(
        "auth.html", {"request": request}
    )

