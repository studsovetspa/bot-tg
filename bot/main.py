import asyncio
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")


# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Файл для хранения статистики пользователей
STATS_FILE = Path("user_stats.json")


# Текст новости (используем HTML для надежности)
NEWS_TEXT = """📰 <b>НОВОСТЬ ОТ СТУДСОВЕТА ФГУ!</b>

🎉 <i>С Новым 2026 годом!</i>

Дорогие студенты!

Студсовет поздравляет вас с наступающим Новым годом!
Желаем успехов в учебе, ярких впечатлений и новых достижений!

📅 <i>Каникулы: 28 декабря - 12 января</i>
📚 <i>Расписание на январь - на сайте ФГУ</i>

#студсовет #ФГУ #новости"""


def load_stats():
    """Загружает статистику из файла"""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_stats(stats):
    """Сохраняет статистику в файл"""
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")


def update_user_stats(user_id, username=None, first_name=None):
    """Обновляет статистику пользователя"""
    stats = load_stats()
    
    if str(user_id) not in stats:
        stats[str(user_id)] = {
            "first_name": first_name or "Неизвестно",
            "username": username or None,
            "messages_count": 0,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
    
    # Увеличиваем счетчик сообщений
    stats[str(user_id)]["messages_count"] += 1
    stats[str(user_id)]["last_seen"] = datetime.now().isoformat()
    
    save_stats(stats)


def get_stats_summary():
    """Возвращает общую статистику в безопасном HTML формате"""
    stats = load_stats()
    total_users = len(stats)
    total_messages = sum(user_data["messages_count"] for user_data in stats.values())
    
    active_users = 0
    try:
        now = datetime.now()
        active_users = sum(1 for user_data in stats.values() 
                          if (now - datetime.fromisoformat(user_data["last_seen"])).days <= 7)
    except:
        active_users = 0
    
    top_users = sorted(stats.items(), 
                      key=lambda x: x[1]["messages_count"], 
                      reverse=True)[:5]
    
    summary = f"""<b>📊 Статистика бота</b>

👥 Всего пользователей: <b>{total_users}</b>
💬 Всего сообщений: <b>{total_messages}</b>
🔥 Активных за неделю: <b>{active_users}</b>

<b>🏆 Топ-5 активных:</b>"""
    
    for i, (user_id, data) in enumerate(top_users, 1):
        username = f"@{data['username']}" if data['username'] else ""
        summary += f"\n{i}. <b>{data['first_name']}</b> {username} — {data['messages_count']} сообщений"
    
    return summary


def get_main_menu():
    """Создает главное меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📰 Новость")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


@dp.message(Command("start"))
async def start_handler(message: Message):
    """Приветствие с меню"""
    user = message.from_user
    update_user_stats(user.id, user.username, user.first_name)
    
    await message.answer(
        "👋 <b>Студсовет ФГУ</b>\n\n"
        "📰 <i>Новости студсовета</i>\n"
        "📊 <i>Статистика бота</i>\n\n"
        "🧪 <i>Aiogram 3.13.1</i>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@dp.message(F.text == "📰 Новость")
async def news_handler(message: Message):
    """Отправляет новость"""
    user = message.from_user
    update_user_stats(user.id, user.username, user.first_name)
    
    try:
        await message.answer(
            NEWS_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка отправки новости: {e}")
        await message.answer(
            "📰 Новость временно недоступна",
            reply_markup=get_main_menu()
        )


@dp.message(F.text == "📊 Статистика")
async def stats_handler(message: Message):
    """Показывает статистику"""
    user = message.from_user
    update_user_stats(user.id, user.username, user.first_name)
    
    try:
        stats_text = get_stats_summary()
        await message.answer(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        await message.answer(
            "📊 Статистика временно недоступна",
            reply_markup=get_main_menu()
        )


@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    """Показывает справку"""
    user = message.from_user
    update_user_stats(user.id, user.username, user.first_name)
    
    await message.answer(
        "<b>📖 Меню студсовета ФГУ</b>\n\n"
        "• 📰 <i>Новость</i> — свежие новости\n"
        "• 📊 <i>Статистика</i> — данные о пользователях\n"
        "• /start — главное меню\n\n"
        "👨‍💻 <i>Студсовет ФГУ</i>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@dp.message()
async def echo_handler(message: Message):
    """Обработка неизвестных команд"""
    update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        "❓ Неизвестная команда. Используйте меню:",
        reply_markup=get_main_menu()
    )


async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск бота студсовета...")
    
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Ошибка получения информации о боте: {e}")
    
    # Создаем файл статистики если его нет
    if not STATS_FILE.exists():
        save_stats({})
    
    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
