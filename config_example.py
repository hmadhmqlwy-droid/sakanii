"""
ملف إعدادات تجريبي - يرجى نسخه وتسميته config.py وتعبئة بياناتك فيه
"""

TELEGRAM_BOT_TOKEN = "ضع_توكن_البوت_هنا"

# بيانات الدخول
SAKANI_EMAIL = "ضع_الهوية_أو_الإيميل_هنا"
SAKANI_PASSWORD = "ضع_كلمة_المرور_هنا"
NATIONAL_ID = "رقم_الهوية"
PHONE_NUMBER = "+966xxxxxxxx"

ALLOWED_USER_IDS = []

# إعدادات التشغيل التلقائي
TARGET_URL = ""
TARGET_TIME = "now"
AUTO_START_CHAT_ID = 0

BOT_NAME = "بوت سكني"
BOT_DESCRIPTION = "بوت يراقب الأراضي والعقارات على موقع سكني"

DATABASE_FILE = "sakani_data.json"
RESULTS_FILE = "sakani_results.json"

DEFAULT_INTERVAL = 1.0
FAST_POLLING_INTERVAL = 0.1
WAIT_BEFORE_START_SECONDS = 60
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
