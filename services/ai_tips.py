from .ai_utils import money, icon, OPTIMIZABLE_CATEGORIES, ESSENTIAL_CATEGORIES


def build_tips(rows):
    candidates = []

    total_current = sum(item["current_amount"] for item in rows)

    for item in rows:
        category = item["category"]

        if category in ESSENTIAL_CATEGORIES:
            continue

        if category not in OPTIMIZABLE_CATEGORIES:
            continue

        if item["current_amount"] <= 0:
            continue

        share = round(item["current_amount"] / total_current * 100) if total_current > 0 else 0
        economy_10 = round(item["current_amount"] * 0.1)
        economy_20 = round(item["current_amount"] * 0.2)

        candidates.append({
            "category": category,
            "share": share,
            "economy_10": economy_10,
            "economy_20": economy_20,
            "current_amount": item["current_amount"],
            "difference": item["difference"],
        })

    candidates.sort(key=lambda x: (x["current_amount"], x["difference"]), reverse=True)

    if not candidates:
        return (
            "💡 AI-рекомендации\n\n"
            "Сейчас нет явных категорий для оптимизации.\n\n"
            "Основные расходы выглядят обязательными."
        )

    text = "💡 AI-рекомендации\n\n"

    total_economy = 0

    for index, item in enumerate(candidates[:3], start=1):
        total_economy += item["economy_20"]

        text += f"{index}️⃣ {icon(item['category'])} {item['category']}\n"
        text += f"Доля в расходах: {item['share']}%\n"

        if item["category"] == "Покупки":
            text += (
                "Если часть покупок была необязательной, "
                "сокращение на 10–20% даст экономию:\n"
            )
        else:
            text += "Сокращение на 10–20% может дать экономию:\n"

        text += f"≈ {money(item['economy_10'])} – {money(item['economy_20'])}\n\n"

    text += f"Потенциальная экономия до: ≈ {money(total_economy)}"

    return text.strip()



def calculate_possible_economy(rows):
    total = 0

    for item in rows:
        category = item["category"]

        if category in ESSENTIAL_CATEGORIES:
            continue

        if category not in OPTIMIZABLE_CATEGORIES:
            continue

        if item["current_amount"] <= 0:
            continue

        total += round(item["current_amount"] * 0.2)

    return total
