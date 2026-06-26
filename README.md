# 🤖 بوت سكني - Sakani Bot

بوت ذكي ومتقدم مخصص لمراقبة وقنص الأراضي السكنية المطروحة على موقع سكني (sakani.sa) وحجزها بشكل فوري وآمن. يتميز البوت بالسرعة الفائقة والذكاء في تلافي حجز القطع القديمة واستهداف القطع الجديدة فور نزولها.

---

## ⚡ الميزات الأساسية:
- **تحميل سريع خارق (Eager Load):** تحميل الصفحة بدون انتظار الصور والوسائط الثقيلة لكسب أجزاء من الثانية.
- **تجنب التكرار الذكي (Smart Action Flags):** تنفيذ أوامر "عرض الوحدات" و "القائمة" لمرة واحدة لكل تحديث.
- **استراتيجية الترصد والمقارنة (Delta Strategy):** مسح أولي وتلقائي للمخطط لتسجيل القطع القديمة وتجاهلها تماماً، والتأهب لقنص أي قطعة جديدة تنزل فوراً.
- **التحديث التلقائي الفوري:** تحديث سريع جداً كل نصف ثانية (أو حسب رغبتك) لالتقاط الطروحات فور حدوثها.
- **لوحة تحكم تفاعلية على Telegram:** رسالة تحكم واحدة محدثة دورياً تعرض السجلات والعد التنازلي وحالة الحجز لتجنب إرسال رسائل سبام.
- **دعم كامل للتنبيهات الحية (`/watch`):** مراقبة التنبيهات والرسائل داخل حسابك بمجرد وصول تنبيه، ينتقل البوت تلقائياً لصفحة الحجز.

---

## 📁 محتويات المشروع:
1. `sakanibot.py`: البرنامج الرئيسي للبوت.
2. `config_example.py`: ملف إعدادات تجريبي يوضح المتغيرات المطلوبة.
3. `requirements_bot.txt`: المكتبات المطلوبة للتشغيل.
4. `.gitignore`: ملف لمنع رفع ملفات الإعدادات الحساسة والسجلات لـ GitHub.

---

## 🚀 طريقة التشغيل والتهيئة (في 5 دقائق):

### الخطوة 1️⃣: تهيئة ملف الإعدادات
1. قم بإنشاء نسخة من الملف `config_example.py` وأعد تسميتها لتصبح `config.py`.
2. افتح الملف `config.py` واكتب بياناتك الأساسية فيه:
   - `TELEGRAM_BOT_TOKEN`: توكن البوت الخاص بك من BotFather.
   - `SAKANI_EMAIL` & `SAKANI_PASSWORD`: بيانات تسجيل الدخول لحسابك في سكني.
   - `PHONE_NUMBER`: رقم جوالك لتلقي إشعارات OTP وتأكيد العمليات.

### الخطوة 2️⃣: تثبيت المتطلبات
افتح موجه الأوامر (Command Prompt / Terminal) واذهب لمسار المشروع:
```bash
cd path/to/SakaniBot
```
ثم قم بتثبيت المكتبات المطلوبة:
```bash
pip install -r requirements_bot.txt
```

### الخطوة 3️⃣: تشغيل البوت
قم بتشغيل البرنامج:
```bash
python sakanibot.py
```

### الخطوة 4️⃣: بدء استخدام البوت في تليجرام
اذهب إلى البوت الخاص بك في تليجرام وأرسل الأمر التالي:
- `/start` للترحيب وبدء التشغيل.
- `/watch` لمراقبة التنبيهات والرسائل تلقائياً.
- `/snipe` لبدء عملية قنص مباشرة على رابط مخطط محدد.

---

## ⚠️ تنويه أمني:
* **لا تقم بمشاركة ملف `config.py`** أو رفعه علناً على GitHub، لأنه يحتوي على معلوماتك الشخصية الحساسة.
* تم إعداد ملف `.gitignore` لحمايتك ومنع رفع هذا الملف تلقائياً.

---

# 🤖 Sakani Bot - English Summary

Advanced automation and sniping bot for residential land plots on the Saudi Sakani platform (sakani.sa).

### Features:
- **Eager Page Loading:** Faster scraping by skipping heavy images and assets.
- **Smart Camping (Delta Strategy):** Automatically records and ignores existing plots upon launch, aggressively targeting new drops.
- **Live Telegram Dashboard:** Keep track of countdown, logs, and actions via a single live-updating message.
- **Watcher Mode:** Scans account notifications and auto-navigates to newly announced projects instantly.

### Quick Start:
1. Rename `config_example.py` to `config.py` and fill in your credentials.
2. Install requirements: `pip install -r requirements_bot.txt`
3. Run the bot: `python sakanibot.py`
4. Interact via Telegram commands (`/start`, `/watch`, `/snipe`).
