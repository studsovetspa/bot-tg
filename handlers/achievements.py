from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import logging

from config import is_admin, is_leadership, get_role_name, LEADERSHIP_IDS
from utils.database import (
    create_achievement,
    get_pending_achievements,
    get_achievement,
    update_achievement_status
)
from utils.keyboards import get_cancel_keyboard

achievements_router = Router()
logger = logging.getLogger(__name__)


# --- FSM для добавления индивидуального достижения ---
class AddAchievement(StatesGroup):
    waiting_for_student_name = State()
    waiting_for_education_level = State()
    waiting_for_course = State()
    waiting_for_description = State()
    waiting_for_points = State()


# --- Клавиатуры ---
def get_pending_achievement_keyboard(achievement_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"ach_approve_{achievement_id}")
    builder.button(text="❌ Отклонить", callback_data=f"ach_reject_{achievement_id}")
    return builder.as_markup()

def get_education_level_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Бакалавриат")
    builder.button(text="Магистратура")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_course_keyboard(education_level: str):
    builder = ReplyKeyboardBuilder()
    if education_level == "Бакалавриат":
        courses = [str(i) for i in range(1, 5)]
    else: # Магистратура
        courses = [str(i) for i in range(1, 3)]
    
    for course in courses:
        builder.button(text=course)
    builder.adjust(4)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


