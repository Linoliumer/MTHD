from sqlalchemy import select
from typing import List

from database import async_session_maker
from models import Statistic as Statistic_DB
from settings import f_config


class SessionStatistic:
    correct: int
    total: int
    total_questions: int

    def __init__(self, correct: int, total: int, total_questions: int):
        self.total = total
        self.correct = correct
        self.total_questions = total_questions


class Element:
    name: str
    interest: float
    correct: int
    partial: int
    total: int

    def __init__(self, name: str, correct: int, total: int, partial: int):
        self.name = name
        self.total = total
        self.partial = partial
        self.correct = correct
        try:
            self.interest = (self.correct + self.partial/2) / self.total
        except ZeroDivisionError:
            self.interest = 0


class Section:
    name: str
    interest: float
    correct: int
    total: int
    partial: int
    elements: List[Element]

    def __init__(self, name: str):
        self.name = name
        self.interest = 0
        self.total = 0
        self.correct = 0
        self.partial = 0
        self.elements = []

    async def form_sections(self, sections: dict):
        elements = f_config.text["CODIFER_DECODE"][self.name]
        for key_element, value_element in sections.items():
            element = Element(
                name=elements[int(key_element)-1],
                correct=value_element[0],
                partial=value_element[1],
                total=value_element[2]
            )
            self.total += element.total
            self.correct += element.correct
            self.partial += element.partial
            self.elements.append(element)
        try:
            self.interest = (self.correct + self.partial/2) / self.total
        except ZeroDivisionError:
            self.interest = 0


class Statistic:
    interest: float
    correct: int
    total: int
    partial: int
    sections: List[Section]

    def __init__(self):
        self.correct = 0
        self.total = 0
        self.partial = 0
        self.sections = []

    async def form_statistic(self, statistic: dict):
        sections = list(f_config.text["CODIFER_DECODE"].keys())
        for key_section, value_section in statistic.items():
            section = Section(name=sections[int(key_section)-1])
            await section.form_sections(sections=value_section)
            self.total += section.total
            self.correct += section.correct
            self.partial += section.partial
            self.sections.append(section)
        try:
            self.interest = (self.correct + self.partial/2) / self.total
        except ZeroDivisionError:
            self.interest = 0

    async def print_statistic(self):
        for section in self.sections:
            print(f"SECTION: {section.name} CORRECT:{section.correct} PARTITIAL:{section.partial} TOTAL:{section.total} INTEREST:{section.interest}")
            for element in section.elements:
                print(f"\tELEMENT: {element.name} CORRECT:{element.correct} PARTITIAL:{element.partial} TOTAL:{element.total} INTEREST:{element.interest}")


async def form_statistic(user_id: int):
    async with async_session_maker() as session:
        query = select(Statistic_DB).where(Statistic_DB.telegram_id == user_id)
        stat = (await session.execute(query)).scalars().one()
    stat_obj = Statistic()
    await stat_obj.form_statistic(stat.summary)
    return stat_obj
