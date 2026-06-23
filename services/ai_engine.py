from datetime import datetime

from .ai_utils import (
    MONTHS_RU,
    ESSENTIAL_CATEGORIES,
    OPTIMIZABLE_CATEGORIES,
    calculate_growth,
    group_by_category,
    icon,
    money,
    month_range,
    previous_month,
    get_expenses_between,
)
from .ai_forecast import build_month_forecast
from .ai_score import calculate_score, build_score_text
from .ai_anomaly import find_impulse_operations, build_anomaly_text
from .ai_tips import build_tips, calculate_possible_economy
from .ai_statistics import build_habits
from .goals import build_goals_ai_text
from .ai_budget import build_budget_ai_text


def generate_ai_expense_analysis(telegram_id: int) -> str:
    today = datetime.now()

    current_start, current_end = month_range(today.year, today.month)
    previous_year, previous_m = previous_month(today.year, today.month)
    previous_start, previous_end = month_range(previous_year, previous_m)

    current_expenses = get_expenses_between(telegram_id, current_start, current_end)
    previous_expenses = get_expenses_between(telegram_id, previous_start, previous_end)

    if not current_expenses:
        return (
            "🤖 AI-анализ расходов\n\n"
            "Пока недостаточно данных за текущий месяц.\n\n"
            "Добавьте несколько расходов, и я смогу показать анализ."
        )

    current_data = group_by_category(current_expenses)
    previous_data = group_by_category(previous_expenses)

    total_current = sum(current_data.values())
    total_previous = sum(previous_data.values())
    total_growth = calculate_growth(total_current, total_previous)

    rows = []
    all_categories = set(current_data.keys()) | set(previous_data.keys())

    for category in all_categories:
        current_amount = current_data.get(category, 0)
        previous_amount = previous_data.get(category, 0)
        difference = current_amount - previous_amount
        growth = calculate_growth(current_amount, previous_amount)

        rows.append({
            "category": category,
            "current_amount": current_amount,
            "previous_amount": previous_amount,
            "difference": difference,
            "growth": growth,
        })

    rows.sort(key=lambda x: (x["difference"], x["current_amount"]), reverse=True)

    optimizable_total = sum(
        item["current_amount"]
        for item in rows
        if item["category"] in OPTIMIZABLE_CATEGORIES
    )

    increased_count = len([x for x in rows if x["difference"] > 0])
    impulses = find_impulse_operations(current_expenses)

    score = calculate_score(
        total_growth=total_growth,
        increased_count=increased_count,
        impulse_count=len(impulses),
        optimizable_total=optimizable_total,
        total_current=total_current,
    )

    text = "🤖 AI-анализ расходов 3.4\n\n"
    text += f"📅 Период: {MONTHS_RU[today.month].capitalize()}\n"
    text += f"📊 Сравнение с месяцем: {MONTHS_RU[previous_m]}\n\n"
    text += f"💸 Расходы за месяц: {money(total_current)}\n"

    if total_previous > 0:
        sign = "+" if total_growth and total_growth > 0 else ""
        text += f"📈 Общее изменение: {sign}{total_growth}%\n\n"
    else:
        text += "📈 Прошлого месяца нет для сравнения.\n\n"

    text += "🏆 Категории\n\n"

    for item in rows[:7]:
        category = item["category"]
        growth = item["growth"]
        difference = item["difference"]

        text += f"{icon(category)} {category}\n"

        if category in ESSENTIAL_CATEGORIES:
            text += "Обязательные расходы\n"
        elif category in OPTIMIZABLE_CATEGORIES:
            text += "Есть потенциал экономии\n"
        else:
            text += "Нейтральная категория\n"

        if growth is None:
            text += f"🆕 Появилась впервые ({money(item['current_amount'])})\n\n"
        else:
            growth_sign = "+" if growth > 0 else ""
            diff_sign = "+" if difference > 0 else ""
            text += f"{growth_sign}{growth}% ({diff_sign}{money(difference)})\n\n"

    possible_economy = calculate_possible_economy(rows)

    text += "━━━━━━━━━━━━━━\n\n"
    text += build_tips(rows)

    forecast = build_month_forecast(total_current, today)
    if forecast:
        text += "\n\n━━━━━━━━━━━━━━\n\n"
        text += forecast

    budget_text = build_budget_ai_text(telegram_id, total_current)
    if budget_text:
        text += "\n\n━━━━━━━━━━━━━━\n\n"
        text += budget_text

    goals_text = build_goals_ai_text(telegram_id, possible_economy)
    if goals_text:
        text += "\n\n━━━━━━━━━━━━━━\n\n"
        text += goals_text

    anomaly_text = build_anomaly_text(impulses)
    if anomaly_text:
        text += "\n\n━━━━━━━━━━━━━━\n\n"
        text += anomaly_text

    habits = build_habits(current_expenses)
    if habits:
        text += "\n\n━━━━━━━━━━━━━━\n\n"
        text += habits

    text += "\n\n━━━━━━━━━━━━━━\n\n"
    text += build_score_text(score)

    return text.strip()
