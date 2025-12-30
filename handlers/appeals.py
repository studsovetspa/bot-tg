from aiogram import Router, F, Bot
from aiogram.types import Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import logging
import asyncio
from config import ADMIN_IDS
from utils.database import update_user_stats, create_appeal
from utils.keyboards import get_main_menu, get_cancel_keyboard

appeals_router = Router()
logger = logging.getLogger(__name__)


class AppealStates(StatesGroup):
    waiting_for_appeal = State()


# Хранилище для медиа-групп (альбомов)
media_groups = {}
# Задачи для обработки групп
processing_tasks = {}


@appeals_router.message(F.text == "💬 Анонимное обращение")
async def start_appeal_handler(message: Message, state: FSMContext):
    """Начало создания обращения"""
    update_user_stats(message.from_user.id, message.from_user.username,
                     message.from_user.first_name)
    
    await state.set_state(AppealStates.waiting_for_appeal)
    await message.answer(
        "💬 <b>Анонимное обращение</b>\n\n"
        "Напишите ваш вопрос или обращение.\n"
        "Вы можете отправить:\n"
        "• 📝 Текст\n"
        "• 📷 Фото (можно несколько)\n"
        "• 🎬 Гифку\n"
        "• 🎭 Стикер\n"
        "• 🎥 Видео\n"
        "• 📄 Документ\n\n"
        "Сообщение будет отправлено студсовету анонимно.\n\n"
        "<i>Для отмены нажмите кнопку ниже</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@appeals_router.message(AppealStates.waiting_for_appeal, F.text == "❌ Отменить")
async def cancel_appeal_handler(message: Message, state: FSMContext):
    """Отмена обращения"""
    await state.clear()
    await message.answer("❌ Обращение отменено", reply_markup=get_main_menu())


async def process_media_group(media_group_id: str):
    """Обработка медиа-группы после сбора всех сообщений"""
    await asyncio.sleep(0.5)  # Ждем, пока все фото соберутся
    
    if media_group_id not in media_groups:
        return
    
    group_data = media_groups[media_group_id]
    messages = sorted(group_data["messages"], key=lambda m: m.message_id)
    user = group_data["user"]
    state = group_data["state"]
    
    # Если уже обработано, пропускаем
    if group_data.get("processed"):
        return
    
    group_data["processed"] = True
    
    # Берем текст из первого сообщения с caption
    text = ""
    for msg in messages:
        if msg.caption:
            text = msg.caption
            break
    
    # Собираем все file_id фотографий
    photo_ids = []
    for msg in messages:
        if msg.photo:
            photo_ids.append(msg.photo[-1].file_id)
    
    # Создаем обращение (сохраняем все photo_ids как строку)
    appeal_id = create_appeal(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        text=text,
        media_type="media_group",
        media_id=",".join(photo_ids)  # Сохраняем все ID через запятую
    )
    
    await state.clear()
    
    # Уведомляем пользователя
    await messages[0].answer(
        f"✅ <b>Обращение #{appeal_id} отправлено!</b>\n\n"
        "Студсовет получит ваше сообщение анонимно.\n"
        "Ответ придет в этот чат.",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )
    
    # Отправляем админам альбом
    if ADMIN_IDS:
        try:
            bot: Bot = messages[0].bot
            
            # Формируем медиа-группу для отправки
            media_group_to_send = []
            admin_text = f"""📬 <b>Новое анонимное обращение #{appeal_id}</b>

📝 <b>Текст:</b>
{text if text else "<i>без текста</i>"}

━━━━━━━━━━━━━━━━
<i>Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>

Ответьте на это сообщение или используйте:
/reply_{appeal_id}"""
            
            for idx, photo_id in enumerate(photo_ids):
                if idx == 0:
                    # Первое фото с текстом
                    media_group_to_send.append(
                        InputMediaPhoto(media=photo_id, caption=admin_text, parse_mode="HTML")
                    )
                else:
                    # Остальные фото без текста
                    media_group_to_send.append(InputMediaPhoto(media=photo_id))
            
            # Отправляем группу всем админам
            for admin_id in ADMIN_IDS:
                try:
                    sent_messages = await bot.send_media_group(admin_id, media_group_to_send)
                    logger.info(f"Обращение #{appeal_id} (альбом из {len(photo_ids)} фото) отправлено админу {admin_id}")

                    # Сохраняем message_id первого сообщения для reply
                    if sent_messages:
                        from utils.database import load_appeals, save_appeals
                        appeals_data = load_appeals()
                        # У каждого админа будет свой message_id для ответа
                        if "admin_message_ids" not in appeals_data[appeal_id]:
                            appeals_data[appeal_id]["admin_message_ids"] = {}
                        appeals_data[appeal_id]["admin_message_ids"][str(admin_id)] = sent_messages[0].message_id
                        save_appeals(appeals_data)

                except Exception as e:
                    logger.error(f"Ошибка отправки обращения админу {admin_id}: {e}")

        except Exception as e:
            logger.error(f"Общая ошибка отправки обращения админам: {e}")
    
    # Очищаем группу через 5 секунд
    await asyncio.sleep(5)
    if media_group_id in media_groups:
        del media_groups[media_group_id]


@appeals_router.message(AppealStates.waiting_for_appeal)
async def process_appeal_handler(message: Message, state: FSMContext):
    """Обработка обращения с медиа"""
    user = message.from_user
    
    # Проверяем, это медиа-группа (альбом)?
    if message.media_group_id:
        # Если это первое сообщение из группы
        if message.media_group_id not in media_groups:
            media_groups[message.media_group_id] = {
                "messages": [],
                "user": user,
                "state": state,
                "processed": False
            }
        
        # Добавляем сообщение в группу
        media_groups[message.media_group_id]["messages"].append(message)
        
        # Отменяем предыдущую задачу если была
        if message.media_group_id in processing_tasks:
            processing_tasks[message.media_group_id].cancel()
        
        # Запускаем новую задачу обработки
        processing_tasks[message.media_group_id] = asyncio.create_task(
            process_media_group(message.media_group_id)
        )
        
        return
    
    # Обычное сообщение (не альбом)
    media_type = None
    media_id = None
    text = message.text or message.caption or ""
    
    if message.photo:
        media_type = "photo"
        media_id = message.photo[-1].file_id
    elif message.sticker:
        media_type = "sticker"
        media_id = message.sticker.file_id
    elif message.animation:
        media_type = "animation"
        media_id = message.animation.file_id
    elif message.video:
        media_type = "video"
        media_id = message.video.file_id
    elif message.document:
        media_type = "document"
        media_id = message.document.file_id
    elif message.voice:
        media_type = "voice"
        media_id = message.voice.file_id
    
    # Создаем обращение
    appeal_id = create_appeal(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        text=text,
        media_type=media_type,
        media_id=media_id
    )
    
    await state.clear()
    
    # Уведомляем пользователя
    await message.answer(
        f"✅ <b>Обращение #{appeal_id} отправлено!</b>\n\n"
        "Студсовет получит ваше сообщение анонимно.\n"
        "Ответ придет в этот чат.",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )
    
    # Отправляем админам
    if ADMIN_IDS:
        bot: Bot = message.bot
        admin_text = f"""📬 <b>Новое анонимное обращение #{appeal_id}</b>

📝 <b>Текст:</b>
{text if text else "<i>без текста</i>"}

━━━━━━━━━━━━━━━━
<i>Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>

Ответьте на это сообщение или используйте:
/reply_{appeal_id}"""

        for admin_id in ADMIN_IDS:
            try:
                # Отправляем с медиа если есть
                admin_msg = None
                if media_type == "photo":
                    admin_msg = await bot.send_photo(admin_id, media_id, caption=admin_text, parse_mode="HTML")
                elif media_type == "sticker":
                    await bot.send_sticker(admin_id, media_id)
                    admin_msg = await bot.send_message(admin_id, admin_text, parse_mode="HTML")
                elif media_type == "animation":
                    admin_msg = await bot.send_animation(admin_id, media_id, caption=admin_text, parse_mode="HTML")
                elif media_type == "video":
                    admin_msg = await bot.send_video(admin_id, media_id, caption=admin_text, parse_mode="HTML")
                elif media_type == "document":
                    admin_msg = await bot.send_document(admin_id, media_id, caption=admin_text, parse_mode="HTML")
                elif media_type == "voice":
                    admin_msg = await bot.send_voice(admin_id, media_id, caption=admin_text, parse_mode="HTML")
                else:
                    admin_msg = await bot.send_message(admin_id, admin_text, parse_mode="HTML")
                
                # Сохраняем message_id для reply
                if admin_msg:
                    from utils.database import load_appeals, save_appeals
                    appeals_data = load_appeals()
                    if "admin_message_ids" not in appeals_data[appeal_id]:
                        appeals_data[appeal_id]["admin_message_ids"] = {}
                    appeals_data[appeal_id]["admin_message_ids"][str(admin_id)] = admin_msg.message_id
                    save_appeals(appeals_data)

                logger.info(f"Обращение #{appeal_id} отправлено админу {admin_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки обращения админу {admin_id}: {e}")
