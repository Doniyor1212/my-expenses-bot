from collections import defaultdict
from datetime import datetime, timedelta
from app.db.connection import db_connection


class FinanceRepository:
    def add_operation(self, telegram_id: int, operation_type: str, category: str, description: str, amount: int) -> int:
        table = "incomes" if operation_type == "income" else "expenses"
        with db_connection() as conn:
            cur = conn.execute(
                f"INSERT INTO {table}(telegram_id, category, description, amount, created_at) VALUES(?, ?, ?, ?, ?)",
                (telegram_id, category, description, int(amount), datetime.now().isoformat()),
            )
            return int(cur.lastrowid)

    def operations_between(self, telegram_id: int, months: int = 6) -> dict[str, list[dict]]:
        start = datetime.now() - timedelta(days=31 * months)
        result = {"expenses": [], "incomes": []}
        with db_connection() as conn:
            for table in result:
                rows = conn.execute(
                    f"SELECT * FROM {table} WHERE telegram_id=? AND created_at>=? ORDER BY created_at ASC",
                    (telegram_id, start.isoformat()),
                ).fetchall()
                result[table] = [dict(row) for row in rows]
        return result

    def snapshot(self, telegram_id: int, months: int = 6) -> dict:
        data = self.operations_between(telegram_id, months)
        expense_total = sum(x["amount"] for x in data["expenses"])
        income_total = sum(x["amount"] for x in data["incomes"])
        cats = defaultdict(int)
        for item in data["expenses"]:
            cats[item["category"]] += item["amount"]
        with db_connection() as conn:
            goals = [dict(row) for row in conn.execute("SELECT * FROM goals WHERE telegram_id=? ORDER BY is_completed, created_at DESC", (telegram_id,)).fetchall()]
            budget = conn.execute("SELECT * FROM budgets WHERE telegram_id=? ORDER BY month DESC LIMIT 1", (telegram_id,)).fetchone()
        return {
            "income_total": income_total,
            "expense_total": expense_total,
            "balance": income_total - expense_total,
            "top_categories": sorted(cats.items(), key=lambda x: x[1], reverse=True)[:10],
            "expenses": data["expenses"],
            "incomes": data["incomes"],
            "goals": goals,
            "budget": dict(budget) if budget else None,
        }
