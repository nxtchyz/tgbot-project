import aiosqlite

DB_PATH = "planner.db"

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    first_seen  TEXT DEFAULT (datetime('now')),
    last_seen   TEXT DEFAULT (datetime('now'))
);
"""

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    title         TEXT    NOT NULL,
    description   TEXT,
    due_date      TEXT,
    due_time      TEXT,
    remind_min    INTEGER DEFAULT 30,
    repeat_remind INTEGER DEFAULT 0,
    done          INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now'))
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_USERS_TABLE)
        await db.execute(CREATE_TASKS_TABLE)
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN repeat_remind INTEGER DEFAULT 0")
        except Exception:
            pass  # колонка уже существует
        await db.commit()
