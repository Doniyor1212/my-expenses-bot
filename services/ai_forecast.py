from datetime import datetime
from .ai_utils import money


def build_month_forecast(current_total: int, today: datetime):
    day = today.day

    if day <= 0:
        return None

    if today.month == 12:
        days_in_month = 31
    else:
        next_month = datetime(today.year, today.month + 1, 1)
        current_month = datetime(today.year, today.month, 1)
        days_in_month = (next_month - current_month).days

    forecast = round(current_total / day * days_in_month)

    return (
        "📈 Прогноз месяца\n\n"
        f"Если продолжить тратить в таком же темпе,\n"
        f"к концу месяца расходы могут составить:\n\n"
        f"≈ {money(forecast)}"
    )
