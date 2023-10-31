import json
import logging

from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile
from fastapi import File as File_Fastapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from src.site.auth.models import User as UserAdmin

from src.site.auth.base_config import current_active_user

from database import get_async_session
from models import Question
from settings import templates

router = APIRouter(prefix="/questions", tags=["question"])


@router.get("/", response_class=HTMLResponse)
async def questions_html(request: Request, user: UserAdmin = Depends(current_active_user)):

    return templates.TemplateResponse(
        "questions.html", {"request": request}
    )


@router.get("/table/{number_list}", response_class=HTMLResponse)
async def questions_table_html(
        request: Request, number_list: int,
        user: UserAdmin = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):

    if number_list <= 0:
        number_list = 1
    try:
        query = select(Question).filter(
            Question.question_id >= 10*(number_list-1),
            Question.question_id <= 10*number_list
        )
        questions = (await session.execute(query)).scalars().all()
    except Exception as er:
        logging.error(f"/questions/table/<number_list>.\n{er}", exc_info=True)
        return templates.TemplateResponse(
            "index_error.html", {"request": request}
        )
    else:
        return templates.TemplateResponse(
            "questions_table.html", {"request": request, "questions": questions, "number_list": number_list}
        )


@router.get("/add", response_class=HTMLResponse)
async def main_html(request: Request, user: UserAdmin = Depends(current_active_user)):

    return templates.TemplateResponse(
        "questions_add.html", {"request": request}
    )


@router.post("/add/create")
async def question_create(
        type_question: str = Form(...),
        section: int = Form(...),
        element: int = Form(...),
        question_text: str = Form(...),
        answer_user: str = Form(...),
        user: UserAdmin = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        session.add(
            Question(
                type=int(type_question),
                section=int(section),
                element=int(element),
                link="None",
                question_text=question_text,
                answer_user=answer_user
            )
        )
        await session.commit()
    except Exception as er:
        logging.error(f"/question/add.\n{er}", exc_info=True)
        raise HTTPException(status_code=500)


@router.post("/add/csv")
async def question_create(
        upload_file: UploadFile = File_Fastapi(...),
        user: UserAdmin = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):

    if upload_file.content_type == "application/json":
        text = json.loads(upload_file.file.read())
        for element in text["questions"]:
            try:
                query_select = select(Question).filter(
                    Question.type == int(element["type"]),
                    Question.section == int(element["section"]),
                    Question.element == int(element["element"]),
                    Question.link == str(element["link"]),
                    Question.question_text == str(element["question_text"]),
                    Question.answer_user == str(element["answer_user"])
                )
                question = (await session.execute(query_select)).scalars().first()
                if question is None:
                    session.add(
                        Question(
                            type=element["type"],
                            section=element["section"],
                            element=element["element"],
                            link=element["link"],
                            question_text=str(element["question_text"]),
                            answer_user=str(element["answer_user"]),
                        )
                    )
                    await session.commit()
            except Exception as e:
                upload_file.file.close()
                logging.error(f"/questions/add/csv | {e}", exc_info=True)
                raise HTTPException(status_code=422)
        upload_file.file.close()
        raise HTTPException(status_code=200)
    raise HTTPException(status_code=422)
