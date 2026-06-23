from datetime import datetime
from app.db.connection import db_connection


class PremiumRepository:
    def get_plan(self, telegram_id: int) -> str:
        with db_connection() as conn:
            row = conn.execute("SELECT premium_plan, premium_until FROM user_profiles WHERE telegram_id=?", (telegram_id,)).fetchone()
        if not row:
            return "free"
        if row["premium_until"] and row["premium_until"] < datetime.now().isoformat():
            return "free"
        return row["premium_plan"] or "free"

    def upsert_profile(self, telegram_id: int, full_name: str | None = None, plan: str = "free") -> None:
        now = datetime.now().isoformat()
        with db_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_profiles(telegram_id, full_name, premium_plan, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET full_name=excluded.full_name, updated_at=excluded.updated_at
                """,
                (telegram_id, full_name, plan, now, now),
            )
