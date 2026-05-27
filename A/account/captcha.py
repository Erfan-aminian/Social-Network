import random
from uuid import uuid4


LOGIN_CAPTCHA_SESSION_KEY = "login_captcha_payload"
QUESTION_TYPE_SUM = "sum"
QUESTION_TYPE_MIN = "min"
QUESTION_TYPES = (QUESTION_TYPE_SUM, QUESTION_TYPE_MIN)


def build_login_captcha():
    first_number = random.randint(0, 10)
    second_number = random.randint(0, 10)
    question_type = random.choice(QUESTION_TYPES)

    if question_type == QUESTION_TYPE_SUM:
        answer = first_number + second_number
    else:
        answer = min(first_number, second_number)

    display_items = _build_display_items(first_number, second_number)
    return {
        "token": uuid4().hex,
        "question_type": question_type,
        "first_number": first_number,
        "second_number": second_number,
        "answer": answer,
        "display_items": display_items,
    }


def get_question_text(question_type):
    if question_type == QUESTION_TYPE_SUM:
        return "جمع دو عدد رنگی چند می‌شود؟"
    return "عدد کوچک‌تر بین دو عدد رنگی کدام است؟"


def validate_login_captcha(captcha_payload, submitted_token, submitted_answer):
    if not captcha_payload:
        return False, "کپچا معتبر نیست. دوباره تلاش کن."

    if submitted_token != captcha_payload.get("token"):
        return False, "کپچا منقضی شده است. دوباره تلاش کن."

    try:
        expected_answer = int(captcha_payload.get("answer"))
        typed_answer = int(submitted_answer)
    except (TypeError, ValueError):
        return False, "پاسخ کپچا معتبر نیست."

    if typed_answer != expected_answer:
        return False, "پاسخ کپچا اشتباه است."

    return True, ""


def _build_display_items(first_number, second_number):
    primary_items = [
        {"value": first_number, "is_primary": True},
        {"value": second_number, "is_primary": True},
    ]
    decoy_items = [{"value": random.randint(0, 10), "is_primary": False} for _ in range(2)]
    items = primary_items + decoy_items
    random.shuffle(items)
    return items
