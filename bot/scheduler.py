from __future__ import annotations
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from db import crud

MOSCOW = ZoneInfo("Europe/Moscow")

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


def moscow_now() -> datetime:
    return datetime.now(MOSCOW).replace(tzinfo=None)


def moscow_today() -> str:
    return datetime.now(MOSCOW).strftime("%Y-%m-%d")


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
    scheduler.add_job(
        check_repeat_reminders,
        trigger="interval",
        minutes=1,
        args=[bot],
        id="repeat_reminders",
        replace_existing=True,
    )
    scheduler.start()


async def send_morning_summary(bot: Bot) -> None:
    today = moscow_today()
    import aiosqlite
    async with aiosqlite.connect(crud.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT DISTINCT user_id FROM tasks WHERE due_date = ? AND done = 0", (today,)
        ) as cursor:
            user_ids = [row[0] for row in await cursor.fetchall()]

    for user_id in user_ids:
        tasks = await crud.get_todays_tasks(user_id, today)
        if not tasks:
            continue
        lines = ["<b>Доброе утро! Задачи на сегодня:</b>"]
        for t in tasks:
            time_str = f" в {t['due_time']}" if t["due_time"] else ""
            lines.append(f"• {t['title']}{time_str}")
        try:
            await bot.send_message(user_id, "\n".join(lines), parse_mode="HTML")
        except Exception:
            pass


async def check_upcoming_reminders(bot: Bot) -> None:
    now = moscow_now()
    today = now.strftime("%Y-%m-%d")

    import aiosqlite
    async with aiosqlite.connect(crud.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tasks WHERE due_date = ? AND due_time IS NOT NULL AND done = 0",
            (today,),
        ) as cursor:
            tasks = [dict(r) for r in await cursor.fetchall()]

    for task in tasks:
        try:
            task_dt = datetime.strptime(
                f"{task['due_date']} {task['due_time']}", "%Y-%m-%d %H:%M"
            )
        except ValueError:
            continue

        # Уведомление в момент дедлайна
        if abs((task_dt - now).total_seconds()) <= 59:
            text = (
                f"⏰ <b>Время пришло!</b>\n"
                f"<b>{task['title']}</b>"
            )
            try:
                await bot.send_message(task["user_id"], text, parse_mode="HTML")
            except Exception:
                pass
            continue

        # Уведомление за remind_min минут до дедлайна (только для обычных задач)
        if task["repeat_remind"]:
            continue

        remind_at = task_dt - timedelta(minutes=task["remind_min"])
        diff = abs((remind_at - now).total_seconds())

        if diff <= 59:
            text = (
                f"🔔 <b>Напоминание!</b>\n"
                f"Через {task['remind_min']} мин: <b>{task['title']}</b>\n"
                f"⏰ {task['due_time']}"
            )
            try:
                await bot.send_message(task["user_id"], text, parse_mode="HTML")
            except Exception:
                pass


async def check_repeat_reminders(bot: Bot) -> None:
    now = moscow_now()
    tasks = await crud.get_repeat_remind_tasks()

    for task in tasks:
        try:
            task_dt = datetime.strptime(
                f"{task['due_date']} {task['due_time']}", "%Y-%m-%d %H:%M"
            )
        except ValueError:
            continue

        remind_start = task_dt - timedelta(minutes=task["remind_min"])
        if now < remind_start:
            continue

        # Не дублируем уведомление в момент дедлайна (оно в check_upcoming_reminders)
        if abs((task_dt - now).total_seconds()) <= 59:
            continue

        elapsed = (now - remind_start).total_seconds()
        interval = task["remind_min"] * 60
        if elapsed % interval > 59:
            continue

        text = (
            f"🔁 <b>Напоминание!</b>\n"
            f"<b>{task['title']}</b>\n"
            f"⏰ Дедлайн: {task['due_date']} {task['due_time']}"
        )
        try:
            await bot.send_message(task["user_id"], text, parse_mode="HTML")
        except Exception:
            pass
