"""
ملف إعدادات تجريبي - يدعم قراءة المتغيرات البيئية عند الرفع على السيرفرات السحابية
"""
import os

# توكن البوت
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7137834336:AAE5s539SqdkEefOPqa59ekaBXStnKwsfbc")

# بيانات الدخول لحساب سكني
SAKANI_EMAIL = os.environ.get("SAKANI_EMAIL", "")
SAKANI_PASSWORD = os.environ.get("SAKANI_PASSWORD", "")
NATIONAL_ID = os.environ.get("NATIONAL_ID", "")
PHONE_NUMBER = os.environ.get("PHONE_NUMBER", "+966565614370")

ALLOWED_USER_IDS = []
allowed_ids_str = os.environ.get("ALLOWED_USER_IDS")
if allowed_ids_str:
    try:
        ALLOWED_USER_IDS = [int(x.strip()) for x in allowed_ids_str.split(",")]
    except:
        pass

# إعدادات التشغيل التلقائي
TARGET_URL = os.environ.get("TARGET_URL", "")
TARGET_TIME = os.environ.get("TARGET_TIME", "now")

auto_chat_id = os.environ.get("AUTO_START_CHAT_ID")
AUTO_START_CHAT_ID = int(auto_chat_id) if auto_chat_id else 1538283246

BOT_NAME = "بوت سكني"
BOT_DESCRIPTION = "بوت يراقب الأراضي والعقارات على موقع سكني"

DATABASE_FILE = "sakani_data.json"
RESULTS_FILE = "sakani_results.json"

DEFAULT_INTERVAL = 1.0
FAST_POLLING_INTERVAL = 0.1
WAIT_BEFORE_START_SECONDS = 60

# فترات التحديث المخصصة
try:
    REFRESH_GAP_DROP = float(os.environ.get("REFRESH_GAP_DROP", 0.3))
    REFRESH_GAP_SEARCH = float(os.environ.get("REFRESH_GAP_SEARCH", 1.0))
except:
    REFRESH_GAP_DROP = 0.3
    REFRESH_GAP_SEARCH = 1.0

class SessionState:
    INITIALIZING = "INITIALIZING 🔄"
    IDLE = "IDLE 💤"
    COUNTDOWN = "COUNTDOWN ⏳"
    ATTACK_MODE = "ATTACK 🔥"
    LOCKED = "LOCKED 🔒"
    OTP_REQUIRED = "OTP 🔑"
    SECURED = "SECURED 🏆"
    TERMINATED = "TERMINATED 💀"
    SETUP = "SETUP ⚙️"
    WATCHING = "WATCHING 📡"

from dataclasses import dataclass

@dataclass
class Unit:
    element: object
    price: int
    area: int
    text: str
    score: int = 0

FILTERS = {
    'enabled': False,
    'max_price': 0,
    'min_area': 100,
    'preferred_block': "",
}

REQUEST_TIMEOUT = 30
REQUEST_RETRY_COUNT = 3
REQUEST_RETRY_DELAY = 5

LOG_FILE = "sakani_bot.log"
LOG_LEVEL = "INFO"
