from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, BotCommandScopeChat, FSInputFile

import config
from db.models import DB_PATH

router = Router()

MAIN_MENU_COMMANDS = [
    BotCommand(command="start",    description="Главное меню"),
    BotCommand(command="planner",  description="📅 Ежедневник — дела и напоминания"),
    BotCommand(command="schedule", description="📚 Расписание — пары по дням"),
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
<i>/planner — открыть раздел</i>

━━━━━━━━━━━━━━━━━━━
<b>📚 Расписание пар</b>
Смотри пары на сегодня или на всю неделю с учётом чётности.
<i>/schedule — открыть раздел</i>

━━━━━━━━━━━━━━━━━━━
<i>🔜 Скоро появятся новые разделы...</i>

Выбери раздел командой или нажми <b>/</b> у строки ввода.
""".strip()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.bot.set_my_commands(
        MAIN_MENU_COMMANDS,
        scope=BotCommandScopeChat(chat_id=message.chat.id),
    )
    name = message.from_user.first_name or "друг"
    await message.answer(START_TEXT.format(name=name), parse_mode="HTML")


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.bot.set_my_commands(
        MAIN_MENU_COMMANDS,
        scope=BotCommandScopeChat(chat_id=message.chat.id),
    )
    name = message.from_user.first_name or "друг"
    await message.answer(START_TEXT.format(name=name), parse_mode="HTML")


@router.message(Command("planner"))
async def cmd_planner(message: Message) -> None:
    await message.bot.set_my_commands(
        PLANNER_COMMANDS,
        scope=BotCommandScopeChat(chat_id=message.chat.id),
    )
    await message.answer(
        "📅 <b>Ежедневник</b>\n\n"
        "/add — добавить задачу\n"
        "/tasks — список активных задач\n"
        "/today — задачи на сегодня\n\n"
        "<i>/menu — вернуться в главное меню</i>",
        parse_mode="HTML",
    )


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


@router.message(Command("schedule"))
async def cmd_schedule(message: Message) -> None:
    await message.bot.set_my_commands(
        SCHEDULE_COMMANDS,
        scope=BotCommandScopeChat(chat_id=message.chat.id),
    )
    await message.answer(
        "📚 <b>Расписание пар</b>\n\n"
        "/pairs — пары на сегодня\n"
        "/week — расписание на всю неделю\n\n"
        "<i>/menu — вернуться в главное меню</i>",
        parse_mode="HTML",
    )
