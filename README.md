# 🤖 Правая рука — Personal Telegram Bot

Персональный многофункциональный Telegram-бот на Python.

## Возможности

### 📅 Ежедневник
- Добавление задач с дедлайном, описанием и временем
- Просмотр списка активных задач
- Отметка задач как выполненных и удаление
- Утренняя сводка дел на день в 09:00 по Москве
- Напоминание за N минут до дедлайна

### 📚 Расписание пар
- Расписание на сегодня с учётом чётности недели
- Расписание на всю неделю
- Номера пар, преподаватели, аудитории
- Автоматическое отображение окон между парами

### 🤖 AI-ассистент (Llama 3.3 70B via Groq)
- Отвечает на любые свободные сообщения
- Помнит контекст последних 20 обменов
- Не мешает работе команд и ежедневника
- `/newchat` — сбросить историю и начать заново

## Стек

- **Python 3.13**
- **aiogram 3.x** — Telegram Bot API
- **SQLite + aiosqlite** — база данных
- **APScheduler** — планировщик напоминаний
- **Llama 3.3 70B (Groq)** — AI-ассистент
- **aiohttp** — HTTP запросы к Groq API
- **python-dotenv** — конфигурация

## Установка

```bash
git clone https://github.com/nxtchyz/tgbot-project.git
cd tgbot-project
pip install -r requirements.txt
```

Создай файл `.env` в корне проекта:

```
BOT_TOKEN=your_telegram_token
GROQ_API_KEY=your_groq_key
```

- Telegram токен — у [@BotFather](https://t.me/BotFather)
- Groq API ключ — на [console.groq.com](https://console.groq.com) (бесплатно)

## Запуск

```bash
python main.py
```

## Структура проекта

```
tgbot_project/
├── bot/
│   ├── handlers/
│   │   ├── start.py        # /start, /menu, навигация по разделам
│   │   ├── planner.py      # ежедневник
│   │   ├── schedule.py     # расписание пар
│   │   └── ai_chat.py      # AI-ассистент (Groq / Llama)
│   ├── keyboards/
│   │   └── planner_kb.py   # inline-клавиатуры
│   └── scheduler.py        # APScheduler — напоминания и сводка
├── db/
│   ├── models.py           # инициализация таблиц
│   └── crud.py             # операции с БД
├── config.py
├── main.py
└── requirements.txt
```

## Команды

| Команда | Описание |
|---|---|
| `/start` | Главное меню |
| `/planner` | Раздел ежедневника |
| `/add` | Добавить задачу |
| `/tasks` | Список активных задач |
| `/today` | Задачи на сегодня |
| `/schedule` | Раздел расписания |
| `/pairs` | Пары на сегодня |
| `/week` | Расписание на неделю |
| `/newchat` | Сбросить историю AI-диалога |
| `/menu` | Вернуться в главное меню |
