from __future__ import annotations
import logging
from collections import defaultdict

import aiohttp
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

import config

log = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "Ты умный персональный ассистент пользователя в Telegram-боте «Правая рука». "
    "Отвечай на русском языке, кратко и по делу. "
    "Помогай с любыми вопросами: учёба, советы, объяснения, идеи и всё остальное."
)

_histories: dict[int, list[dict]] = defaultdict(list)
MAX_HISTORY = 40

router = Router()


def _push(user_id: int, role: str, text: str) -> None:
    _histories[user_id].append({"role": role, "content": text})
    if len(_histories[user_id]) > MAX_HISTORY:
        _histories[user_id] = _histories[user_id][-MAX_HISTORY:]


@router.message(Command("newchat"))
async def cmd_newchat(message: Message) -> None:
    _histories[message.from_user.id].clear()
    await message.answer("🔄 История диалога очищена. Начинаем заново!")


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def ai_handler(message: Message) -> None:
    if not config.GROQ_API_KEY:
        await message.answer("⚠️ AI-ассистент не настроен: отсутствует GROQ_API_KEY.")
        return

    user_id = message.from_user.id
    user_text = message.text.strip()

    await message.bot.send_chat_action(message.chat.id, "typing")

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + _histories[user_id].copy()
        + [{"role": "user", "content": user_text}]
    )

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GROQ_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()

        if resp.status != 200:
            error = data.get("error", {}).get("message", str(data))
            log.error("Groq API error %s: %s", resp.status, error)
            await message.answer(f"⚠️ Ошибка API: <code>{error}</code>", parse_mode="HTML")
            return

        reply = data["choices"][0]["message"]["content"]
        _push(user_id, "user", user_text)
        _push(user_id, "assistant", reply)
        await message.answer(reply)

    except Exception as e:
        log.error("AI handler error: %s", e, exc_info=True)
        await message.answer(f"⚠️ Ошибка: <code>{type(e).__name__}: {e}</code>", parse_mode="HTML")
