from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BotCommand, BotCommandScopeChat, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
from db.models import DB_PATH

router = Router()

MAIN_MENU_COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
]

PLANNER_COMMANDS = [
    BotCommand(command="add",   description="Добавить задачу"),
    BotCommand(command="tasks", description="Мои задачи"),
    BotCommand(command="today", description="Задачи на сегодня"),
    BotCommand(command="menu",  description="◀️ Главное меню"),
]

SCHEDULE_COMMANDS = [
    BotCommand(command="pairs", description="Пары на сегодня"),
    BotCommand(command="week",  description="Расписание на неделю"),
    BotCommand(command="menu",  description="◀️ Главное меню"),
]

START_TEXT = """
👋 <b>Привет, {name}!</b>

Я твой персональный помощник. Вот что я умею:

━━━━━━━━━━━━━━━━━━━
<b>📅 Ежедневник</b>
Добавляй задачи, ставь дедлайны и получай напоминания — утром сводку на день и в нужный момент перед делом.

━━━━━━━━━━━━━━━━━━━
<b>📚 Расписание пар</b>
Смотри пары на сегодня или на всю неделю с учётом чётности.

━━━━━━━━━━━━━━━━━━━
<i>🔜 Скоро появятся новые разделы...</i>
""".strip()


def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Ежедневник", callback_data="section:planner")
    builder.button(text="📚 Расписание", callback_data="section:schedule")
    builder.adjust(2)
    return builder.as_markup()


async def _show_main_menu(message: Message) -> None:
    await message.bot.set_my_commands(
        MAIN_MENU_COMMANDS,
        scope=BotCommandScopeChat(chat_id=message.chat.id),
    )
    name = message.from_user.first_name or "друг"
    await message.answer(START_TEXT.format(name=name), parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await _show_main_menu(message)


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await _show_main_menu(message)


@router.callback_query(F.data == "section:planner")
async def cb_planner(callback: CallbackQuery) -> None:
    await callback.bot.set_my_commands(
        PLANNER_COMMANDS,
        scope=BotCommandScopeChat(chat_id=callback.message.chat.id),
    )
    await callback.message.edit_text(
        "📅 <b>Ежедневник</b>\n\n"
        "/add — добавить задачу\n"
        "/tasks — список активных задач\n"
        "/today — задачи на сегодня\n\n"
        "<i>/menu — вернуться в главное меню</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "section:schedule")
async def cb_schedule(callback: CallbackQuery) -> None:
    await callback.bot.set_my_commands(
        SCHEDULE_COMMANDS,
        scope=BotCommandScopeChat(chat_id=callback.message.chat.id),
    )
    await callback.message.edit_text(
        "📚 <b>Расписание пар</b>\n\n"
        "/pairs — пары на сегодня\n"
        "/week — расписание на всю неделю\n\n"
        "<i>/menu — вернуться в главное меню</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("getdb"))
async def cmd_getdb(message: Message) -> None:
    if message.from_user.id != config.ADMIN_ID:
        await message.answer(f"ID: {message.from_user.id}")
        return
    import os
    paths_to_check = [DB_PATH, f"/app/data/{DB_PATH}", f"/app/{DB_PATH}"]
    for path in paths_to_check:
        if os.path.exists(path):
            await message.answer_document(FSInputFile(path, filename="planner.db"))
            return
    await message.answer(f"Файл не найден. Проверил: {', '.join(paths_to_check)}\nРабочая папка: {os.getcwd()}")


