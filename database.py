import os
import sqlite3
from datetime import datetime

DB_NAME = "data/expenses.db"


def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        category TEXT,
        description TEXT,
        amount INTEGER,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS incomes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        category TEXT,
        description TEXT,
        amount INTEGER,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS budgets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        month TEXT,
        limit_amount INTEGER,
        created_at TEXT,
        updated_at TEXT,
        UNIQUE(telegram_id, month)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS goals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        title TEXT,
        target_amount INTEGER,
        saved_amount INTEGER DEFAULT 0,
        is_completed INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_expense(telegram_id, category, description, amount):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO expenses
    (telegram_id, category, description, amount, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (telegram_id, category, description, amount, datetime.now().isoformat()))

    operation_id = cur.lastrowid

    conn.commit()
    conn.close()

    return operation_id


def add_income(telegram_id, category, description, amount):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO incomes
    (telegram_id, category, description, amount, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (telegram_id, category, description, amount, datetime.now().isoformat()))

    operation_id = cur.lastrowid

    conn.commit()
    conn.close()

    return operation_id


def get_expenses(telegram_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM expenses
    WHERE telegram_id = ?
    ORDER BY created_at DESC
    """, (telegram_id,))

    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_incomes(telegram_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM incomes
    WHERE telegram_id = ?
    ORDER BY created_at DESC
    """, (telegram_id,))

    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_last_operation(telegram_id):
    operations = []

    for item in get_expenses(telegram_id):
        item["table"] = "expenses"
        item["type"] = "expense"
        operations.append(item)

    for item in get_incomes(telegram_id):
        item["table"] = "incomes"
        item["type"] = "income"
        operations.append(item)

    if not operations:
        return None

    operations.sort(key=lambda x: x["created_at"], reverse=True)
    return operations[0]


def get_operation_by_id(table, operation_id, telegram_id):
    if table not in ["expenses", "incomes"]:
        return None

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT * FROM {table}
        WHERE id = ? AND telegram_id = ?
        """,
        (operation_id, telegram_id)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    item = dict(row)
    item["table"] = table
    item["type"] = "income" if table == "incomes" else "expense"

    return item


def delete_operation_by_id(table, operation_id, telegram_id):
    item = get_operation_by_id(table, operation_id, telegram_id)

    if not item:
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        f"DELETE FROM {table} WHERE id = ? AND telegram_id = ?",
        (operation_id, telegram_id)
    )

    conn.commit()
    conn.close()

    return item


def duplicate_operation_by_id(table, operation_id, telegram_id):
    item = get_operation_by_id(table, operation_id, telegram_id)

    if not item:
        return None

    if table == "expenses":
        new_id = add_expense(
            telegram_id,
            item["category"],
            item["description"],
            item["amount"]
        )
    else:
        new_id = add_income(
            telegram_id,
            item["category"],
            item["description"],
            item["amount"]
        )

    return get_operation_by_id(table, new_id, telegram_id)


def delete_last_operation(telegram_id):
    last = get_last_operation(telegram_id)

    if not last:
        return None

    return delete_operation_by_id(last["table"], last["id"], telegram_id)


def clear_all_operations(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM expenses WHERE telegram_id = ?", (telegram_id,))
    cur.execute("DELETE FROM incomes WHERE telegram_id = ?", (telegram_id,))

    conn.commit()
    conn.close()

    return True


def update_operation(table, operation_id, telegram_id, category, description, amount):
    if table not in ["expenses", "incomes"]:
        return False

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        f"""
        UPDATE {table}
        SET category = ?, description = ?, amount = ?
        WHERE id = ? AND telegram_id = ?
        """,
        (category, description, amount, operation_id, telegram_id)
    )

    conn.commit()
    conn.close()

    return True


def set_month_budget(telegram_id: int, month: str, limit_amount: int):
    conn = get_connection()
    cur = conn.cursor()

    now = datetime.now().isoformat()

    cur.execute(
        """
        INSERT INTO budgets (telegram_id, month, limit_amount, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id, month)
        DO UPDATE SET
            limit_amount = excluded.limit_amount,
            updated_at = excluded.updated_at
        """,
        (telegram_id, month, limit_amount, now, now)
    )

    conn.commit()
    conn.close()

    return True


def get_month_budget(telegram_id: int, month: str):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM budgets
        WHERE telegram_id = ? AND month = ?
        """,
        (telegram_id, month)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def delete_month_budget(telegram_id: int, month: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM budgets
        WHERE telegram_id = ? AND month = ?
        """,
        (telegram_id, month)
    )

    conn.commit()
    conn.close()

    return True



def create_goal(telegram_id: int, title: str, target_amount: int):
    conn = get_connection()
    cur = conn.cursor()

    now = datetime.now().isoformat()

    cur.execute(
        """
        INSERT INTO goals
        (telegram_id, title, target_amount, saved_amount, is_completed, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (telegram_id, title, target_amount, 0, 0, now, now)
    )

    goal_id = cur.lastrowid

    conn.commit()
    conn.close()

    return goal_id


def get_goals(telegram_id: int, include_completed: bool = True):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if include_completed:
        cur.execute(
            """
            SELECT *
            FROM goals
            WHERE telegram_id = ?
            ORDER BY is_completed ASC, created_at DESC
            """,
            (telegram_id,)
        )
    else:
        cur.execute(
            """
            SELECT *
            FROM goals
            WHERE telegram_id = ? AND is_completed = 0
            ORDER BY created_at DESC
            """,
            (telegram_id,)
        )

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_goal_by_id(telegram_id: int, goal_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM goals
        WHERE telegram_id = ? AND id = ?
        """,
        (telegram_id, goal_id)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def find_goal_by_title(telegram_id: int, title: str):
    title = title.strip().lower()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM goals
        WHERE telegram_id = ?
        ORDER BY created_at DESC
        """,
        (telegram_id,)
    )

    rows = cur.fetchall()
    conn.close()

    for row in rows:
        item = dict(row)
        if item["title"].strip().lower() == title:
            return item

    for row in rows:
        item = dict(row)
        if title in item["title"].strip().lower():
            return item

    return None


def add_goal_saving(telegram_id: int, goal_id: int, amount: int):
    goal = get_goal_by_id(telegram_id, goal_id)

    if not goal:
        return None

    new_saved = goal["saved_amount"] + amount
    is_completed = 1 if new_saved >= goal["target_amount"] else 0

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE goals
        SET saved_amount = ?, is_completed = ?, updated_at = ?
        WHERE telegram_id = ? AND id = ?
        """,
        (new_saved, is_completed, datetime.now().isoformat(), telegram_id, goal_id)
    )

    conn.commit()
    conn.close()

    return get_goal_by_id(telegram_id, goal_id)


def delete_goal(telegram_id: int, goal_id: int):
    goal = get_goal_by_id(telegram_id, goal_id)

    if not goal:
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM goals
        WHERE telegram_id = ? AND id = ?
        """,
        (telegram_id, goal_id)
    )

    conn.commit()
    conn.close()

    return goal
