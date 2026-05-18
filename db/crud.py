from __future__ import annotations
import aiosqlite
from db.models import DB_PATH


async def upsert_user(user_id: int, username: str | None, first_name: str | None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_seen)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_seen  = datetime('now')
            """,
            (user_id, username, first_name),
        )
        await db.commit()


async def add_task(
    user_id: int,
    title: str,
    description: str | None,
    due_date: str | None,
    due_time: str | None,
    remind_min: int = 30,
    repeat_remind: bool = False,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO tasks (user_id, title, description, due_date, due_time, remind_min, repeat_remind)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, due_date, due_time, remind_min, int(repeat_remind)),
        )
        await db.commit()
        return cursor.lastrowid


async def get_tasks(user_id: int, only_undone: bool = True) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        where = "WHERE user_id = ?" + (" AND done = 0" if only_undone else "")
        async with db.execute(
            f"SELECT * FROM tasks {where} ORDER BY due_date, due_time", (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_task(task_id: int, user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def mark_done(task_id: int, user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        await db.commit()


async def delete_task(task_id: int, user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        )
        await db.commit()


async def get_tasks_for_reminder(due_date: str, due_time: str) -> list[dict]:
    """Return undone tasks matching exact date+time for scheduler."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM tasks
            WHERE due_date = ? AND due_time = ? AND done = 0
            """,
            (due_date, due_time),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_todays_tasks(user_id: int, today: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM tasks
            WHERE user_id = ? AND due_date = ? AND done = 0
            ORDER BY due_time
            """,
            (user_id, today),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_repeat_remind_tasks() -> list[dict]:
    """Return undone tasks with repeat_remind=1 that have due_date and due_time."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM tasks
            WHERE repeat_remind = 1 AND done = 0
              AND due_date IS NOT NULL AND due_time IS NOT NULL
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
