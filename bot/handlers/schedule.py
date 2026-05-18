from __future__ import annotations
from datetime import date, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

# May 18, 2026 (Monday) = odd week (нечётная)
_REF_ODD_MONDAY = date(2026, 5, 18)

DAY_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
MONTHS_GEN = ["", "янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
TYPE_EMOJI = {"Лекция": "📖", "Практика": "💻"}

# weeks: 0 = каждую, 1 = нечётную, 2 = чётную
SCHEDULE: dict[int, list[dict]] = {
    0: [  # Понедельник
        {"time": "13:40", "subject": "Информационные технологии", "type": "Практика",
         "teacher": "Цехановский В.В.", "room": None, "weeks": 0},
    ],
    1: [  # Вторник
        {"time": "08:00", "subject": "Физика, конт", "type": "Лекция",
         "teacher": "Ходьков Д.А.", "room": None, "weeks": 0},
        {"time": "09:50", "subject": "Физкультура", "type": "Практика",
         "teacher": None, "room": None, "weeks": 0},
        {"time": "11:40", "subject": "Математический анализ", "type": "Лекция",
         "teacher": "Медведев А.Н.", "room": "3324", "weeks": 0},
        {"time": "13:40", "subject": "Дискретная математика и теор. информатика", "type": "Практика",
         "teacher": "Соловьев С.В.", "room": "4211", "weeks": 0},
        {"time": "15:30", "subject": "Математический анализ", "type": "Практика",
         "teacher": "Медведев А.Н.", "room": "3421", "weeks": 0},
    ],
    2: [  # Среда
        {"time": "08:00", "subject": "Программирование", "type": "Лекция",
         "teacher": "Синев В.Е.", "room": "1158", "weeks": 0},
        {"time": "09:50", "subject": "Информационные технологии", "type": "Лекция",
         "teacher": "Цехановский В.В.", "room": "1158", "weeks": 0},
        {"time": "11:40", "subject": "Иностранный язык", "type": "Практика",
         "teacher": None, "room": "к.ИняЗ", "weeks": 0},
    ],
    3: [  # Четверг
        {"time": "08:00", "subject": "Физкультура", "type": "Практика",
         "teacher": None, "room": None, "weeks": 0},
        {"time": "09:50", "subject": "Дискретная математика и теор. информатика", "type": "Лекция",
         "teacher": "Чухнов А.С.", "room": "3308", "weeks": 0},
        {"time": "11:40", "subject": "История России", "type": "Лекция",
         "teacher": "Тарасова Е.А.", "room": "5427", "weeks": 0},
    ],
    4: [  # Пятница
        {"time": "08:00", "subject": "Физика", "type": "Практика",
         "teacher": "Иманбаева Р.Т., Лоскутников В.С.", "room": "3102", "weeks": 1},
        {"time": "09:50", "subject": "Алгебра и геометрия", "type": "Практика",
         "teacher": "Крым В.Р.", "room": "4210", "weeks": 0},
        {"time": "11:40", "subject": "История России", "type": "Практика",
         "teacher": "Рубцов А.А.", "room": "3426", "weeks": 0},
        {"time": "13:40", "subject": "История России", "type": "Лекция",
         "teacher": "Тарасова Е.А.", "room": "5427", "weeks": 0},
    ],
    5: [  # Суббота
        {"time": "08:00", "subject": "Экология", "type": "Лекция",
         "teacher": "Ковалевская А.С.", "room": None, "weeks": 1},
        {"time": "09:50", "subject": "Алгебра и геометрия", "type": "Лекция",
         "teacher": "Костырев И.И.", "room": "3308", "weeks": 0},
        {"time": "11:40", "subject": "Программирование", "type": "Практика",
         "teacher": "Глущенко А.Г.", "room": "1215", "weeks": 0},
    ],
}


def week_parity(d: date | None = None) -> int:
    """1 = нечётная, 2 = чётная."""
    if d is None:
        d = date.today()
    monday = d - timedelta(days=d.weekday())
    delta_weeks = (monday - _REF_ODD_MONDAY).days // 7
    return 1 if delta_weeks % 2 == 0 else 2


def parity_label(p: int) -> str:
    return "нечётная" if p == 1 else "чётная"


def get_day_pairs(weekday: int, parity: int) -> list[dict]:
    return [p for p in SCHEDULE.get(weekday, []) if p["weeks"] == 0 or p["weeks"] == parity]


def fmt_pair(pair: dict) -> str:
    emoji = TYPE_EMOJI.get(pair["type"], "•")
    lines = [f"• <b>{pair['time']}</b>  {pair['subject']} {emoji}"]
    details = []
    if pair.get("teacher"):
        details.append(pair["teacher"])
    if pair.get("room"):
        details.append(f"ауд. {pair['room']}")
    if details:
        lines.append("  " + " · ".join(details))
    return "\n".join(lines)


def fmt_day_block(d: date, parity: int) -> str | None:
    pairs = get_day_pairs(d.weekday(), parity)
    if not pairs:
        return None
    header = f"<b>{DAY_NAMES[d.weekday()]}, {d.day} {MONTHS_GEN[d.month]}</b>"
    return header + "\n" + "\n\n".join(fmt_pair(p) for p in pairs)


# ── /pairs — пары на сегодня ───────────────────────────────────────────────────

@router.message(Command("pairs"))
async def cmd_pairs(message: Message) -> None:
    today = date.today()
    parity = week_parity(today)

    if today.weekday() == 6:
        await message.answer("Сегодня воскресенье — пар нет 🎉")
        return

    pairs = get_day_pairs(today.weekday(), parity)
    if not pairs:
        await message.answer(
            f"<b>{DAY_NAMES[today.weekday()]}, {today.day} {MONTHS_GEN[today.month]}</b>\n\nПар нет 🎉",
            parse_mode="HTML",
        )
        return

    block = fmt_day_block(today, parity)
    await message.answer(
        f"📅 <b>Сегодня</b>  <i>({parity_label(parity)} неделя)</i>\n\n{block}",
        parse_mode="HTML",
    )


# ── /week — расписание на неделю ──────────────────────────────────────────────

@router.message(Command("week"))
async def cmd_week(message: Message) -> None:
    today = date.today()
    parity = week_parity(today)
    monday = today - timedelta(days=today.weekday())
    saturday = monday + timedelta(days=5)

    blocks = []
    for i in range(6):  # Пн–Сб
        block = fmt_day_block(monday + timedelta(days=i), parity)
        if block:
            blocks.append(block)

    if not blocks:
        await message.answer("На этой неделе пар нет 🎉")
        return

    header = (
        f"📅 <b>Расписание на неделю</b>\n"
        f"<i>{parity_label(parity)} · "
        f"{monday.day} {MONTHS_GEN[monday.month]} — {saturday.day} {MONTHS_GEN[saturday.month]}</i>\n"
    )
    await message.answer(header + "\n" + "\n\n".join(blocks), parse_mode="HTML")
