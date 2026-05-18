from aiogram.types import InlineKeyboardMarkup
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


def skip_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Пропустить", callback_data="skip")
    return builder.as_markup()


def remind_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔔 Один раз", callback_data="remind_type:once")
    builder.button(text="🔁 Пока не сделаю", callback_data="remind_type:repeat")
    builder.button(text="🔕 Без напоминания", callback_data="remind_type:none")
    builder.adjust(1)
    return builder.as_markup()


def remind_min_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="15 мин", callback_data="remind_min:15")
    builder.button(text="30 мин", callback_data="remind_min:30")
    builder.button(text="1 час",  callback_data="remind_min:60")
    builder.button(text="2 часа", callback_data="remind_min:120")
    builder.adjust(2)
    return builder.as_markup()


def remind_repeat_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="каждые 5 мин",  callback_data="remind_interval:5")
    builder.button(text="каждые 15 мин", callback_data="remind_interval:15")
    builder.button(text="каждые 30 мин", callback_data="remind_interval:30")
    builder.adjust(1)
    return builder.as_markup()
