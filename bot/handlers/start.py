from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, BotCommandScopeChat

router = Router()

MAIN_MENU_COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="planner", description="📅 Ежедневник — дела и напоминания"),
]

PLANNER_COMMANDS = [
    BotCommand(command="add", description="Добавить задачу"),
    BotCommand(command="tasks", description="Мои задачи"),
    BotCommand(command="today", description="Задачи на сегодня"),
    BotCommand(command="menu", description="◀️ Главное меню"),
]

START_TEXT = """
👋 <b>Привет, {name}!</b>

Я твой персональный помощник. Вот что я умею:

━━━━━━━━━━━━━━━━━━━
<b>📅 Ежедневник</b>
Добавляй задачи, ставь дедлайны и получай напоминания — утром сводку на день и в нужный момент перед делом.
<i>/planner — открыть раздел</i>

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
    await message.answer(
        "Ты в главном меню. Выбери раздел:",
        parse_mode="HTML",
    )


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
