from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import logging
from config import ADMIN_IDS
from utils.database import (
    get_admin_appeals_summary, 
    get_appeal, 
    get_appeal_by_message_id,
    answer_appeal
)
from utils.keyboards import get_cancel_keyboard

admin_router = Router()
logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    waiting_for_reply = State()


@admin_router.message(Command("appeals"))
async def admin_appeals_handler(message: Message):
    """Список обращений"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        summary = get_admin_appeals_summary()
        await message.answer(summary, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка получения обращений: {e}")
        await message.answer("❌ Ошибка получения обращений")

@admin_router.message(F.text.regexp(r'^/view_\d{4}$'))
async def admin_view_appeal_handler(message: Message):
    """Просмотр обращения"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    appeal_id = message.text.split('_')[1]
    appeal = get_appeal(appeal_id)
    
    if not appeal:
        await message.answer(f"❌ Обращение #{appeal_id} не найдено")
        return
    
    status_emoji = "📥" if appeal["status"] == "new" else "✅"
    
    text = f"""{status_emoji} <b>Обращение #{appeal_id}</b>

👤 <b>От:</b> {appeal['first_name']}"""
    
    if appeal.get('username'):
        text += f" (@{appeal['username']})"
    
    text += f"""

📝 <b>Текст:</b>
{appeal['text'] if appeal['text'] else '<i>без текста</i>'}"""
    
    if appeal.get('media_type'):
        if appeal['media_type'] == 'media_group':
            photo_ids = appeal['media_id'].split(',')
            text += f"\n📎 <b>Медиа:</b> альбом ({len(photo_ids)} фото)"
        else:
            text += f"\n📎 <b>Медиа:</b> {appeal['media_type']}"
    
    text += f"""

📅 <b>Дата:</b> {datetime.fromisoformat(appeal['created_at']).strftime('%d.%m.%Y %H:%M')}
📊 <b>Статус:</b> {appeal['status']}"""
    
    if appeal['status'] == 'answered':
        text += f"""

💬 <b>Ответ:</b>
{appeal['answer'] if appeal['answer'] else '<i>без текста</i>'}"""
        
        if appeal.get('answer_media_type'):
            text += f"\n📎 <b>Ответ медиа:</b> {appeal['answer_media_type']}"
        
        text += f"\n\n🕐 <b>Отвечено:</b> {datetime.fromisoformat(appeal['answered_at']).strftime('%d.%m.%Y %H:%M')}"
    else:
        text += f"\n\n<b>Ответить:</b> /reply_{appeal_id}"
    
    # Отправляем с медиа если есть
    bot: Bot = message.bot
    media_type = appeal.get('media_type')
    media_id = appeal.get('media_id')
    
    # Если это альбом фотографий
    if media_type == "media_group" and media_id:
        photo_ids = media_id.split(',')
        media_group = []
        
        for idx, photo_id in enumerate(photo_ids):
            if idx == 0:
                media_group.append(InputMediaPhoto(media=photo_id, caption=text, parse_mode="HTML"))
            else:
                media_group.append(InputMediaPhoto(media=photo_id))
        
        await bot.send_media_group(message.chat.id, media_group)
    elif media_type == "photo":
        await bot.send_photo(message.chat.id, media_id, caption=text, parse_mode="HTML")
    elif media_type == "sticker":
        await bot.send_sticker(message.chat.id, media_id)
        await message.answer(text, parse_mode="HTML")
    elif media_type == "animation":
        await bot.send_animation(message.chat.id, media_id, caption=text, parse_mode="HTML")
    elif media_type == "video":
        await bot.send_video(message.chat.id, media_id, caption=text, parse_mode="HTML")
    elif media_type == "document":
        await bot.send_document(message.chat.id, media_id, caption=text, parse_mode="HTML")
    elif media_type == "voice":
        await bot.send_voice(message.chat.id, media_id, caption=text, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")


@admin_router.message(F.text.regexp(r'^/reply_\d{4}$'))
async def admin_start_reply_handler(message: Message, state: FSMContext):
    """Начало ответа через команду"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    appeal_id = message.text.split('_')[1]
    appeal = get_appeal(appeal_id)
    
    if not appeal:
        await message.answer(f"❌ Обращение #{appeal_id} не найдено")
        return
    
    await state.set_state(AdminStates.waiting_for_reply)
    await state.update_data(appeal_id=appeal_id)
    
    reply_text = f"💬 <b>Ответ на обращение #{appeal_id}</b>\n\n"
    reply_text += f"<b>Вопрос:</b>\n{appeal['text'] if appeal['text'] else '<i>без текста</i>'}\n\n"
    
    if appeal.get('media_type'):
        reply_text += f"📎 <i>К вопросу прикреплено: {appeal['media_type']}</i>\n\n"
    
    reply_text += "Напишите ваш ответ.\n"
    reply_text += "Вы можете отправить текст, фото, гифку, стикер или видео."
    
    await message.answer(
        reply_text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


# НОВОЕ: Обработка ответа через Reply на сообщение
@admin_router.message(F.reply_to_message)
async def admin_reply_to_message_handler(message: Message, state: FSMContext):
    """Ответ через Reply на сообщение обращения"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # Ищем обращение по message_id
    result = get_appeal_by_message_id(message.reply_to_message.message_id)
    
    if not result:
        # Это не ответ на обращение, пропускаем
        return
    
    appeal_id, appeal = result
    
    # Определяем тип медиа в ответе
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
    
    # Сохраняем ответ
    answer_appeal(appeal_id, text, media_type, media_id)
    
    # Отправляем пользователю
    try:
        bot: Bot = message.bot
        user_text = f"""💬 <b>Ответ от студсовета ФГУ</b>
<b>Заявление #{appeal_id}</b>

<b>Ваш вопрос:</b>
{appeal['text'] if appeal['text'] else '<i>без текста</i>'}

<b>Ответ:</b>
{text if text else '<i>без текста</i>'}

━━━━━━━━━━━━━━━━
<i>Если у вас есть еще вопросы, используйте кнопку "💬 Анонимное обращение"</i>"""
        
        # Отправляем с медиа если есть
        if media_type == "photo":
            await bot.send_photo(appeal['user_id'], media_id, caption=user_text, 
                               parse_mode="HTML")
        elif media_type == "sticker":
            await bot.send_sticker(appeal['user_id'], media_id)
            await bot.send_message(appeal['user_id'], user_text, parse_mode="HTML")
        elif media_type == "animation":
            await bot.send_animation(appeal['user_id'], media_id, caption=user_text,
                                   parse_mode="HTML")
        elif media_type == "video":
            await bot.send_video(appeal['user_id'], media_id, caption=user_text,
                               parse_mode="HTML")
        elif media_type == "document":
            await bot.send_document(appeal['user_id'], media_id, caption=user_text,
                                  parse_mode="HTML")
        elif media_type == "voice":
            await bot.send_voice(appeal['user_id'], media_id, caption=user_text,
                               parse_mode="HTML")
        else:
            await bot.send_message(appeal['user_id'], user_text, parse_mode="HTML")
        
        await message.answer(
            f"✅ <b>Ответ на обращение #{appeal_id} отправлен!</b>",
            parse_mode="HTML"
        )
        logger.info(f"Отправлен ответ на обращение #{appeal_id} (через reply)")
        
    except Exception as e:
        logger.error(f"Ошибка отправки ответа: {e}")
        await message.answer("❌ Ошибка отправки ответа")


@admin_router.message(AdminStates.waiting_for_reply, F.text == "❌ Отменить")
async def admin_cancel_reply_handler(message: Message, state: FSMContext):
    """Отмена ответа"""
    await state.clear()
    await message.answer("❌ Ответ отменен", reply_markup=ReplyKeyboardRemove())


@admin_router.message(AdminStates.waiting_for_reply)
async def admin_process_reply_handler(message: Message, state: FSMContext):
    """Обработка ответа через команду"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    data = await state.get_data()
    appeal_id = data.get("appeal_id")
    
    appeal = get_appeal(appeal_id)
    if not appeal:
        await message.answer("❌ Обращение не найдено")
        await state.clear()
        return
    
    # Определяем тип медиа в ответе
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
    
    # Сохраняем ответ
    answer_appeal(appeal_id, text, media_type, media_id)
    
    # Отправляем пользователю
    try:
        bot: Bot = message.bot
        user_text = f"""💬 <b>Ответ от студсовета ФГУ</b>
<b>Заявление #{appeal_id}</b>

<b>Ваш вопрос:</b>
{appeal['text'] if appeal['text'] else '<i>без текста</i>'}

<b>Ответ:</b>
{text if text else '<i>без текста</i>'}

━━━━━━━━━━━━━━━━
<i>Если у вас есть еще вопросы, используйте кнопку "💬 Анонимное обращение"</i>"""
        
        # Отправляем с медиа если есть
        if media_type == "photo":
            await bot.send_photo(appeal['user_id'], media_id, caption=user_text, 
                               parse_mode="HTML")
        elif media_type == "sticker":
            await bot.send_sticker(appeal['user_id'], media_id)
            await bot.send_message(appeal['user_id'], user_text, parse_mode="HTML")
        elif media_type == "animation":
            await bot.send_animation(appeal['user_id'], media_id, caption=user_text,
                                   parse_mode="HTML")
        elif media_type == "video":
            await bot.send_video(appeal['user_id'], media_id, caption=user_text,
                               parse_mode="HTML")
        elif media_type == "document":
            await bot.send_document(appeal['user_id'], media_id, caption=user_text,
                                  parse_mode="HTML")
        elif media_type == "voice":
            await bot.send_voice(appeal['user_id'], media_id, caption=user_text,
                               parse_mode="HTML")
        else:
            await bot.send_message(appeal['user_id'], user_text, parse_mode="HTML")
        
        await message.answer(
            f"✅ <b>Ответ на обращение #{appeal_id} отправлен!</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"Отправлен ответ на обращение #{appeal_id}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки ответа: {e}")
        await message.answer("❌ Ошибка отправки ответа",
                           reply_markup=ReplyKeyboardRemove())
    
    await state.clear()