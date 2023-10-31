from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.answer_check import CHECK
from bot.utils.statistic import SessionStatistic
from models import Statistic, Data
from settings import COUNT_QUESTIONS


async def save_session(data: dict, status: int, session: AsyncSession) -> SessionStatistic:
    # Forming session data
    score_session = 0
    i = 0
    transcript_session = ""

    query = select(Statistic).where(Statistic.telegram_id == int(data["telegram_id"]))
    statistic = (await session.execute(query)).scalar()
    incorrect_answers_session = []
    for element in data["answers"]:
        if (element == CHECK.CORRECT_2) or (element == CHECK.CORRECT_1):
            score = 1
            if element == CHECK.CORRECT_2:
                score = 2
            statistic.summary[f"{data['questions'][i].section}"][f"{data['questions'][i].element}"][0] += 1
        elif element == CHECK.PARTLY:
            score = 1
            statistic.summary[f"{data['questions'][i].section}"][f"{data['questions'][i].element}"][1] += 1
            incorrect_answers_session.append(data['questions'][i].question_id)
        else:
            score = 0
            incorrect_answers_session.append(data['questions'][i].question_id)
        transcript_session += f"{data['questions'][i].question_id}-{score};"
        statistic.summary[f"{data['questions'][i].section}"][f"{data['questions'][i].element}"][2] += 1
        score_session += score
        i += 1
    data["session"].duration = 0
    data["session"].status = status
    data["session"].score = score_session
    data["session"].transcript = transcript_session
    query = update(Data). \
        where(Data.telegram_id == int(data["telegram_id"])). \
        values(
            count_session=Data.count_session+1,
            last_session=data["session"].date_session
        )
    await session.execute(query)
    # Saving related session data
    statistic.incorrect = list(set(statistic.incorrect) ^ set(incorrect_answers_session))
    query = update(Statistic).where(Statistic.telegram_id == int(statistic.telegram_id)).values(
        incorrect=statistic.incorrect,
        summary=statistic.summary
    )
    await session.execute(query)
    session.add(data["session"])
    await session.commit()
    session_statistic = SessionStatistic(
        total=i,
        correct=score_session,
        total_questions=COUNT_QUESTIONS
    )
    return session_statistic
