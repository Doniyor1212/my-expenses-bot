from datetime import datetime, timedelta

from database import get_expenses, get_incomes


def money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " сум"


def parse_date(value: str):
    return datetime.fromisoformat(value).date()


def filter_by_period(items, start_date, end_date):
    return [
        item for item in items
        if start_date <= parse_date(item["created_at"]) <= end_date
    ]


def build_period_report(telegram_id: int, period: str) -> str:
    today = datetime.now().date()

    if period == "today":
        start_date = today
        end_date = today
        title = "Сегодня"

    elif period == "yesterday":
        start_date = today - timedelta(days=1)
        end_date = start_date
        title = "Вчера"

    elif period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
        title = "Эта неделя"

    elif period == "month":
        start_date = today.replace(day=1)
        end_date = today
        title = "Этот месяц"

    else:
        return "Неизвестный период."

    expenses = filter_by_period(get_expenses(telegram_id), start_date, end_date)
    incomes = filter_by_period(get_incomes(telegram_id), start_date, end_date)

    total_expenses = sum(item["amount"] for item in expenses)
    total_incomes = sum(item["amount"] for item in incomes)
    balance = total_incomes - total_expenses

    text = (
        f"📅 Отчет: {title}\n\n"
        f"💰 Доходы: {money(total_incomes)}\n"
        f"💸 Расходы: {money(total_expenses)}\n"
        f"💼 Баланс: {money(balance)}\n\n"
        f"🧾 Операций: {len(expenses) + len(incomes)}"
    )

    if expenses:
        categories = {}

        for item in expenses:
            categories[item["category"]] = categories.get(item["category"], 0) + item["amount"]

        text += "\n\n🏆 Расходы по категориям"

        for category, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            text += f"\n📂 {category}: {money(amount)}"

    return text