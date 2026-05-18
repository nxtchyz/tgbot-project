from __future__ import annotations
import asyncio
import logging
from collections import defaultdict

from groq import Groq
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

client = None
if config.GROQ_API_KEY:
    client = Groq(api_key=config.GROQ_API_KEY)

_histories: dict[int, list[dict]] = defaultdict(list)
MAX_HISTORY = 40  # последние 20 обменов

router = Router()


def _push(user_id: int, role: str, text: str) -> None:
    _histories[user_id].append({"role": role, "content": text})
    if len(_histories[user_id]) > MAX_HISTORY:
        _histories[user_id] = _histories[user_id][-MAX_HISTORY:]


def _build_messages(user_id: int, user_text: str) -> list[dict]:
    return (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + _histories[user_id]
        + [{"role": "user", "content": user_text}]
    )


# ── /newchat — сбросить историю ───────────────────────────────────────────────

@router.message(Command("newchat"))
async def cmd_newchat(message: Message) -> None:
    _histories[message.from_user.id].clear()
    await message.answer("🔄 История диалога очищена. Начинаем заново!")


# ── Основной AI-обработчик ────────────────────────────────────────────────────

@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def ai_handler(message: Message) -> None:
    if client is None:
        await message.answer("⚠️ AI-ассистент не настроен: отсутствует GROQ_API_KEY.")
        return

    user_id = message.from_user.id
    user_text = message.text.strip()

    await message.bot.send_chat_action(message.chat.id, "typing")

    messages = _build_messages(user_id, user_text)

    try:
        def _call() -> str:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=1024,
            )
            return response.choices[0].message.content

        reply = await asyncio.to_thread(_call)
        _push(user_id, "user", user_text)
        _push(user_id, "assistant", reply)
        await message.answer(reply)
    except Exception as e:
        log.error("Groq error: %s", e, exc_info=True)
        await message.answer(f"⚠️ Ошибка: <code>{type(e).__name__}: {e}</code>", parse_mode="HTML")
