from collections import defaultdict
import ui
from database import get_expenses

def build_statistics_report(user_id: int):
    expenses = get_expenses(user_id)
    if not expenses:
        return ui.empty("Статистика", "Добавь первую операцию: кофе 25000")
    stats = defaultdict(int)
    total = 0
    for item in expenses:
        category = item.get("category", "Прочее")
        amount = int(item.get("amount", 0))
        stats[category] += amount
        total += amount
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    top_expense = max(expenses, key=lambda x: int(x.get("amount", 0)))
    lines = [ui.row("Всего", ui.money(total)), ui.row("Категорий", len(sorted_stats)), ""]
    for category, amount in sorted_stats:
        percent = round(amount / total * 100) if total else 0
        lines.append(f"<b>{ui.t(category)}</b> — {percent}% · {ui.money(amount)}")
    lines += ["", "<b>Крупный чек</b>", ui.t(top_expense.get("description", "Без описания")), ui.money(int(top_expense.get("amount", 0)))]
    return ui.card("Статистика", lines)
