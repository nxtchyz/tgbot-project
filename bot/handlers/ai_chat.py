from __future__ import annotations
import asyncio
import logging
from collections import defaultdict

import google.generativeai as genai
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

import config

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты умный персональный ассистент пользователя в Telegram-боте «Правая рука». "
    "Отвечай на русском языке, кратко и по делу. "
    "Помогай с любыми вопросами: учёба, советы, объяснения, идеи и всё остальное."
)

model = None
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )

# История диалога в памяти, per user_id
_histories: dict[int, list[dict]] = defaultdict(list)
MAX_HISTORY = 40  # последние 20 обменов

router = Router()


def _get_history(user_id: int) -> list[dict]:
    return _histories[user_id]


def _push(user_id: int, role: str, text: str) -> None:
    _histories[user_id].append({"role": role, "parts": [text]})
    if len(_histories[user_id]) > MAX_HISTORY:
        _histories[user_id] = _histories[user_id][-MAX_HISTORY:]


# ── /newchat — сбросить историю ───────────────────────────────────────────────

@router.message(Command("newchat"))
async def cmd_newchat(message: Message) -> None:
    _histories[message.from_user.id].clear()
    await message.answer("🔄 История диалога очищена. Начинаем заново!")


# ── Основной AI-обработчик ────────────────────────────────────────────────────
# StateFilter(None) — срабатывает только когда пользователь НЕ в FSM-состоянии

@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def ai_handler(message: Message) -> None:
    if model is None:
        await message.answer("⚠️ AI-ассистент не настроен: отсутствует GEMINI_API_KEY.")
        return

    user_id = message.from_user.id
    user_text = message.text.strip()

    await message.bot.send_chat_action(message.chat.id, "typing")

    history_snapshot = _get_history(user_id).copy()
    _push(user_id, "user", user_text)

    try:
        chat = model.start_chat(history=history_snapshot)
        response = await asyncio.to_thread(chat.send_message, user_text)
        reply = response.text
        _push(user_id, "model", reply)
        await message.answer(reply)
    except Exception as e:
        log.error("Gemini error: %s", e, exc_info=True)
        _histories[user_id].pop()
        await message.answer("⚠️ Не удалось получить ответ, попробуй чуть позже.")
