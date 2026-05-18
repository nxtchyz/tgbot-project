from __future__ import annotations
from datetime import date, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from db import crud


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


def setup_scheduler(bot: Bot) -> None:
    scheduler.add_job(
        send_morning_summary,
        trigger="cron",
        hour=9,
        minute=0,
        args=[bot],
        id="morning_summary",
        replace_existing=True,
    )
    scheduler.add_job(
        check_upcoming_reminders,
        trigger="interval",
        minutes=1,
        args=[bot],
        id="upcoming_reminders",
        replace_existing=True,
    )
    scheduler.start()


async def send_morning_summary(bot: Bot) -> None:
    """Sends today's tasks to every user who has tasks today."""
    today = date.today().isoformat()
    # We get all undone tasks for today grouped by user
    async with __import__("aiosqlite").connect(crud.DB_PATH) as db:
        db.row_factory = __import__("aiosqlite").Row
        async with db.execute(
            "SELECT DISTINCT user_id FROM tasks WHERE due_date = ? AND done = 0", (today,)
        ) as cursor:
            user_ids = [row[0] for row in await cursor.fetchall()]

    for user_id in user_ids:
        tasks = await crud.get_todays_tasks(user_id, today)
        if not tasks:
            continue
        lines = [f"<b>Доброе утро! Задачи на сегодня:</b>"]
        for t in tasks:
            time_str = f" в {t['due_time']}" if t["due_time"] else ""
            lines.append(f"• {t['title']}{time_str}")
        try:
            await bot.send_message(user_id, "\n".join(lines), parse_mode="HTML")
        except Exception:
            pass


async def check_upcoming_reminders(bot: Bot) -> None:
    """Every minute checks if any task needs a reminder right now."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    async with __import__("aiosqlite").connect(crud.DB_PATH) as db:
        db.row_factory = __import__("aiosqlite").Row
        async with db.execute(
            "SELECT * FROM tasks WHERE due_date = ? AND due_time IS NOT NULL AND done = 0",
            (today,),
        ) as cursor:
            tasks = [dict(r) for r in await cursor.fetchall()]

    for task in tasks:
        try:
            task_dt = datetime.strptime(f"{task['due_date']} {task['due_time']}", "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        remind_at = task_dt - timedelta(minutes=task["remind_min"])
        # Fire if current minute matches reminder minute
        if remind_at.strftime("%Y-%m-%d %H:%M") == now.strftime("%Y-%m-%d %H:%M"):
            text = (
                f"🔔 <b>Напоминание!</b>\n"
                f"Через {task['remind_min']} мин: <b>{task['title']}</b>\n"
                f"⏰ {task['due_time']}"
            )
            try:
                await bot.send_message(task["user_id"], text, parse_mode="HTML")
            except Exception:
                pass
