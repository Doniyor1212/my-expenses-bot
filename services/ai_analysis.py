from collections import defaultdict
from datetime import datetime
import ui
from database import get_expenses

def generate_ai_expense_analysis(user_id: int) -> str:
    expenses = get_expenses(user_id) or []
    if not expenses:
        return ui.card("AI-анализ", ["Пока недостаточно данных."])
    total = sum(int(x.get("amount", 0)) for x in expenses)
    count = len(expenses)
    stats = defaultdict(int)
    for item in expenses:
        stats[item.get("category", "Прочее")] += int(item.get("amount", 0))
    top_category, top_amount = sorted(stats.items(), key=lambda x: x[1], reverse=True)[0]
    share = round(top_amount / total * 100) if total else 0
    economy = round(top_amount * 0.2)
    day = max(datetime.now().day, 1)
    forecast = round(total / day * 31)
    score = 100
    if share >= 70:
        score -= 20
    elif share >= 50:
        score -= 12
    if count < 10:
        score -= 8
    score = max(35, min(100, score))
    return ui.card("AI-анализ", [
        ui.row("Период", datetime.now().strftime("%m.%Y")),
        ui.row("Расходы", ui.money(total)),
        ui.row("Операций", count),
        "",
        ui.row("Топ", top_category),
        ui.row("Доля", f"{share}%"),
        ui.row("Экономия", ui.money(economy)),
        ui.row("Прогноз", ui.money(forecast)),
        ui.row("Рейтинг", f"{score}/100"),
    ])
