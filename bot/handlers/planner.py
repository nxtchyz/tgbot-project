from __future__ import annotations
import re
from datetime import date, datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from db import crud
from bot.keyboards.planner_kb import (
    tasks_list_kb,
    task_actions_kb,
    skip_kb,
    remind_type_kb,
    remind_min_kb,
    remind_repeat_kb,
)

router = Router()


class AddTask(StatesGroup):
    title = State()
    description = State()
    due_date = State()
    due_time = State()
    remind_type = State()
    remind_min = State()
    remind_interval = State()


def _parse_time(text: str) -> str | None:
    """Convert dot-format time (9.30, 21.00) to HH:MM. Returns None if invalid."""
    m = re.match(r"^(\d{1,2})\.(\d{2})$", text.strip())
    if not m:
        return None
    h, minute = int(m.group(1)), int(m.group(2))
    if not (0 <= h <= 23 and 0 <= minute <= 59):
        return None
    return f"{h:02d}:{minute:02d}"


def _format_task_summary(data: dict, task_id: int, remind_min: int, repeat_remind: bool) -> str:
    lines = [f"✅ Задача добавлена (#{task_id})", f"<b>{data['title']}</b>"]
    if data.get("description"):
        lines.append(data["description"])
    if data.get("due_date"):
        time_part = f" в {data['due_time']}" if data.get("due_time") else ""
        lines.append(f"📅 {data['due_date']}{time_part}")
    if repeat_remind:
        lines.append("🔁 Буду напоминать каждые 30 мин до выполнения")
    elif remind_min:
        lines.append(f"🔔 Напомню за {remind_min} мин.")
    return "\n".join(lines)


async def _save_task(state: FSMContext, user_id: int, remind_min: int, repeat_remind: bool) -> str:
    data = await state.get_data()
    await state.clear()
    task_id = await crud.add_task(
        user_id=user_id,
        title=data["title"],
        description=data.get("description"),
        due_date=data.get("due_date"),
        due_time=data.get("due_time"),
        remind_min=remind_min,
        repeat_remind=repeat_remind,
    )
    return _format_task_summary(data, task_id, remind_min, repeat_remind)


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
    await message.answer("Краткое описание:", reply_markup=skip_kb())


# description — текст или кнопка «Пропустить»
@router.message(AddTask.description)
async def got_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(AddTask.due_date)
    await message.answer("Дата дедлайна в формате ДД.ММ.ГГГГ:", reply_markup=skip_kb())


@router.callback_query(AddTask.description, F.data == "skip")
async def skip_description(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(description=None)
    await state.set_state(AddTask.due_date)
    await callback.message.edit_text("Дата дедлайна в формате ДД.ММ.ГГГГ:", reply_markup=skip_kb())
    await callback.answer()


# due_date
@router.message(AddTask.due_date)
async def got_due_date(message: Message, state: FSMContext) -> None:
    try:
        parsed = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        await state.update_data(due_date=parsed.isoformat())
    except ValueError:
        await message.answer("Неверный формат. Попробуй ДД.ММ.ГГГГ:", reply_markup=skip_kb())
        return
    await state.set_state(AddTask.due_time)
    await message.answer("Время дедлайна (например 9.30 или 21.00):", reply_markup=skip_kb())


@router.callback_query(AddTask.due_date, F.data == "skip")
async def skip_due_date(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(due_date=None)
    await state.set_state(AddTask.due_time)
    await callback.message.edit_text(
        "Время дедлайна (например 9.30 или 21.00):", reply_markup=skip_kb()
    )
    await callback.answer()


# due_time
@router.message(AddTask.due_time)
async def got_due_time(message: Message, state: FSMContext) -> None:
    parsed = _parse_time(message.text)
    if parsed is None:
        await message.answer("Неверный формат. Используй точку: 9.30, 21.00:", reply_markup=skip_kb())
        return
    await state.update_data(due_time=parsed)
    await state.set_state(AddTask.remind_type)
    await message.answer("Как напоминать?", reply_markup=remind_type_kb())


@router.callback_query(AddTask.due_time, F.data == "skip")
async def skip_due_time(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(due_time=None)
    await state.set_state(AddTask.remind_type)
    await callback.message.edit_text("Как напоминать?", reply_markup=remind_type_kb())
    await callback.answer()


# remind_type
@router.callback_query(AddTask.remind_type, F.data.startswith("remind_type:"))
async def got_remind_type(callback: CallbackQuery, state: FSMContext) -> None:
    choice = callback.data.split(":")[1]

    if choice == "none":
        summary = await _save_task(state, callback.from_user.id, remind_min=0, repeat_remind=False)
        await callback.message.edit_text(summary, parse_mode="HTML")
        await callback.answer()
        return

    if choice == "repeat":
        await state.set_state(AddTask.remind_interval)
        await callback.message.edit_text("Как часто напоминать?", reply_markup=remind_repeat_kb())
        await callback.answer()
        return

    # once → ask how many minutes before
    await state.set_state(AddTask.remind_min)
    await callback.message.edit_text("За сколько минут напомнить?", reply_markup=remind_min_kb())
    await callback.answer()


# remind_min (один раз)
@router.callback_query(AddTask.remind_min, F.data.startswith("remind_min:"))
async def got_remind_min(callback: CallbackQuery, state: FSMContext) -> None:
    remind_min = int(callback.data.split(":")[1])
    summary = await _save_task(state, callback.from_user.id, remind_min=remind_min, repeat_remind=False)
    await callback.message.edit_text(summary, parse_mode="HTML")
    await callback.answer()


# remind_interval (пока не сделаю)
@router.callback_query(AddTask.remind_interval, F.data.startswith("remind_interval:"))
async def got_remind_interval(callback: CallbackQuery, state: FSMContext) -> None:
    interval = int(callback.data.split(":")[1])
    summary = await _save_task(state, callback.from_user.id, remind_min=interval, repeat_remind=True)
    await callback.message.edit_text(summary, parse_mode="HTML")
    await callback.answer()


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
        time_part = f" в {task['due_time']}" if task["due_time"] else ""
        lines.append(f"📅 {task['due_date']}{time_part}")
    if task["repeat_remind"]:
        lines.append("🔁 Напоминание каждые 30 мин до выполнения")
    elif task["remind_min"]:
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
    await callback.message.edit_reply_markup(reply_markup=task_actions_kb(task_id, done=True))


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


@router.callback_query(F.data == "nav:add")
async def cb_nav_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddTask.title)
    await callback.message.answer("Как называется задача?")
    await callback.answer()


@router.callback_query(F.data == "nav:tasks")
async def cb_nav_tasks(callback: CallbackQuery) -> None:
    tasks = await crud.get_tasks(callback.from_user.id)
    if not tasks:
        await callback.message.answer("У тебя нет активных задач.")
    else:
        await callback.message.answer("Твои задачи:", reply_markup=tasks_list_kb(tasks))
    await callback.answer()


@router.callback_query(F.data == "nav:today")
async def cb_nav_today(callback: CallbackQuery) -> None:
    today = date.today().isoformat()
    tasks = await crud.get_todays_tasks(callback.from_user.id, today)
    if not tasks:
        await callback.message.answer("На сегодня задач нет. Отдыхай!")
    else:
        lines = [f"<b>Задачи на сегодня ({today}):</b>"]
        for t in tasks:
            time_str = f" в {t['due_time']}" if t["due_time"] else ""
            lines.append(f"• {t['title']}{time_str}")
        await callback.message.answer("\n".join(lines), parse_mode="HTML")
    await callback.answer()
