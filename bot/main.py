import asyncio
import logging
import os
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

# Текст новости (можно изменить)
NEWS_TEXT = """
📰 **НОВОСТЬ ОТ СТУДСОВЕТА ФГУ!**

🎉 *С Новым 2026 годом!*

Дорогие студенты! 

Студсовет поздравляет вас с наступающим Новым годом! 
Желаем успехов в учебе, ярких впечатлений и новых достижений!

📅 *Каникулы: 28 декабря - 12 января*
📚 *Расписание на январь - на сайте ФГУ*

#студсовет #ФГУ #новости
"""

def get_main_menu():
    """Создает главное меню с кнопкой 'Новость'"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📰 Новость")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: Message):
    """Приветствие с инструкцией и меню"""
    await message.answer(
        "👋 **Повторюшка студсовета ФГУ**\n\n"
        "• Напишите любое сообщение\n"
        "• Я повторю его дословно\n\n"
        "📰 Нажмите кнопку *Новость* для свежих новостей!\n\n"
        "🧪 *Тестирование aiogram 3.13.1*",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "📰 Новость")
async def news_handler(message: Message):
    """Отправляет новость при нажатии кнопки"""
    await message.answer(
        NEWS_TEXT,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    """Показывает справку"""
    await message.answer(
        "📖 **Помощь**\n\n"
        "• Напишите текст → бот повторит\n"
        "• 📰 Новость → свежие новости\n"
        "• /start → перезапустить\n\n"
        "👨‍💻 *Студсовет ФГУ*",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

@dp.message()
async def echo_handler(message: Message):
    """Повторяет ВСЁ, что пишет пользователь (кроме команд меню)"""
    user = message.from_user
    
    response = (
        f"👤 *{user.first_name or 'Пользователь'}*\n"
        f"`ID: {user.id}`\n\n"
        f"📢 **Сообщение:**\n"
        f"{message.text}"
    )
    
    await message.answer(response, parse_mode="Markdown", reply_markup=get_main_menu())

async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск повторюшки...")
    logger.info(f"✅ Бот: @{await bot.get_me()}")
    
    # Запуск polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
