from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import NEWS_TEXT, is_admin
from utils.database import update_user_stats, get_stats_summary, get_student_achievements_summary
from utils.keyboards import get_main_menu

user_router = Router()


@user_router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    """Приветствие"""
    await state.clear()
    user = message.from_user
    update_user_stats(user.id, user.username, user.first_name)
    
    await message.answer(
        "👋 <b>Студсовет ФГУ</b>\n\n"
        "📰 <i>Новости студсовета</i>\n"
        "💬 <i>Анонимные обращения</i>\n"
        "📊 <i>Статистика бота</i>\n\n"
        "🧪 <i>Aiogram 3.13.1</i>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@user_router.message(Command("achievements"))
async def get_achievements_command(message: Message):
    """Показывает достижения студента."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Пожалуйста, укажите ФИО студента после команды. \nНапример: `/achievements Иванов Иван Иванович`")
        return

    student_name = args[1]
    summary = get_student_achievements_summary(student_name)
    await message.answer(summary, parse_mode="HTML")


@user_router.message(F.text == "📰 Новость")
async def news_handler(message: Message):
    """Новость"""
    update_user_stats(message.from_user.id, message.from_user.username, 
                     message.from_user.first_name)
    
    await message.answer(NEWS_TEXT, parse_mode="HTML", reply_markup=get_main_menu())


@user_router.message(F.text == "📊 Статистика")
async def stats_handler(message: Message):
    """Статистика"""
    update_user_stats(message.from_user.id, message.from_user.username,
                     message.from_user.first_name)
    
    try:
        stats_text = get_stats_summary()
        await message.answer(stats_text, parse_mode="HTML", reply_markup=get_main_menu())
    except Exception as e:
        await message.answer("📊 Статистика временно недоступна", 
                           reply_markup=get_main_menu())


@user_router.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    """Помощь"""
    update_user_stats(message.from_user.id, message.from_user.username,
                     message.from_user.first_name)
    
    help_text = """<b>📖 Меню студсовета ФГУ</b>

• 📰 <i>Новость</i> — свежие новости
• 💬 <i>Анонимное обращение</i> — задать вопрос
• 📊 <i>Статистика</i> — данные о боте
• /start — главное меню
• /achievements [ФИО] - просмотр достижений студента

👨‍💻 <i>Студсовет ФГУ</i>"""
    
    if is_admin(message.from_user.id):
        help_text += "\n\n<b>🔐 Команды админа:</b>\n"
        help_text += "• /add_achievement - добавить достижение\n"
        help_text += "• /pending_achievements - ожидающие подтверждения\n"
        help_text += "• /appeals — список обращений\n"
        help_text += "• /view_XXXX — просмотр\n"
        help_text += "• /reply_XXXX — ответить"
    
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_menu())


@user_router.message()
async def echo_handler(message: Message):
    """Неизвестная команда"""
    update_user_stats(message.from_user.id, message.from_user.username,
                     message.from_user.first_name)
    
    await message.answer("❓ Неизвестная команда. Используйте меню:",
                        reply_markup=get_main_menu())
