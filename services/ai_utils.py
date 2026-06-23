import sqlite3
from datetime import datetime, timedelta
from database import get_connection


MONTHS_RU = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}


CATEGORY_ICONS = {
    "Продукты": "🍞",
    "Напитки": "🥤",
    "Кафе": "🍔",
    "Транспорт": "🚕",
    "Покупки": "🛍",
    "Здоровье": "💊",
    "Дом": "🏠",
    "Коммунальные": "💡",
    "Одежда": "👕",
    "Развлечения": "🎮",
    "Переводы": "🔁",
    "Доход": "💰",
    "Прочее": "📦",
}


ESSENTIAL_CATEGORIES = {
    "Дом",
    "Коммунальные",
    "Здоровье",
    "Переводы",
}


OPTIMIZABLE_CATEGORIES = {
    "Кафе",
    "Развлечения",
    "Покупки",
    "Напитки",
    "Транспорт",
    "Одежда",
    "Прочее",
}


def money(amount: int) -> str:
    return f"{int(amount):,}".replace(",", " ") + " сум"


def icon(category: str) -> str:
    return CATEGORY_ICONS.get(category, "📂")


def parse_dt(value: str):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def month_range(year: int, month: int):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


def previous_month(year: int, month: int):
    if month == 1:
        return year - 1, 12
    return year, month - 1


def calculate_growth(current: int, previous: int):
    if previous == 0 and current > 0:
        return None
    if previous == 0:
        return 0
    return round(((current - previous) / previous) * 100)


def get_expenses_between(telegram_id: int, start: datetime, end: datetime):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM expenses
        WHERE telegram_id = ?
          AND created_at >= ?
          AND created_at < ?
        ORDER BY created_at ASC
        """,
        (telegram_id, start.isoformat(), end.isoformat())
    )

    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_incomes_between(telegram_id: int, start: datetime, end: datetime):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM incomes
        WHERE telegram_id = ?
          AND created_at >= ?
          AND created_at < ?
        ORDER BY created_at ASC
        """,
        (telegram_id, start.isoformat(), end.isoformat())
    )

    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def group_by_category(expenses: list):
    result = {}
    for item in expenses:
        result[item["category"]] = result.get(item["category"], 0) + item["amount"]
    return result


def progress_bar(score: float, max_score: float = 10, size: int = 10):
    filled = round(score / max_score * size)
    filled = max(0, min(size, filled))
    return "█" * filled + "░" * (size - filled)
