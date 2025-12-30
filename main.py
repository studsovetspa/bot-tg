import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_IDS, STATS_FILE, APPEALS_FILE
from handlers.user import user_router
from handlers.admin import admin_router
from handlers.appeals import appeals_router
from utils.database import save_stats, save_appeals

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск бота студсовета...")
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Подключаем роутеры
    dp.include_router(admin_router)
    dp.include_router(appeals_router)
    dp.include_router(user_router)
    
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот: @{bot_info.username}")
        if ADMIN_IDS:
            logger.info(f"👤 ID админов: {', '.join(map(str, ADMIN_IDS))}")
        else:
            logger.warning("⚠️ ID админов не установлены!")
    except Exception as e:
        logger.error(f"Ошибка получения информации о боте: {e}")
    
    # Создаем файлы если их нет
    if not STATS_FILE.exists():
        save_stats({})
    if not APPEALS_FILE.exists():
        save_appeals({})
    
    # Запуск
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

