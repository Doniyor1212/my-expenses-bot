from collections import defaultdict
from .ai_utils import parse_dt, money, icon, OPTIMIZABLE_CATEGORIES


MIN_OPERATIONS_FOR_HABITS = 10


def build_habits(expenses):
    useful_expenses = [
        item for item in expenses
        if item.get("category") in OPTIMIZABLE_CATEGORIES
    ]

    if len(useful_expenses) < MIN_OPERATIONS_FOR_HABITS:
        return (
            "📊 Финансовые привычки\n\n"
            "Пока недостаточно данных для анализа привычек.\n\n"
            f"Нужно минимум {MIN_OPERATIONS_FOR_HABITS} необязательных расходов.\n"
            f"Сейчас: {len(useful_expenses)}."
        )

    category_count = defaultdict(int)
    category_sum = defaultdict(int)
    weekday_sum = defaultdict(int)

    weekdays = {
        0: "понедельник",
        1: "вторник",
        2: "среда",
        3: "четверг",
        4: "пятница",
        5: "суббота",
        6: "воскресенье",
    }

    for item in useful_expenses:
        category = item["category"]
        category_count[category] += 1
        category_sum[category] += item["amount"]

        dt = parse_dt(item.get("created_at"))
        if dt:
            weekday_sum[dt.weekday()] += item["amount"]

    top_category = max(category_sum.items(), key=lambda x: x[1])
    top_count = category_count[top_category[0]]
    avg_check = round(top_category[1] / max(1, top_count))

    top_weekday = "не определен"
    if weekday_sum:
        top_weekday = weekdays[max(weekday_sum.items(), key=lambda x: x[1])[0]]

    return (
        "📊 Финансовые привычки\n\n"
        f"Чаще всего можно оптимизировать: {icon(top_category[0])} {top_category[0]}\n"
        f"Операций: {top_count}\n"
        f"Средний чек: {money(avg_check)}\n"
        f"День с самыми большими необязательными расходами: {top_weekday}"
    )
