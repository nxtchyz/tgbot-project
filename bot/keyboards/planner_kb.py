from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def tasks_list_kb(tasks: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks:
        label = f"{'✅' if task['done'] else '📌'} {task['title']}"
        builder.button(text=label, callback_data=f"task:{task['id']}")
    builder.adjust(1)
    return builder.as_markup()


def task_actions_kb(task_id: int, done: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not done:
        builder.button(text="✅ Выполнено", callback_data=f"done:{task_id}")
    builder.button(text="🗑 Удалить", callback_data=f"delete:{task_id}")
    builder.button(text="◀️ Назад", callback_data="back:list")
    builder.adjust(1)
    return builder.as_markup()
