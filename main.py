import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_IDS, STATS_FILE, APPEALS_FILE, ROLES, ACHIEVEMENTS_FILE
from handlers.user import user_router
from handlers.admin import admin_router
# Мы убрали appeals_router, так как его функционал теперь в других файлах
# from handlers.appeals import appeals_router 
from handlers.achievements import achievements_router
from utils.database import save_stats, save_appeals, save_achievements

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
    
    # --- ПРАВИЛЬНЫЙ ПОРЯДОК РЕГИСТРАЦИИ РОУТЕРОВ ---
    # Сначала регистрируем роутеры с конкретными командами
    dp.include_router(admin_router)
    # dp.include_router(appeals_router) # appeals_router больше не используется
    dp.include_router(achievements_router)
    
    # В САМОМ КОНЦЕ регистрируем роутер с обработчиком для всех остальных сообщений
    dp.include_router(user_router)
    
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот: @{bot_info.username}")
        if ADMIN_IDS:
            logger.info("✅ Список администраторов загружен:")
            for role, ids in ROLES.items():
                if ids:
                    logger.info(f"  - {role.replace('_', ' ').title()}: {', '.join(map(str, ids))}")
        else:
            logger.warning("⚠️ ID админов не установлены в .env файле!")
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о боте: {e}")
    
    # Создаем файлы данных, если они отсутствуют
    if not STATS_FILE.exists():
        save_stats({})
        logger.info(f"Создан файл статистики: {STATS_FILE}")
    if not APPEALS_FILE.exists():
        save_appeals({})
        logger.info(f"Создан файл обращений: {APPEALS_FILE}")
    if not ACHIEVEMENTS_FILE.exists():
        save_achievements([])
        logger.info(f"Создан файл достижений: {ACHIEVEMENTS_FILE}")
    
    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем.")
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка при запуске бота: {e}", exc_info=True)
