from models import Question
from enum import Enum


class CHECK(Enum):
    CORRECT_2 = 3
    CORRECT_1 = 2
    PARTLY = 1
    INCORRECT = 0


async def answer_check(answer_user: str, question: Question) -> CHECK:
    answer_question = str(question.answer_user)
    len_answer_question = len(answer_question)
    len_answer_user = len(answer_user)
    discrepancy = abs(len_answer_question - len_answer_user)
    correct = CHECK.CORRECT_2
    incorrect = CHECK.INCORRECT
    partly = CHECK.PARTLY
    if question.type in [1, 3, 9, 12]:
        correct = CHECK.CORRECT_1
        partly = CHECK.INCORRECT
    if 0 <= discrepancy <= 1:
        for i in range(0, len_answer_question):
            res = answer_user.find(answer_question[i])
            if res != -1:
                answer_user = answer_user[:res] + answer_user[res+1:]
        temp = len(answer_user)
        if len_answer_question > len_answer_user:
            if temp == 0:
                return partly
            return incorrect
        elif len_answer_question < len_answer_user:
            if temp <= 1:
                return partly
            return incorrect
        else:
            if temp == 0:
                return correct
            elif temp <= 1:
                if len_answer_user != 1:
                    return partly
            return incorrect
    return incorrect
