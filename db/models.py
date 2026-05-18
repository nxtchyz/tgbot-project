import aiosqlite

DB_PATH = "planner.db"

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    title       TEXT    NOT NULL,
    description TEXT,
    due_date    TEXT,           -- ISO format: YYYY-MM-DD
    due_time    TEXT,           -- HH:MM
    remind_min  INTEGER DEFAULT 30,  -- remind N minutes before
    done        INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now'))
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TASKS_TABLE)
        await db.commit()
