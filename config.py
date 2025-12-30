
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Токены
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS")
ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_IDS_STR.split(',')] if ADMIN_IDS_STR else []


if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")

if not ADMIN_IDS:
    print("⚠️ ADMIN_IDS не найден в .env! Админ-панель будет недоступна.")


# Папки и файлы
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

STATS_FILE = DATA_DIR / "user_stats.json"
APPEALS_FILE = DATA_DIR / "appeals.json"

# Контент
NEWS_TEXT = """📰 <b>НОВОСТЬ ОТ СТУДСОВЕТА ФГУ!</b>

🎉 <i>С Новым 2026 годом!</i>

Дорогие студенты!

Студсовет поздравляет вас с наступающим Новым годом!
Желаем успехов в учебе, ярких впечатлений и новых достижений!

📅 <i>Каникулы: 28 декабря - 12 января</i>
📚 <i>Расписание на январь - на сайте ФГУ</i>

#студсовет #ФГУ #новости"""
