from dataclasses import dataclass


@dataclass
class Operation:
    id: int | None
    telegram_id: int
    type: str
    category: str
    description: str
    amount: int
    created_at: str | None = None


@dataclass
class FinancialSnapshot:
    income_total: int
    expense_total: int
    balance: int
    top_categories: list[tuple[str, int]]
    goals: list[dict]
    budget: dict | None
