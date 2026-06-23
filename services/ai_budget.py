from datetime import datetime
from database import get_month_budget
from .ai_utils import money, progress_bar


def current_month_key():
    now = datetime.now()
    return f"{now.year}-{now.month:02d}"


def build_budget_ai_text(telegram_id: int, total_current: int):
    month = current_month_key()
    budget = get_month_budget(telegram_id, month)

    if not budget:
        return (
            "💰 Бюджет\n\n"
            "Бюджет на месяц не установлен.\n"
            "Чтобы включить контроль бюджета, напишите:\n\n"
            "Бюджет 6000000"
        )

    limit_amount = budget["limit_amount"]
    left = limit_amount - total_current
    percent = round(total_current / limit_amount * 100) if limit_amount > 0 else 0
    percent_for_bar = min(percent, 100)

    now = datetime.now()

    if now.month == 12:
        days_in_month = 31
    else:
        next_month = datetime(now.year, now.month + 1, 1)
        current_month = datetime(now.year, now.month, 1)
        days_in_month = (next_month - current_month).days

    days_left = max(0, days_in_month - now.day)

    text = "💰 Бюджет\n\n"
    text += f"Лимит: {money(limit_amount)}\n"
    text += f"Потрачено: {money(total_current)}\n"
    text += f"{progress_bar(percent_for_bar, max_score=100)} {percent}%\n\n"

    if left >= 0:
        text += f"Осталось: {money(left)}\n"

        if days_left > 0:
            daily_limit = round(left / days_left)
            text += f"До конца месяца: {days_left} дней\n"
            text += f"Рекомендуемый лимит в день: {money(daily_limit)}"
    else:
        text += f"Превышение: {money(abs(left))}\n"
        text += "Рекомендуется ограничить необязательные расходы."

    return text
