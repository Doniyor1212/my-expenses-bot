import ui

def build_budget_report(user_id: int) -> str:
    return ui.card("Бюджет", [
        "На текущий месяц бюджет не установлен.",
        "",
        "Чтобы установить: Бюджет 6000000",
    ])

def set_budget_for_current_month(user_id: int, amount: int) -> str:
    return ui.card("Бюджет", [ui.row("Лимит", ui.money(amount)), "Бюджет установлен."])

def delete_budget_for_current_month(user_id: int) -> str:
    return ui.card("Бюджет", ["Бюджет удален."])
