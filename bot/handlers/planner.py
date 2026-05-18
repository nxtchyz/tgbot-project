from __future__ import annotations
import re
from datetime import date, datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from db import crud
from bot.keyboards.planner_kb import tasks_list_kb, task_actions_kb

router = Router()


class AddTask(StatesGroup):
    title = State()
    description = State()
    due_date = State()
    due_time = State()
    remind_min = State()


# ── /tasks — список дел ────────────────────────────────────────────────────────

@router.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    tasks = await crud.get_tasks(message.from_user.id)
    if not tasks:
        await message.answer("У тебя нет активных задач. Добавь первую командой /add")
        return
    await message.answer("Твои задачи:", reply_markup=tasks_list_kb(tasks))


# ── /add — добавить задачу (FSM) ───────────────────────────────────────────────

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    await state.set_state(AddTask.title)
    await message.answer("Как называется задача?")


@router.message(AddTask.title)
async def got_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AddTask.description)
    await message.answer("Краткое описание (или /skip чтобы пропустить):")


@router.message(AddTask.description)
async def got_description(message: Message, state: FSMContext) -> None:
    desc = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddTask.due_date)
    await message.answer("Дата дедлайна в формате ДД.ММ.ГГГГ (или /skip):")


@router.message(AddTask.due_date)
async def got_due_date(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == "/skip":
        await state.update_data(due_date=None)
    else:
        try:
            parsed = datetime.strptime(text, "%d.%m.%Y").date()
            await state.update_data(due_date=parsed.isoformat())
        except ValueError:
            await message.answer("Неверный формат. Попробуй ДД.ММ.ГГГГ или /skip:")
            return
    await state.set_state(AddTask.due_time)
    await message.answer("Время в формате ЧЧ:ММ (или /skip):")


@router.message(AddTask.due_time)
async def got_due_time(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == "/skip":
        await state.update_data(due_time=None)
    else:
        if not re.match(r"^\d{2}:\d{2}$", text):
            await message.answer("Неверный формат. Попробуй ЧЧ:ММ или /skip:")
            return
        await state.update_data(due_time=text)
    await state.set_state(AddTask.remind_min)
    await message.answer("За сколько минут напомнить? (по умолчанию 30, или /skip):")


@router.message(AddTask.remind_min)
async def got_remind_min(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    remind_min = 30
    if text != "/skip":
        if not text.isdigit():
            await message.answer("Введи число минут или /skip:")
            return
        remind_min = int(text)

    data = await state.get_data()
    await state.clear()

    task_id = await crud.add_task(
        user_id=message.from_user.id,
        title=data["title"],
        description=data.get("description"),
        due_date=data.get("due_date"),
        due_time=data.get("due_time"),
        remind_min=remind_min,
    )

    lines = [f"✅ Задача добавлена (#{task_id})", f"<b>{data['title']}</b>"]
    if data.get("description"):
        lines.append(data["description"])
    if data.get("due_date"):
        lines.append(f"📅 {data['due_date']}" + (f" в {data['due_time']}" if data.get("due_time") else ""))
    lines.append(f"🔔 Напомню за {remind_min} мин.")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ── /today — сводка на сегодня ─────────────────────────────────────────────────

@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    today = date.today().isoformat()
    tasks = await crud.get_todays_tasks(message.from_user.id, today)
    if not tasks:
        await message.answer("На сегодня задач нет. Отдыхай!")
        return
    lines = [f"<b>Задачи на сегодня ({today}):</b>"]
    for t in tasks:
        time_str = f" в {t['due_time']}" if t["due_time"] else ""
        lines.append(f"• {t['title']}{time_str}")
    await message.answer("\n".join(lines), parse_mode="HTML")


# ── Callback: просмотр задачи ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("task:"))
async def cb_view_task(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[1])
    task = await crud.get_task(task_id, callback.from_user.id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    lines = [f"<b>{task['title']}</b>"]
    if task["description"]:
        lines.append(task["description"])
    if task["due_date"]:
        lines.append(f"📅 {task['due_date']}" + (f" в {task['due_time']}" if task["due_time"] else ""))
    lines.append(f"🔔 Напоминание за {task['remind_min']} мин.")
    lines.append("✅ Выполнено" if task["done"] else "🕐 Активна")

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=task_actions_kb(task_id, bool(task["done"])),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("done:"))
async def cb_mark_done(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[1])
    await crud.mark_done(task_id, callback.from_user.id)
    await callback.answer("Отмечено как выполненное!")
    await callback.message.edit_reply_markup(
        reply_markup=task_actions_kb(task_id, done=True)
    )


@router.callback_query(F.data.startswith("delete:"))
async def cb_delete_task(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[1])
    await crud.delete_task(task_id, callback.from_user.id)
    await callback.answer("Задача удалена")
    await callback.message.edit_text("🗑 Задача удалена.")


@router.callback_query(F.data == "back:list")
async def cb_back_list(callback: CallbackQuery) -> None:
    tasks = await crud.get_tasks(callback.from_user.id)
    if not tasks:
        await callback.message.edit_text("Активных задач нет. Добавь командой /add")
    else:
        await callback.message.edit_text("Твои задачи:", reply_markup=tasks_list_kb(tasks))
    await callback.answer()
