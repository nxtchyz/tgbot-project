from __future__ import annotations
import logging
from collections import defaultdict

import aiohttp
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

import config

log = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)

SYSTEM_PROMPT = (
    "Ты умный персональный ассистент пользователя в Telegram-боте «Правая рука». "
    "Отвечай на русском языке, кратко и по делу. "
    "Помогай с любыми вопросами: учёба, советы, объяснения, идеи и всё остальное."
)

_histories: dict[int, list[dict]] = defaultdict(list)
MAX_HISTORY = 40

router = Router()


def _push(user_id: int, role: str, text: str) -> None:
    _histories[user_id].append({"role": role, "parts": [{"text": text}]})
    if len(_histories[user_id]) > MAX_HISTORY:
        _histories[user_id] = _histories[user_id][-MAX_HISTORY:]


@router.message(Command("newchat"))
async def cmd_newchat(message: Message) -> None:
    _histories[message.from_user.id].clear()
    await message.answer("🔄 История диалога очищена. Начинаем заново!")


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def ai_handler(message: Message) -> None:
    if not config.GEMINI_API_KEY:
        await message.answer("⚠️ AI-ассистент не настроен: отсутствует GEMINI_API_KEY.")
        return

    user_id = message.from_user.id
    user_text = message.text.strip()

    await message.bot.send_chat_action(message.chat.id, "typing")

    contents = _histories[user_id].copy()
    contents.append({"role": "user", "parts": [{"text": user_text}]})

    system_seed = [
        {"role": "user",  "parts": [{"text": SYSTEM_PROMPT}]},
        {"role": "model", "parts": [{"text": "Понял, буду следовать инструкциям."}]},
    ]
    payload = {
        "contents": system_seed + contents,
        "generationConfig": {"maxOutputTokens": 1024},
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GEMINI_URL.format(key=config.GEMINI_API_KEY),
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()

        if resp.status != 200:
            error = data.get("error", {}).get("message", str(data))
            log.error("Gemini API error %s: %s", resp.status, error)
            await message.answer(f"⚠️ Ошибка API: <code>{error}</code>", parse_mode="HTML")
            return

        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        _push(user_id, "user", user_text)
        _push(user_id, "model", reply)
        await message.answer(reply)

    except Exception as e:
        log.error("AI handler error: %s", e, exc_info=True)
        await message.answer(f"⚠️ Ошибка: <code>{type(e).__name__}: {e}</code>", parse_mode="HTML")
