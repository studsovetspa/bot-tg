import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

# Токены
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")

def get_ids_from_env(key: str) -> List[int]:
    """Получает список ID из переменной окружения."""
    ids_str = os.getenv(key)
    if not ids_str:
        return []
    return [int(admin_id) for admin_id in ids_str.split(',') if admin_id]

# Роли
ROLES: Dict[str, List[int]] = {
    # Председатель
    "chairman": get_ids_from_env("CHAIRMAN_IDS"),
    # Заместитель председателя
    "deputy_chairman": get_ids_from_env("DEPUTY_CHAIRMAN_IDS"),
    # Ответственный секретарь
    "secretary": get_ids_from_env("SECRETARY_IDS"),
    # Руководитель Информационного отдела
    "info_head": get_ids_from_env("INFO_HEAD_IDS"),
    "info_deputy": get_ids_from_env("INFO_DEPUTY_IDS"),
    # Руководитель Культурного отдела
    "culture_head": get_ids_from_env("CULTURE_HEAD_IDS"),
    "culture_deputy": get_ids_from_env("CULTURE_DEPUTY_IDS"),
    # Руководитель Научного отдела
    "science_head": get_ids_from_env("SCIENCE_HEAD_IDS"),
    "science_deputy": get_ids_from_env("SCIENCE_DEPUTY_IDS"),
    # Руководитель Волонтёрского отдела
    "volunteer_head": get_ids_from_env("VOLUNTEER_HEAD_IDS"),
    "volunteer_deputy": get_ids_from_env("VOLUNTEER_DEPUTY_IDS"),
    # Руководитель Международного отдела
    "international_head": get_ids_from_env("INTERNATIONAL_HEAD_IDS"),
    "international_deputy": get_ids_from_env("INTERNATIONAL_DEPUTY_IDS"),
    # Заведующий Комитетом по быту
    "social_head": get_ids_from_env("SOCIAL_HEAD_IDS"),
    "social_deputy": get_ids_from_env("SOCIAL_DEPUTY_IDS"),
    # Заведующий Комитетом по образованию
    "education_head": get_ids_from_env("EDUCATION_HEAD_IDS"),
    "education_deputy": get_ids_from_env("EDUCATION_DEPUTY_IDS"),
    # Заведующий Комитетом по спорту
    "sport_head": get_ids_from_env("SPORT_HEAD_IDS"),
    "sport_deputy": get_ids_from_env("SPORT_DEPUTY_IDS"),
    # Заведующий Комитетом по работе со спонсорами
    "sponsors_head": get_ids_from_env("SPONSORS_HEAD_IDS"),
    "sponsors_deputy": get_ids_from_env("SPONSORS_DEPUTY_IDS"),
    # Заведующий Комитетом по Межфакультетским связям
    "interfaculty_head": get_ids_from_env("INTERFACULTY_HEAD_IDS"),
    "interfaculty_deputy": get_ids_from_env("INTERFACULTY_DEPUTY_IDS"),
    # Заведующий Комитетом по цифровому развитию и техническому обеспечению
    "tech_head": get_ids_from_env("TECH_HEAD_IDS"),
    "tech_deputy": get_ids_from_env("TECH_DEPUTY_IDS"),
}

# Общий список всех админов
ADMIN_IDS = sorted(list(set(id for role_ids in ROLES.values() for id in role_ids)))

# Определение ролей руководства
LEADERSHIP_ROLES = ["chairman", "deputy_chairman", "secretary"]
LEADERSHIP_IDS = sorted(list(set(id for role in LEADERSHIP_ROLES for id in ROLES[role])))

if not ADMIN_IDS:
    print("⚠️ Ни один ID администратора не найден в .env! Админ-панель будет недоступна.")

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом."""
    return user_id in ADMIN_IDS

def is_leadership(user_id: int) -> bool:
    """Проверяет, является ли пользователь руководством."""
    return user_id in LEADERSHIP_IDS

def get_role_name(user_id: int) -> str:
    """Возвращает название роли пользователя."""
    for role, ids in ROLES.items():
        if user_id in ids:
            # This is a simple implementation, you might want to map role keys to human-readable names
            return role.replace('_', ' ').title()
    return "User"

# Папки и файлы
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

STATS_FILE = DATA_DIR / "user_stats.json"
APPEALS_FILE = DATA_DIR / "appeals.json"
ACHIEVEMENTS_FILE = DATA_DIR / "achievements.json"

# Контент
NEWS_TEXT = """📰 <b>НОВОСТЬ ОТ СТУДСОВЕТА ФГУ!</b>

🎉 <i>С Новым 2026 годом!</i>

Дорогие студенты!

Студсовет поздравляет вас с наступающим Новым годом!
Желаем успехов в учебе, ярких впечатлений и новых достижений!

📅 <i>Каникулы: 28 декабря - 12 января</i>
📚 <i>Расписание на январь - на сайте ФГУ</i>

#студсовет #ФГУ #новости"""
