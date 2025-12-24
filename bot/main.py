import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
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

@dp.message(Command("start"))
async def start_handler(message: Message):
    """Приветствие с инструкцией"""
    await message.answer(
        "👋 **Повторюшка студсовета ФГУ**\n\n"
        "• Напишите любое сообщение\n"
        "• Я повторю его дословно\n\n"
        "🧪 *Тестирование aiogram 3.13.1*",
        parse_mode="Markdown"
    )

@dp.message()
async def echo_handler(message: Message):
    """Повторяет ВСЁ, что пишет пользователь"""
    user = message.from_user
    
    response = (
        f"👤 *{user.first_name or 'Пользователь'}*\n"
        f"`ID: {user.id}`\n\n"
        f"📢 **Сообщение:**\n"
        f"{message.text}"
    )
    
    await message.answer(response, parse_mode="Markdown")

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
