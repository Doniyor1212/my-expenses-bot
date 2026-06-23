from datetime import datetime
import ui
from database import get_expenses

try:
    from database import get_incomes
except Exception:
    get_incomes = None

def _amount(item):
    try:
        return int(item.get("amount", 0))
    except Exception:
        return 0

def _created_at(item):
    return str(item.get("created_at") or item.get("date") or "")

def _month():
    return datetime.now().strftime("%Y-%m")

def _filter_month(items):
    key = _month()
    result = []
    for item in items or []:
        created = _created_at(item)
        if not created or created.startswith(key):
            result.append(item)
    return result

def build_balance_report(user_id: int) -> str:
    expenses = _filter_month(get_expenses(user_id))
    incomes = _filter_month(get_incomes(user_id)) if get_incomes else []
    total_expenses = sum(_amount(x) for x in expenses)
    total_incomes = sum(_amount(x) for x in incomes)
    balance = total_incomes - total_expenses
    return ui.card("Баланс", [
        ui.row("Доходы", ui.money(total_incomes)),
        ui.row("Расходы", ui.money(total_expenses)),
        "",
        ui.row("Остаток", ui.money(balance)),
        ui.row("Статус", "Плюс" if balance >= 0 else "Минус"),
    ])

def build_history_report(user_id: int, limit: int = 10) -> str:
    expenses = get_expenses(user_id) or []
    if not expenses:
        return ui.empty("История", "Добавь операцию: кофе 25000")
    items = list(expenses)[-limit:][::-1]
    lines = []
    for item in items:
        lines.append(f"{ui.t(str(item.get('description', 'Без описания'))[:22])} — {ui.money(_amount(item))}")
    return ui.card("История", lines)
