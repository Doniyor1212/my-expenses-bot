from .ai_utils import parse_dt, money, OPTIMIZABLE_CATEGORIES


MAX_SINGLE_IMPULSE_AMOUNT = 300_000
MIN_TOTAL_IMPULSE_AMOUNT = 150_000
MAX_WINDOW_MINUTES = 30
MIN_OPERATIONS_COUNT = 3


def find_impulse_operations(expenses):
    """
    Ищем возможные импульсивные расходы.

    Логика:
    - только необязательные категории;
    - не берем крупные разовые покупки;
    - берем минимум 3 операции за короткое время;
    - общая сумма должна быть значимой.
    """
    filtered_items = []

    for item in expenses:
        category = item.get("category")
        amount = item.get("amount", 0)
        dt = parse_dt(item.get("created_at"))

        if not dt:
            continue

        if category not in OPTIMIZABLE_CATEGORIES:
            continue

        if amount > MAX_SINGLE_IMPULSE_AMOUNT:
            continue

        copied = dict(item)
        copied["_dt"] = dt
        filtered_items.append(copied)

    filtered_items.sort(key=lambda x: x["_dt"])

    result = []

    for i in range(len(filtered_items)):
        pack = [filtered_items[i]]

        for j in range(i + 1, len(filtered_items)):
            minutes = (filtered_items[j]["_dt"] - filtered_items[i]["_dt"]).total_seconds() / 60

            if minutes <= MAX_WINDOW_MINUTES:
                pack.append(filtered_items[j])
            else:
                break

        if len(pack) >= MIN_OPERATIONS_COUNT:
            total = sum(x["amount"] for x in pack)

            if total >= MIN_TOTAL_IMPULSE_AMOUNT:
                result.append({
                    "count": len(pack),
                    "minutes": max(1, round((pack[-1]["_dt"] - pack[0]["_dt"]).total_seconds() / 60)),
                    "total": total,
                    "categories": list({x["category"] for x in pack}),
                })

    return result[:3]


def build_anomaly_text(impulses):
    if not impulses:
        return None

    item = impulses[0]
    cats = ", ".join(item["categories"])

    return (
        "⚠️ Возможные импульсивные расходы\n\n"
        f"{item['count']} операции за {item['minutes']} минут.\n"
        f"Сумма: {money(item['total'])}\n"
        f"Категории: {cats}\n\n"
        "Это не ошибка, но такие траты лучше проверять."
    )
