from __future__ import annotations
import json
from app.core.cache import cache
from app.core.config import get_settings
from app.repositories.finance import FinanceRepository


def money(amount: int) -> str:
    return f"{int(amount):,}".replace(",", " ") + " сум"


class AIAdvisorService:
    def __init__(self, repo: FinanceRepository | None = None):
        self.repo = repo or FinanceRepository()

    def answer(self, telegram_id: int, question: str) -> str:
        key = f"ai:{telegram_id}:{question.lower().strip()}"
        cached = cache.get(key)
        if cached:
            return cached
        snapshot = self.repo.snapshot(telegram_id, months=6)
        answer = self._rule_based_answer(snapshot, question)
        llm_answer = self._try_llm(snapshot, question)
        if llm_answer:
            answer = llm_answer
        cache.set(key, answer)
        return answer

    def _rule_based_answer(self, s: dict, question: str) -> str:
        q = question.lower()
        income = s["income_total"]
        expense = s["expense_total"]
        balance = s["balance"]
        avg_income = income // 6 if income else 0
        avg_expense = expense // 6 if expense else 0
        top = s["top_categories"][:5]

        if not s["expenses"] and not s["incomes"]:
            return "🤖 AI-финсоветник\n\nПока мало данных. Добавьте доходы и расходы хотя бы за 2–3 недели, потом я смогу считать бюджет, цели и покупки."

        if "iphone" in q or "айфон" in q or "можно купить" in q or "купить" in q:
            price = self._extract_amount(q) or 12_000_000
            safe_limit = max(0, balance - avg_expense)
            decision = "можно рассмотреть покупку" if safe_limit >= price else "лучше пока не покупать"
            return (
                "🤖 AI-решение по покупке\n\n"
                f"Ориентир цены: {money(price)}\n"
                f"Доход за период: {money(income)}\n"
                f"Расход за период: {money(expense)}\n"
                f"Текущий остаток: {money(balance)}\n"
                f"Безопасный лимит на крупную покупку: {money(safe_limit)}\n\n"
                f"Вывод: **{decision}**.\n"
                "Правило: крупная покупка не должна съедать резерв на обязательные расходы и цели."
            )

        if "почему" in q or "больше" in q or "много" in q:
            lines = ["🤖 Почему расходы выросли", ""]
            if top:
                lines.append("Главные категории расходов:")
                for cat, amount in top:
                    lines.append(f"• {cat}: {money(amount)}")
                lines.append("")
            lines.append(f"Средний доход/мес: {money(avg_income)}")
            lines.append(f"Средний расход/мес: {money(avg_expense)}")
            if top:
                lines.append(f"Основная причина — высокая доля категории **{top[0][0]}**.")
            lines.append("Рекомендация: поставьте лимит на 2–3 необязательные категории и проверьте результат через неделю.")
            return "\n".join(lines)

        return (
            "🤖 AI-финсоветник\n\n"
            f"Доходы: {money(income)}\n"
            f"Расходы: {money(expense)}\n"
            f"Баланс: {money(balance)}\n\n"
            "Можете спросить: «Почему трачу больше?» или «Можно купить iPhone за 12 млн?»"
        )

    def _extract_amount(self, text: str) -> int | None:
        import re
        nums = re.findall(r"\d+[\d\s.,]*", text)
        if not nums:
            return None
        n = int(re.sub(r"\D", "", nums[0]))
        if "млн" in text or "миллион" in text:
            return n * 1_000_000 if n < 1000 else n
        if "тыс" in text and n < 1000:
            return n * 1000
        return n

    def _try_llm(self, snapshot: dict, question: str) -> str | None:
        settings = get_settings()
        if not settings.openai_api_key:
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            payload = {k: snapshot[k] for k in ["income_total", "expense_total", "balance", "top_categories", "goals", "budget"]}
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "Ты финансовый AI-советник MyCost. Отвечай кратко, по-русски, на основании данных. Не выдумывай операции."},
                    {"role": "user", "content": f"Вопрос: {question}\nФинансовые данные JSON: {json.dumps(payload, ensure_ascii=False)}"},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception:
            return None
