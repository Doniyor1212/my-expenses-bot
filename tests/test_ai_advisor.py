from app.services.ai_advisor import AIAdvisorService


class Repo:
    def snapshot(self, telegram_id, months=6):
        return {"income_total": 20_000_000, "expense_total": 8_000_000, "balance": 12_000_000, "top_categories": [("Кафе", 2_000_000)], "expenses": [{"amount": 1}], "incomes": [{"amount": 1}], "goals": [], "budget": None}


def test_ai_purchase_answer():
    text = AIAdvisorService(Repo()).answer(1, "Можно купить iPhone за 10 млн?")
    assert "AI-решение" in text
    assert "10 000 000" in text
