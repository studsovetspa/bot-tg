import json
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Импортируем после определения logger
from config import STATS_FILE, APPEALS_FILE


# === Статистика ===

def load_stats() -> Dict:
    """Загружает статистику"""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки статистики: {e}")
            return {}
    return {}


def save_stats(stats: Dict) -> None:
    """Сохраняет статистику"""
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")


def update_user_stats(user_id: int, username: Optional[str] = None, 
                     first_name: Optional[str] = None) -> None:
    """Обновляет статистику пользователя"""
    stats = load_stats()
    user_key = str(user_id)
    
    if user_key not in stats:
        stats[user_key] = {
            "first_name": first_name or "Неизвестно",
            "username": username,
            "messages_count": 0,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
    
    stats[user_key]["messages_count"] += 1
    stats[user_key]["last_seen"] = datetime.now().isoformat()
    
    save_stats(stats)


def get_stats_summary() -> str:
    """Возвращает сводку статистики"""
    stats = load_stats()
    total_users = len(stats)
    total_messages = sum(u["messages_count"] for u in stats.values())
    
    now = datetime.now()
    active_users = sum(
        1 for u in stats.values() 
        if (now - datetime.fromisoformat(u["last_seen"])).days <= 7
    )
    
    top_users = sorted(
        stats.items(), 
        key=lambda x: x[1]["messages_count"], 
        reverse=True
    )[:5]
    
    summary = f"""<b>📊 Статистика бота</b>

👥 Всего пользователей: <b>{total_users}</b>
💬 Всего сообщений: <b>{total_messages}</b>
🔥 Активных за неделю: <b>{active_users}</b>

<b>🏆 Топ-5 активных:</b>"""
    
    for i, (user_id, data) in enumerate(top_users, 1):
        username = f"@{data['username']}" if data.get('username') else ""
        summary += f"\n{i}. <b>{data['first_name']}</b> {username} — {data['messages_count']} сообщений"
    
    return summary


# === Обращения ===

def load_appeals() -> Dict:
    """Загружает обращения"""
    if APPEALS_FILE.exists():
        try:
            with open(APPEALS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки обращений: {e}")
            return {}
    return {}


def save_appeals(appeals: Dict) -> None:
    """Сохраняет обращения"""
    try:
        with open(APPEALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(appeals, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения обращений: {e}")


def create_appeal(user_id: int, username: Optional[str], 
                 first_name: str, text: str, media_type: str = None,
                 media_id: str = None) -> str:
    """Создает новое обращение с поддержкой медиа"""
    appeals = load_appeals()
    appeal_id = str(len(appeals) + 1).zfill(4)
    
    appeals[appeal_id] = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "text": text or "",
        "media_type": media_type,
        "media_id": media_id,
        "admin_message_ids": {},  # Будет установлен после отправки админам
        "created_at": datetime.now().isoformat(),
        "status": "new",
        "answer": None,
        "answer_media_type": None,
        "answer_media_id": None,
        "answered_at": None
    }
    
    save_appeals(appeals)
    return appeal_id


def get_appeal(appeal_id: str) -> Optional[Dict]:
    """Получает обращение по ID"""
    appeals = load_appeals()
    return appeals.get(appeal_id)


def get_appeal_by_message_id(message_id: int) -> Optional[tuple]:
    """Получает обращение по message_id (для reply)"""
    appeals = load_appeals()
    for appeal_id, appeal in appeals.items():
        # Для обратной совместимости со старой версией
        if appeal.get("admin_message_id") == message_id:
            return appeal_id, appeal
        # Новый формат с несколькими админами
        if "admin_message_ids" in appeal:
            for admin_id, msg_id in appeal["admin_message_ids"].items():
                if msg_id == message_id:
                    return appeal_id, appeal
    return None


def answer_appeal(appeal_id: str, answer_text: str, 
                 media_type: str = None, media_id: str = None) -> bool:
    """Отвечает на обращение с поддержкой медиа"""
    appeals = load_appeals()
    
    if appeal_id not in appeals:
        return False
    
    appeals[appeal_id]["status"] = "answered"
    appeals[appeal_id]["answer"] = answer_text or ""
    appeals[appeal_id]["answer_media_type"] = media_type
    appeals[appeal_id]["answer_media_id"] = media_id
    appeals[appeal_id]["answered_at"] = datetime.now().isoformat()
    
    save_appeals(appeals)
    return True


def get_admin_appeals_summary() -> str:
    """Сводка по обращениям для админа"""
    appeals = load_appeals()
    
    new_count = sum(1 for a in appeals.values() if a["status"] == "new")
    answered_count = sum(1 for a in appeals.values() if a["status"] == "answered")
    
    summary = f"""<b>📬 Обращения</b>

📥 Новых: <b>{new_count}</b>
✅ Отвеченных: <b>{answered_count}</b>
📊 Всего: <b>{len(appeals)}</b>"""
    
    if new_count > 0:
        summary += "\n\n<b>Новые обращения:</b>"
        new_appeals = [(aid, a) for aid, a in appeals.items() if a["status"] == "new"]
        new_appeals.sort(key=lambda x: x[1]["created_at"], reverse=True)
        
        for appeal_id, appeal in new_appeals[:5]:
            text_preview = appeal["text"][:50]
            if len(appeal["text"]) > 50:
                text_preview += "..."
            
            # Добавляем информацию об альбоме
            media_info = ""
            if appeal.get('media_type') == 'media_group' and appeal.get('media_id'):
                photo_count = len(appeal['media_id'].split(','))
                media_info = f" 📷×{photo_count}"
            elif appeal.get('media_type'):
                media_info = f" 📎"
            
            summary += f"\n\n<b>#{appeal_id}</b>{media_info} от {appeal['first_name']}"
            summary += f"\n<i>{text_preview}</i>"
            summary += f"\n/view_{appeal_id} /reply_{appeal_id}"
    
    return summary