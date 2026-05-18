from __future__ import annotations
import aiosqlite
from db.models import DB_PATH


async def add_task(
    user_id: int,
    title: str,
    description: str | None,
    due_date: str | None,
    due_time: str | None,
    remind_min: int = 30,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO tasks (user_id, title, description, due_date, due_time, remind_min)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, due_date, due_time, remind_min),
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
