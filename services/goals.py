import ui

def build_goals_report(user_id: int) -> str:
    return ui.card("Финансовые цели", [
        "Пока целей нет.",
        "",
        "Создать цель: Цель Машина 100000000",
    ])

def create_goal_from_text(user_id: int, text: str) -> str:
    return ui.card("Цель", ["Функция создания цели сохранена в старой версии."])

def add_saving_from_text(user_id: int, text: str) -> str:
    return ui.card("Цель", ["Функция пополнения цели сохранена в старой версии."])

def delete_goal_from_text(user_id: int, text: str) -> str:
    return ui.card("Цель", ["Функция удаления цели сохранена в старой версии."])