# --- Команды для админов ---
@achievements_router.message(Command("add_achievement"))
async def start_add_achievement(message: Message, state: FSMContext):
    """Начинает процесс добавления нового индивидуального достижения."""
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(AddAchievement.waiting_for_student_name)
    await message.answer(
        "📝 <b>Добавление индивидуального достижения</b>\n\n"
        "Введите ФИО студента, которому вы хотите добавить индивидуальное достижение.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


# --- Обработка FSM ---
@achievements_router.message(AddAchievement.waiting_for_student_name)
async def process_student_name(message: Message, state: FSMContext):
    await state.update_data(student_name=message.text)
    await state.set_state(AddAchievement.waiting_for_education_level)
    await message.answer("Выберите уровень образования.", reply_markup=get_education_level_keyboard())

@achievements_router.message(AddAchievement.waiting_for_education_level, F.text.in_(["Бакалавриат", "Магистратура"]))
async def process_education_level(message: Message, state: FSMContext):
    education_level = message.text
    await state.update_data(education_level=education_level)
    await state.set_state(AddAchievement.waiting_for_course)
    await message.answer(
        "Выберите курс.",
        reply_markup=get_course_keyboard(education_level)
    )

@achievements_router.message(AddAchievement.waiting_for_course, F.text.regexp(r'^[1-4]$'))
async def process_course(message: Message, state: FSMContext):
    data = await state.get_data()
    education_level = data.get("education_level")
    course = message.text

    is_valid = False
    if education_level == "Бакалавриат" and course in ["1", "2", "3", "4"]:
        is_valid = True
    elif education_level == "Магистратура" and course in ["1", "2"]:
        is_valid = True

    if not is_valid:
        await message.answer(
            "⛔️ <b>Ошибка:</b> Пожалуйста, выберите курс с помощью кнопок.", 
            parse_mode="HTML",
            reply_markup=get_course_keyboard(education_level)
        )
        return

    await state.update_data(course=course)
    await state.set_state(AddAchievement.waiting_for_description)
    await message.answer(
        "Теперь опишите индивидуальное достижение (за что начисляются баллы).",
        reply_markup=ReplyKeyboardRemove()
    )


@achievements_router.message(AddAchievement.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddAchievement.waiting_for_points)
    await message.answer("Введите количество баллов (целое число).")


@achievements_router.message(AddAchievement.waiting_for_points)
async def process_points(message: Message, state: FSMContext, bot: Bot):
    try:
        points = int(message.text)
    except ValueError:
        await message.answer("⛔️ <b>Ошибка:</b> Количество баллов должно быть целым числом. Попробуйте снова.", parse_mode="HTML")
        return

    data = await state.get_data()
    student_name = data.get("student_name")
    education_level = data.get("education_level")
    course = data.get("course")
    description = data.get("description")

    reporter_id = message.from_user.id
    reporter_name = message.from_user.full_name
    reporter_role = get_role_name(reporter_id)
    
    achievement_id = create_achievement(
        reporter_id=reporter_id,
        reporter_name=reporter_name,
        reporter_role=reporter_role,
        student_name=student_name,
        education_level=education_level,
        course=course,
        description=description,
        points=points
    )

    await state.clear()
    await message.answer(
        "✅ <b>Заявка на добавление индивидуального достижения создана!</b>\n\n"
        f"Студент: <b>{student_name}</b>\n"
        f"Уровень образования: <b>{education_level}</b>\n"
        f"Курс: <b>{course}</b>\n"
        f"Описание: <b>{description}</b>\n"
        f"Баллы: <b>{points}</b>\n\n"
        "Она отправлена на подтверждение руководству.",
        parse_mode="HTML"
    )

    # --- Отправка уведомления руководству ---
    notification_text = (
        f"🔔 <b>Новая заявка на индивидуальное достижение!</b>\n\n"
        f"От: <b>{reporter_name} ({reporter_role})</b>\n"
        f"Студент: <b>{student_name}</b>\n"
        f"Уровень образования: <b>{education_level}</b>\n"
        f"Курс: <b>{course}</b>\n"
        f"Описание: <b>{description}</b>\n"
        f"Баллы: <b>{points}</b>"
    )

    for admin_id in LEADERSHIP_IDS:
        try:
            await bot.send_message(
                admin_id, 
                notification_text, 
                parse_mode="HTML",
                reply_markup=get_pending_achievement_keyboard(achievement_id)
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление о индивидуальном достижении админу {admin_id}: {e}")


# --- Команды для руководства ---
@achievements_router.message(Command("pending_achievements"))
async def show_pending_achievements(message: Message):
    """Показывает список индивидуальных достижений, ожидающих подтверждения."""
    if not is_leadership(message.from_user.id):
        return

    pending_list = get_pending_achievements()

    if not pending_list:
        await message.answer("✅ Нет заявок на подтверждение индивидуальных достижений.")
        return

    summary = f"⏳ <b>Заявки на подтверждение ({len(pending_list)}):</b>\n"
    for ach in pending_list:
        summary += (
            "\n--------------------\n"
            f"Студент: <b>{ach['student_name']} ({ach.get('education_level', '')}, {ach.get('course', '')} курс)</b>\n"
            f"Баллы: <b>{ach['points']}</b> ({ach['description']})\n"
            f"Добавил: {ach['reporter_name']} ({ach['reporter_role']})\n"
            f"/approve_{ach['id']} /reject_{ach['id']}"
        )

    await message.answer(summary, parse_mode="HTML")

# --- Обработка Callback-ов от руководства ---
@achievements_router.callback_query(F.data.startswith("ach_approve_"))
async def approve_achievement_callback(callback: CallbackQuery, bot: Bot):
    achievement_id = callback.data.split("_")[-1]
    await process_achievement_decision(callback, bot, achievement_id, "approved")

@achievements_router.callback_query(F.data.startswith("ach_reject_"))
async def reject_achievement_callback(callback: CallbackQuery, bot: Bot):
    achievement_id = callback.data.split("_")[-1]
    await process_achievement_decision(callback, bot, achievement_id, "rejected")
    
async def process_achievement_decision(callback: CallbackQuery, bot: Bot, achievement_id: str, decision: str):
    if not is_leadership(callback.from_user.id):
        await callback.answer("У вас нет прав для этого действия.", show_alert=True)
        return

    achievement = get_achievement(achievement_id)
    if not achievement or achievement["status"] != "pending":
        await callback.message.edit_text("<i>Заявка не найдена или уже была обработана.</i>", parse_mode="HTML")
        await callback.answer()
        return

    approver_id = callback.from_user.id
    approver_name = callback.from_user.full_name

    update_achievement_status(
        achievement_id=achievement_id, 
        status=decision, 
        approver_id=approver_id, 
        approver_name=approver_name
    )
    
    decision_text = "✅ Одобрена" if decision == "approved" else "❌ Отклонена"

    # Use achievement details in the edited message
    original_text = callback.message.text
    if "\n\n--- " not in original_text:
        updated_text = (
            f"{original_text}\n\n"
            f"--- <b>{decision_text}</b> пользователем {approver_name} --- "
        )
        await callback.message.edit_text(updated_text, parse_mode="HTML", reply_markup=None)
    
    reporter_notification = (
        f"🔔 <b>Ваша заявка на индивидуальное достижение была обработана.</b>\n\n"
        f"Студент: <b>{achievement.get('student_name', 'N/A')}</b>\n"
        f"Статус: <b>{decision_text}</b>\n"
        f"Обработал: <b>{approver_name}</b>"
    )
    
    try:
        await bot.send_message(achievement['reporter_id'], reporter_notification, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление автору заявки {achievement['reporter_id']}: {e}")

    await callback.answer(f"Заявка была {decision.replace('ed', 'ена')}")
