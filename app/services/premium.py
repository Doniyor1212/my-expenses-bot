from app.repositories.premium import PremiumRepository


ZENMONEY_LIKE_FEATURES = [
    "мульти-счета и категории",
    "бюджеты по категориям",
    "финансовые цели",
    "AI-анализ и прогноз",
    "OCR чеков",
    "экспорт CSV/Excel",
    "Web-кабинет",
    "лимиты и уведомления",
]


class PremiumService:
    def __init__(self):
        self.repo = PremiumRepository()

    def build_plan_text(self, telegram_id: int) -> str:
        plan = self.repo.get_plan(telegram_id)
        features = "\n".join(f"✅ {x}" for x in ZENMONEY_LIKE_FEATURES)
        return f"💎 Premium\n\nТекущий тариф: {plan}\n\nВозможности:\n{features}\n\nДля оплаты подключите платежный провайдер в Web/API."
