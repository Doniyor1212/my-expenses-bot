from datetime import datetime
from pathlib import Path
from app.db.connection import db_connection


def run_migrations() -> None:
    migrations_dir = Path(__file__).parent / "migrations"
    with db_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
        for file in sorted(migrations_dir.glob("*.sql")):
            version = file.stem
            if version in applied:
                continue
            conn.executescript(file.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations(version, applied_at) VALUES(?, ?)", (version, datetime.now().isoformat()))
