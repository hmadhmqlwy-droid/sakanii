
import asyncio
import logging
import time
import re  # Fixed: Import re at top level
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Selenium Imports
from selenium import webdriver
# Use Undetected Chromedriver for WAF Bypass
import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# Telegram Imports
try:
    from telegram import Update
    from telegram.ext import (
        Application, 
        CommandHandler, 
        MessageHandler, 
        filters, 
        ContextTypes, 
        ConversationHandler
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

from config import (
    TELEGRAM_BOT_TOKEN,
    LOG_FILE,
    LOG_LEVEL,
    SessionState,
    Unit,
    FAST_POLLING_INTERVAL,
    SAKANI_EMAIL,
    SAKANI_PASSWORD,
    TARGET_URL,
    TARGET_TIME,
    AUTO_START_CHAT_ID,
    NATIONAL_ID,
    PHONE_NUMBER,
    FILTERS,
    REFRESH_GAP_DROP,
    REFRESH_GAP_SEARCH
)

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Selenium Sniper Session ---
class SniperSession:
    def __init__(self, session_id: str, chat_id: int, url: str, target_time: datetime = None):
        self.session_id = session_id
        self.chat_id = chat_id
        self.url = url
        self.target_time = target_time
        self.status = SessionState.INITIALIZING # Fixed: Initial state
        self.driver = None
        self.mode = "SEARCH" # Default: SEARCH or DROP
        self.attempts = 0
        self.logs = []
        self.otp_event = asyncio.Event()
        self.otp_code = None
        self.success_url = None 
        self.dashboard_msg_id = None # ID of the live dashboard message
        
        # Launch Browser Immediately
        self._launch_browser()
        
        # Smart Drop Logic 🧠
        self.ignored_plots = set()
        self.first_scan_done = False
        self.list_view_clicked = False
        self.show_units_clicked = False

    async def update_dashboard(self, app: Application, custom_text: str = None):
        """تحديث لوحة التحكم الحية بدلاً من إرسال رسائل جديدة"""
        # Status Icon & Arabization
        status_text = f"`{self.status}`"
        icon = "⚪"
        
        if self.status == SessionState.IDLE: 
            icon = "💤"
            status_text = "خامل (انتظار)"
        elif self.status == SessionState.COUNTDOWN: 
            icon = "⏳"
            status_text = "العد التنازلي"
        elif self.status == SessionState.ATTACK_MODE: 
            icon = "🔥"
            status_text = "جاري الهجوم!"
        elif self.status == SessionState.LOCKED: 
            icon = "🔒"
            status_text = "تم العثور (قفل الهدف)"
        elif self.status == SessionState.SECURED: 
            icon = "🏆"
            status_text = "تمت العملية بنجاح"
        elif self.status == SessionState.TERMINATED: 
            icon = "☠️"
            status_text = "توقفت"
        
        # Time Display
        rem = int(self.time_remaining_seconds())
        time_str = f"{rem} ثانية" if rem > 0 else "الآن"
        if self.status == SessionState.IDLE and rem > 60:
             time_str = f"{rem//60} دقيقة و {rem%60} ثانية"

        # Build The Dashboard Content (Arabic)
        content = (
            f"🦅 **لوحة تحكم سكاني (النخبة)**\n"
            f"━━━━━━━━━━━━━━\n"
            f"🆔 **المهمة:** `{self.session_id[-4:]}`\n"
            f"⚙️ **الوضع:** `{'⚡ قنص طرح جديد' if self.mode == 'DROP' else '� بحث في الصفحة'}`\n"
            f"�🚦 **الحالة:** {icon} {status_text}\n"
            f"⏲️ **المتبقي:** `{time_str}`\n"
            f"🎯 **الهدف:** [رابط المشروع]({self.url})\n"
            f"━━━━━━━━━━━━━━\n"
        )
        
            
        if custom_text:
            content += f"\n📢 **تنبيه:** {custom_text}\n"
        elif self.logs:
            # Try to translate generic logs if possible or keep as is
            last_log = self.logs[-1]
            content += f"\n📝 **السجل:** `{last_log}`\n"

        try:
            if not self.dashboard_msg_id:
                # First time: Send new message
                msg = await app.bot.send_message(chat_id=self.chat_id, text=content, parse_mode='Markdown', disable_web_page_preview=True)
                self.dashboard_msg_id = msg.message_id
            else:
                # Update existing
                try:
                    await app.bot.edit_message_text(
                        chat_id=self.chat_id, 
                        message_id=self.dashboard_msg_id, 
                        text=content, 
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    # Message likely not modified or too old, ignore common error
                    pass
        except: pass

    def log_event(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.logs.append(entry)
        if len(self.logs) > 50: self.logs.pop(0)

    def _launch_browser(self):
        """تشغيل المتصفح باستخدام undetected-chromedriver لتجاوز الحظر 403"""
        try:
            self.log_event("🖥️ تشغيل المتصفح (وضع التخفي المطلق - UC)...")
            
            # UD-Chrome Options
            options = uc.ChromeOptions()
            options.page_load_strategy = "eager"  # التحميل السريع جداً (لا ينتظر الصور والملفات الخارجية الثقيلة)
            options.add_argument("--start-maximized")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-notifications") # Block web notifications
            
            # Disable Location & Notifications Prompts (As seen in screenshot)
            prefs = {
                "profile.default_content_setting_values.notifications": 2, # 2 = Block
                "profile.default_content_setting_values.geolocation": 2,   # 2 = Block
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
            options.add_experimental_option("prefs", prefs)
            
            # Using uc.Chrome() instead of webdriver.Chrome()
            # use_subprocess=True helps in some environments to keep it distinct
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            
            # الذهاب للرابط فوراً
            self.driver.get(self.url)
            
            # NO Auto-Login. User does it.
            self.log_event("⏳ Waiting for user manual login...")
            self.log_event("✅ المتصفح جاهز.")
            
        except Exception as e:
            self.log_event(f"❌ خطأ تشغيل المتصفح: {e}")
            self.status = SessionState.TERMINATED

    def set_target_time(self, time_str: str):
        now = datetime.now()
        try:
            target = datetime.strptime(time_str, "%H:%M:%S").time()
            self.target_time = datetime.combine(now.date(), target)
            if self.target_time < now:
                self.target_time += timedelta(days=1)
            self.log_event(f"🎯 وقت القنص: {self.target_time.strftime('%H:%M:%S')}")
        except ValueError:
            self.target_time = None

    def time_remaining_seconds(self) -> float:
        if not self.target_time: return 0
        return (self.target_time - datetime.now()).total_seconds()

    def scan_units(self) -> List[Unit]:
        """المسح الشامل وتحويل الـ DOM إلى كائنات Unit"""
        units = []
        driver = self.driver
        # 1. Broad Search
        xpath_btn = "//*[contains(text(), 'حجز') or contains(text(), 'احجز') or contains(text(), 'Book')]"
        try:
            buttons = driver.find_elements(By.XPATH, xpath_btn)
            # LOG DEBUG: Found X buttons
            # self.log_event(f"🔍 Found {len(buttons)} booking buttons.") 
        except: return []

        for btn in buttons:
            if not (btn.is_displayed() and btn.is_enabled()): continue
            
            try:
                # Get Parent Card
                card = btn.find_element(By.XPATH, "./.. | ./../.. | ./../../..")
                text = card.text.replace("\n", " ")
                
                # Parse
                price = 0
                price_match = re.search(r'(\d{1,3}(?:,\d{3})*)', text)
                if price_match: price = int(price_match.group(1).replace(",", ""))
                
                area = 0
                area_match = re.search(r'(\d+)\s*(?:م2|متر|sqm)', text)
                if area_match: area = int(area_match.group(1))
                
                # Create Unit Object
                u = Unit(element=btn, price=price, area=area, text=text)
                units.append(u)
                
                # LOG DETAILS OF FOUND UNIT
                self.log_event(f"🔎 Unit Found: Price={price}, Area={area}, Text={text[:20]}...")
                
            except: continue
            
        return units

    def score_unit(self, unit: Unit) -> int:
        """محرك التقييم (Scoring Engine)"""
        score = 100 
        
        # 0. Check if Filters are Enabled
        # If disabled, we accept EVERYTHING instantly.
        if not FILTERS.get('enabled', True):
            return score

        # Free / Cheap Land Logic 🆓
        max_p = FILTERS.get('max_price', 999999999)
        min_a = FILTERS.get('min_area', 0)
        
        rejection_reason = ""
        
        # 1. Area Filter
        if unit.area < min_a:
             rejection_reason = f"Area {unit.area}<{min_a}"
             
        # 2. Price Filter (Relaxed for 'Free' mode)
        # If max_p is 0 (Admin set strict free), we relax it slightly to 1000 SAR 
        # to catch lands that might be parsed incorrectly as having small value or fees.
        effective_max_p = max_p if max_p > 0 else 1000 
        
        if unit.price > effective_max_p:
             rejection_reason = f"Price {unit.price} > {effective_max_p}"

        # Decision
        if rejection_reason:
            self.log_event(f"⚠️ Ignored: {rejection_reason}")
            return -1 
        
        return score
        
        # 3. Preference Filter
        pref = FILTERS.get('preferred_block', "")
        if pref and pref not in unit.text: return -1
        
        # Bonus Points
        # - Cheap units get more points? 
        # - Larger area gets more points?
        
        return score

    def check_and_act(self) -> bool:
        """
        دورة الحياة:
        ATTACK_MODE -> Scan -> Score -> Select Best -> Disable Other Events -> Click -> LOCKED
        """
        if self.status != SessionState.ATTACK_MODE: return False
        
        self.attempts += 1 # Increment counter
        driver = self.driver
        
        try:
            # 1. Scan
            units = self.scan_units()
            
            # Show "Heartbeat" log every 20 attempts so user knows we are alive
            if self.attempts % 20 == 0:
                self.log_event(f"💓 جاري المسح... (النتائج: {len(units)})")

            if not units:
                # --- PROJECT PAGE LOGIC: Force Show Units -> Switch to List -> Snipe First ---
                try:
                    # 1. Try to switch to "List View" if Map is active (Common in Land projects)
                    if not getattr(self, 'list_view_clicked', False):
                        try:
                            list_view_btn = driver.find_elements(By.XPATH, "//*[contains(@class, 'list') or contains(@class, 'view-list') or contains(text(), 'قائمة')]")
                            for btn in list_view_btn:
                                if btn.is_displayed() and "map" not in btn.get_attribute("class"):
                                    driver.execute_script("arguments[0].click();", btn)
                                    self.list_view_clicked = True
                                    time.sleep(0.3)
                                    break
                        except: pass

                    # 2. Click "Show Units" (عرض الوحدات) - Aggressive Search
                    if not getattr(self, 'show_units_clicked', False):
                        xpath_show = "//*[contains(text(), 'عرض') and contains(text(), 'الوحدات')] | //*[contains(text(), 'Show Units')] | //button[contains(@class, 'btn') and contains(., 'وحدات')]"
                        try:
                            show_btns = driver.find_elements(By.XPATH, xpath_show)
                            for btn in show_btns:
                                if btn.is_displayed():
                                    self.log_event("🖱️ ضغط زر 'عرض الوحدات'...")
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                    time.sleep(0.1)
                                    driver.execute_script("arguments[0].click();", btn)
                                    self.show_units_clicked = True
                                    time.sleep(0.5) # Wait for expansion
                                    break
                        except: pass
                    
                    # 3. SCROLL & SNIPE (The "New Drop" Strategy) ⚡
                    xpath_all_cards = "//*[contains(text(), 'رقم القطعة') or contains(text(), 'أرض')]/ancestor::div[contains(@class, 'card') or contains(@class, 'item') or contains(@class, 'col')]"
                    
                    if not self.first_scan_done:
                        self.log_event("📜 جاري رسم خريطة القطع الحالية وتجاهلها...")
                        # Map initial plots by scrolling down
                        for i in range(5):
                            cards = driver.find_elements(By.XPATH, xpath_all_cards)
                            for c in cards:
                                if c.is_displayed():
                                    try:
                                        txt = c.text
                                        match = re.search(r'[\d]+-[\d]+', txt)
                                        pid = match.group(0) if match else txt[:20].strip()
                                        self.ignored_plots.add(pid)
                                    except: pass
                            driver.execute_script("window.scrollBy(0, 800);")
                            time.sleep(0.2)
                            
                        self.first_scan_done = True
                        self.log_event(f"✅ تم حفظ الخريطة ({len(self.ignored_plots)} قطعة). جاري انتظار الجديد...")
                        return False
                        
                    else:
                        # FAST SCAN: Scan all cards in DOM without scrolling first
                        cards = driver.find_elements(By.XPATH, xpath_all_cards)
                        for c in cards:
                            if c.is_displayed():
                                try:
                                    txt = c.text
                                    match = re.search(r'[\d]+-[\d]+', txt)
                                    pid = match.group(0) if match else txt[:20].strip()
                                    
                                    if pid not in self.ignored_plots:
                                        # FOUND A NEW ONE! 🚨
                                        self.log_event(f"🚨 **قطعة جديدة ظهرت!** ({pid})")
                                        self.status = SessionState.LOCKED
                                        try:
                                            driver.execute_script("arguments[0].style.border='5px solid red'", c)
                                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", c)
                                            time.sleep(0.05)
                                            
                                            # Click Logic
                                            try:
                                                btn = c.find_element(By.XPATH, ".//*[contains(text(), 'حجز') or contains(text(), 'احجز')]")
                                                driver.execute_script("arguments[0].click();", btn)
                                            except:
                                                driver.execute_script("arguments[0].click();", c)
                                        except:
                                            c.click()
                                            
                                        self._handle_post_click_flow()
                                        return True
                                except: pass
                                
                        # No new plots in DOM -> Return False immediately (super fast, no scroll/sleep)
                        return False

                except Exception as e:
                    pass

            # 2. Score
            scored_units = []
            for u in units:
                s = self.score_unit(u)
                if s > 0:
                    u.score = s
                    scored_units.append(u)
            
            # 3. Sort (Best Score First)
            scored_units.sort(key=lambda x: x.score, reverse=True)
            
            if not scored_units:
                if units:
                    self.log_event("⚠️ وحدات متاحة لكنها لا تطابق المواصفات.") 
            else:
                # 4. Attack Top 1
                target = scored_units[0]
                self.log_event(f"🎯 Target Acquired: {target.price} SAR | {target.area} m2 | Score: {target.score}")
                
                # Before Clicking, Lock State
                self.status = SessionState.LOCKED
                
                # Scroll & Click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", target.element)
                time.sleep(0.05) 
                target.element.click()
                
                # 5. Handover to Confirmation Logic
                self._handle_post_click_flow()
                return True

            # --- SMART REFRESH ALGORITHM (Hyper Speed) ---
            current_time = time.time()
            if not hasattr(self, 'last_refresh_time'):
                self.last_refresh_time = 0
            
            # Use configurable refresh gaps
            refresh_gap = REFRESH_GAP_DROP if self.mode == 'DROP' else REFRESH_GAP_SEARCH
            
            if current_time - self.last_refresh_time > refresh_gap:
                self.log_event("🔄 تحديث الصفحة (Refresh)...")
                try: 
                    driver.refresh()
                    self.list_view_clicked = False
                    self.show_units_clicked = False
                    # Wait for page load slightly
                    try: WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    except: pass
                except: pass
                self.last_refresh_time = current_time
                
            return False

        except Exception as e:
            # If error, unlock state
            self.status = SessionState.ATTACK_MODE 
            return False

    def _handle_post_click_flow(self):
        """التعامل مع التسلسل: ضغط ذكي + مراقبة حقيقية"""
        driver = self.driver
        MAX_WAIT = 45 # مهلة كافية للحجز
        
        start_time = time.time()
        booking_clicked = False
        sign_later_clicked = False
        
        self.log_event("👀 (Post-Click) جاري البحث عن زر الحجز...")
        
        while time.time() - start_time < MAX_WAIT:
            current_url = driver.current_url
            
            # 1. Success Check (Ultimate Goal)
            # 1. Success Check (Ultimate Goal)
            try:
                src_lower = driver.page_source.lower()
                if ("booking-confirm" in current_url or "success" in current_url or 
                    "تم الحجز" in src_lower or "تهانينا" in src_lower or 
                    "رقم الحجز" in src_lower or "طباعة العقد" in src_lower or
                    "حجوزاتي" in current_url):
                    
                    self.status = SessionState.SECURED
                    self.success_url = current_url
                    self.log_event("🏆 تمت العملية بنجاح حقيقي! (Confirmed)")
                    return
            except: pass

            # 2. Checkbox Handling (Always Accept Terms)
            try:
                checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                for chk in checkboxes:
                    if not chk.is_selected() and chk.is_displayed():
                        driver.execute_script("arguments[0].click();", chk)
                        time.sleep(0.1)
            except: pass

            # 3. STAGE 1: Click 'Book' / 'Reserve' (حجز)
            if not booking_clicked:
                # Updated XPath to include 'احجز وحدة' as seen in screenshot
                xpath_book = "//*[contains(text(), 'احجز وحدة') or normalize-space(text())='حجز' or normalize-space(text())='احجز الآن' or contains(@class, 'book-unit')]"
                try:
                    btns = driver.find_elements(By.XPATH, xpath_book)
                    if not btns:
                        # Scroll down to find button if not visible immediately
                        driver.execute_script("window.scrollBy(0, 300);")
                    
                    for btn in btns:
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.1)
                            driver.execute_script("arguments[0].click();", btn)
                            self.log_event("👆 تم ضغط زر 'احجز وحدة'!")
                            booking_clicked = True
                            time.sleep(1) # Wait for modal/next page
                except: pass
            
            # 4. STAGE 2: Click 'Sign Later' / 'Confirm' (وقع لاحقاً / تأكيد)
            # Only look for this if we suspect we are in the confirmation modal/page
            if booking_clicked or len(driver.find_elements(By.XPATH, "//*[contains(text(), 'وقع لاحقاً')]")) > 0:
                xpath_sign_later = "//*[contains(text(), 'لاحقا') or contains(text(), 'وقع لاحقاً')]"
                xpath_confirm = "//*[contains(text(), 'تأكيد') or contains(text(), 'موافق') or contains(text(), 'إرسال')]"
                
                try:
                    # Try 'Sign Later' first (Priority)
                    btns = driver.find_elements(By.XPATH, xpath_sign_later)
                    if not btns: btns = driver.find_elements(By.XPATH, xpath_confirm)
                    
                    for btn in btns:
                        if btn.is_displayed() and btn.is_enabled():
                            # Avoid clicking 'Cancel' by mistake
                            if "إلغاء" in btn.text: continue
                            
                            driver.execute_script("arguments[0].click();", btn)
                            self.log_event(f"👆 تأكيد نهائي: {btn.text}")
                            sign_later_clicked = True
                            time.sleep(1)
                except: pass

            # 5. Fallback: If we waited too long and nothing happened, maybe we never clicked the unit?
            # (Handled by the main loop timeout returning control to user)

            time.sleep(0.5)
            
        # If we reached here, limit reached.
        if sign_later_clicked:
             self.log_event("⚠️ تم إكمال الخطوات، يرجى التحقق من الحالة يدوياً.")
             try: self.success_url = driver.current_url
             except: pass
             self.status = SessionState.SECURED
        else:
             self.log_event("⚠️ انتهى الوقت دون تأكيد نهائي. هل الصفحة صحيحة؟")
             # We do NOT lock session here, letting user intervene.

    def check_header_notifications(self) -> Optional[str]:
        """مراقبة الرسائل والتنبيهات داخل الحساب (بعد تسجيل الدخول)"""
        driver = self.driver
        try:
            # تحديث الصفحة كل 30 ثانية لضمان ظهور التنبيهات الجديدة
            if int(time.time()) % 30 == 0: 
                 self.log_event("🔄 تحديث الصفحة للتحقق من الرسائل الجديدة...")
                 driver.refresh()
                 time.sleep(3)

            # 1. البحث عن 'الرسائل' (Messages)
            xpath_msgs = "//*[contains(text(), 'الرسائل') or contains(@href, 'messages') or contains(@class, 'messages')]"
            # 2. البحث عن 'التنبيهات' (Alerts)
            xpath_alerts = "//*[contains(text(), 'التنبيهات') or contains(text(), 'notifications')]"
            
            elements = driver.find_elements(By.XPATH, xpath_msgs) + driver.find_elements(By.XPATH, xpath_alerts)
            
            for el in elements:
                if not el.is_displayed(): continue
                
                # Check for "Badge" (Number/Red Dot)
                # usually indicated by a child span with number or class 'badge'
                try:
                    badge = el.find_element(By.XPATH, ".//*[contains(@class, 'badge') or contains(@class, 'count') or number(text()) > 0]")
                    if badge.is_displayed():
                        self.log_event("📬 **يوجد رسالة/تنبيه جديد!**")
                        
                        # Click to open
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(2)
                        
                        # Now scan the dropdown or the new page for keywords
                        return self._scan_page_for_links()
                except:
                    # If no badge logic, we can't blindly click or we'll loop.
                    pass

        except Exception as e:
            pass
            
        return None

    def _scan_page_for_links(self) -> Optional[str]:
        """مسح الصفحة أو القائمة المنسدلة بحثاً عن روابط مشاريع"""
        try:
            # Look for recent links with keywords
            # We look for links created closely or just top links
            links = self.driver.find_elements(By.TAG_NAME, "a")
            keywords = ["مشروع", "أرض", "للبيع", "حجز", "متوفر", "Project", "Land", "Booking"]
            
            for link in links:
                if not link.is_displayed(): continue
                text = link.text
                href = link.get_attribute('href')
                
                if not href or len(text) < 5: continue
                
                if any(k in text for k in keywords):
                    self.log_event(f"🎯 **تم العثور على رابط في الرسائل:** {text}")
                    return href
        except: pass
        return None

    def enable_notifications(self) -> bool:
        """تفعيل الإشعارات تلقائياً حسب الطريقة 1"""
        driver = self.driver
        
        # 1. Check Login Status
        if "login" in driver.current_url or "signin" in driver.current_url:
            self.log_event("⏳ الرجاء تسجيل الدخول أولاً...")
            return False

        # 2. Go to Profile if not there
        if "profile" not in driver.current_url:
            self.log_event("➡️ الانتقال للملف الشخصي...")
            driver.get("https://sakani.sa/profile")
            time.sleep(3)
        
        # 3. Find and Enable options
        keywords = ["إشعارات المشاريع الجديدة", "إشعارات الحجز"]
        found_any = False
        
        for kw in keywords:
            try:
                # Find Label
                label_xpath = f"//*[contains(text(), '{kw}')]"
                labels = driver.find_elements(By.XPATH, label_xpath)
                
                for label in labels:
                    if not label.is_displayed(): continue
                    
                    # Search for checkbox/switch nearby
                    # Assuming standard structure
                    parent = label.find_element(By.XPATH, "./..")
                    try:
                        # Try finding input sibling or child
                        checkbox = parent.find_element(By.XPATH, ".//input[@type='checkbox']")
                        
                        if not checkbox.is_selected():
                            self.log_event(f"فعّل: {kw}")
                            driver.execute_script("arguments[0].click();", checkbox)
                            time.sleep(1)
                            found_any = True
                        else:
                            self.log_event(f"✅ {kw} مفعل مسبقاً.")
                            found_any = True
                    except:
                        # Try wider search
                        try:
                           checkbox = parent.find_element(By.XPATH, "./..//input[@type='checkbox']")
                           if not checkbox.is_selected():
                               driver.execute_script("arguments[0].click();", checkbox)
                               found_any = True
                        except: pass
            except: pass
            
        if found_any:
            return True
        return False

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except: 
                pass
            self.driver = None


# --- Sniper Engine ---
class SniperEngine:
    def __init__(self):
        self.sessions: Dict[str, SniperSession] = {}
        self.running = False
    
    def add_session(self, chat_id: int, url: str) -> SniperSession:
        s_id = f"{chat_id}_{int(time.time())}"
        session = SniperSession(s_id, chat_id, url)
        self.sessions[s_id] = session
        return session

    async def run_loop(self, bot_app: Application):
        self.running = True
        logger.info("🔥 Selenium Sniper Engine Started")
        
        while self.running:
            # Dynamic Speed Control 🏎️
            # Default: Slow (Safe Mode) for manual login phase
            current_interval = 2.0 
            
            # Check if ANY session needs speed
            sessions_snapshot = list(self.sessions.values())
            for session in sessions_snapshot:
                if session.status in [SessionState.ATTACK_MODE, SessionState.LOCKED, SessionState.COUNTDOWN]:
                    # Turbo Mode triggers during Attack or final Countdown
                    current_interval = 0.001 
                    break
            
            await asyncio.sleep(current_interval)
            
            for session in sessions_snapshot:
                await self._process_session(session, bot_app)

    async def _process_session(self, session: SniperSession, app: Application):
        # 0. WATCHING Logic (Notification Monitor)
        if session.status == SessionState.WATCHING:
            # Check for notifications every 2-3 seconds
            loop = asyncio.get_running_loop()
            found_url = await loop.run_in_executor(None, session.check_header_notifications)
            
            if found_url:
                session.log_event(f"🚨 تم اقتناص رابط من الإشعارات: {found_url}")
                
                # RESET SNIPER STATE for the new target 🔄
                session.first_scan_done = False
                session.ignored_plots = set()
                session.list_view_clicked = False
                session.show_units_clicked = False
                session.url = found_url
                
                # Switch to Attack
                session.mode = 'DROP' 
                session.status = SessionState.ATTACK_MODE 
                
                # Navigate immediately
                session.driver.get(found_url)
                
                await session.update_dashboard(app, f"🦅 **هجوم!** مصدر الرابط: إشعار")
            else:
                 # Update time only occasionally
                 if int(time.time()) % 10 == 0:
                     await session.update_dashboard(app)
            return

        # 1. INITIALIZING -> IDLE or COUNTDOWN
        if session.status == SessionState.INITIALIZING:
            session.status = SessionState.IDLE
            await session.update_dashboard(app, "System Initialized.")
            
        # 2. IDLE/COUNTDOWN Logic
        elif session.status in [SessionState.IDLE, SessionState.COUNTDOWN]:
            rem = session.time_remaining_seconds()
            
            # Status Transition logic
            if rem > 60:
                session.status = SessionState.IDLE
            elif 10 < rem <= 60:
                if session.status != SessionState.COUNTDOWN:
                    session.log_event("⏳ Entering Critical Zone (<60s)")
                    session.status = SessionState.COUNTDOWN
                    
            elif rem <= 10:
                if rem <= 0:
                    session.status = SessionState.ATTACK_MODE
                    await session.update_dashboard(app, "🦅 **ASSAULT STARTED!**")
                else:
                    session.status = SessionState.COUNTDOWN

            # Periodic Update (every few seconds avoid spam)
            if int(rem) % 5 == 0: 
                 await session.update_dashboard(app)

        # 3. ATTACK MODE (The Loop)
        elif session.status == SessionState.ATTACK_MODE:
            loop = asyncio.get_running_loop()
            
            # Rapid Fire Loop (Increased Speed & Intensity)
            # We loop more times with less sleep to dominate the CPU time for checking
            for _ in range(50): 
                if session.status != SessionState.ATTACK_MODE: break
                
                await loop.run_in_executor(None, session.check_and_act)
                # Hyper-speed delay
                await asyncio.sleep(0.01) 
            
            # Update Dashboard less frequently during attack
            # But if we did not find anything after 50 checks, maybe we just loop again.

        # 4. LOCKED / OTP / SECURED Handlers
        elif session.status in [SessionState.LOCKED, SessionState.OTP_REQUIRED]:
            pass
        elif session.status == SessionState.SECURED:
             if not getattr(session, 'notified_success', False):
                link = session.success_url if session.success_url else session.url
                msg = (
                    "🎉 **مبروك! تم الحجز بنجاح** 🏆\n\n"
                    f"🔗 **رابط الوحدة:**\n{link}\n\n"
                    "✅ يرجى التأكد من صفحة 'حجوزاتي'."
                )
                try: await app.bot.send_message(chat_id=session.chat_id, text=msg)
                except: pass
                
                session.notified_success = True
                await session.update_dashboard(app, "🏆 تمت المهمة بنجاح!")
        elif session.status == SessionState.SETUP:
             # Run notification setup logic
             # We run in executor because it uses blocking Selenium calls
             loop = asyncio.get_running_loop()
             success = await loop.run_in_executor(None, session.enable_notifications)
             
             if success:
                 session.status = SessionState.SECURED
                 await session.update_dashboard(app, "✅ تم تفعيل الإشعارات بنجاح!")
             else:
                 # It might actully be 'waiting for login' which returns False
                 # We keep status as SETUP to retry or wait?
                 # enable_notifications handles its own loop logic?
                 # Actually, enable_notifications in my design does one pass. 
                 # If it returns False (e.g. at login page), we should wait and retry.
                 await asyncio.sleep(2)

        elif session.status == SessionState.TERMINATED:
             pass

    async def _notify(self, app: Application, session: SniperSession, text: str):
        # Legacy Wrapper: Redirects to dashboard update for consistency
        await session.update_dashboard(app, text)

engine = SniperEngine()

# --- Telegram Handlers ---

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
# States
URL, TIME, MODE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown(
        "👋 **أهلاً بك في نظام القنص الذكي**\n\n"
        "🔗 **الرابط:** يرجى إرسال رابط الوحدة أو المشروع.\n"
        "سيقوم البوت بإدارة العملية بالكامل."
    )

async def snipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔗 **الرابط:** أرسل رابط الصفحة المطلوبة:")
    return URL

async def notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start notification setup session"""
    chat_id = update.effective_chat.id
    url = "https://sakani.sa/profile"
    
    session = engine.add_session(chat_id, url)
    session.status = SessionState.SETUP
    session.mode = "SETUP"
    
    msg = (
        "⚙️ **بدء إعداد الإشعارات (الطريقة 1)**\n"
        "1️⃣ سيتم فتح صفحة الملف الشخصي.\n"
        "2️⃣ سجل الدخول إذا طلب منك ذلك.\n"
        "3️⃣ سأقوم بتفعيل التنبيهات تلقائياً.\n\n"
        "⏳ **جاري التشغيل...**"
    )
    await update.message.reply_markdown(msg)
    await session.update_dashboard(context.application)


async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    context.user_data['snipe_url'] = url
    
    # Launch Session immediately
    session = engine.add_session(update.effective_chat.id, url)
    
    # FORCE Mode to 'DROP' (Insane Speed & Aggression) ⚡
    session.mode = 'DROP' 
    context.user_data['sess_id'] = session.session_id
    
    # Auto-set time to NOW + 60 seconds buffer
    future_now = datetime.now() + timedelta(seconds=60)
    session.set_target_time(future_now.strftime("%H:%M:%S"))
    
    msg = (
        "✅ **تم استلام الرابط!**\n"
        "⚡ **تم تفعيل وضع القنص الجنوني تلقائياً!**\n\n"
        "🛑 **المطلوب منك الآن:**\n"
        "1️⃣ اذهب للمتصفح المفتوح وسجل الدخول بسرعة.\n"
        "2️⃣ بعد 60 ثانية سأبدأ الهجوم تلقائياً!\n\n"
        "🦅 **وضع الهجوم: بعد 60 ثانية...**"
    )
    
    warning = ""
    if not PHONE_NUMBER:
        warning = "\n⚠️ **تنبيه:** رقم الجوال غير مسجل."
        msg += warning

    await update.message.reply_text(msg)
    
    # Show dashboard immediately
    await session.update_dashboard(context.application)
    
    # End conversation immediately
    return ConversationHandler.END

async def receive_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    session_id = context.user_data.get('session_id')
    
    if not session_id: 
        await update.message.reply_text("❌ حدث خطأ في الجلسة.")
        return ConversationHandler.END
    
    session = engine.sessions.get(session_id)
    if not session: 
        await update.message.reply_text("❌ الجلسة غير موجودة.")
        return ConversationHandler.END

    # Set Mode logic
    mode_msg = ""
    if "جديد" in choice or "⚡" in choice:
        session.mode = 'DROP'
        mode_msg = "⚡ **تم تفعيل وضع القنص (تحديث جنوني)!**"
    else:
        session.mode = 'SEARCH'
        mode_msg = "🔍 **تم تفعيل وضع البحث (تحديث هادئ).**"

    # Start Timer Logic (60s Buffer)
    future_now = datetime.now() + timedelta(seconds=60)
    session.set_target_time(future_now.strftime("%H:%M:%S"))
    
    msg = (
        f"{mode_msg}\n\n"
        "✅ **تم فتح المتصفح!**\n"
        "🛑 **المطلوب منك الآن:**\n"
        "1️⃣ اذهب للمتصفح المفتوح وسجل الدخول بسرعة.\n"
        "2️⃣ بعد 60 ثانية سأبدأ الهجوم تلقائياً!\n\n"
        "🦅 **وضع الهجوم: بعد 60 ثانية...**"
    )
    
    warning = ""
    if not PHONE_NUMBER:
        warning = "\n⚠️ **تنبيه:** رقم الجوال غير مسجل."
        msg += warning

    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    
    # Show dashboard
    await session.update_dashboard(context.application)
    
    return ConversationHandler.END

async def receive_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This might not be reached if we end conversation in receive_url
    # But checking for safety
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 تم الإلغاء.")
    return ConversationHandler.END

async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مراقبة الإشعارات الحية"""
    chat_id = update.effective_chat.id
    url = "https://sakani.sa/dashboard" # Default landing
    
    session = engine.add_session(chat_id, url)
    session.status = SessionState.WATCHING
    session.mode = "WATCH"
    
    msg = (
        "📡 **بدء نظام المراقبة (Watch Mode)**\n"
        "سيقوم البوت بمراقبة:\n"
        "1️⃣ **الرسائل (Messages)**\n"
        "2️⃣ **التنبيهات (Alerts)**\n"
        "داخل حساب سكني الخاص بك.\n\n"
        "⚠️ **ملاحظة:** طريقة المراقبة الأسرع هي الـ SMS، ولكن البوت سيحاول التقاط أي رسالة جديدة تظهر في الموقع فوراً."
    )
    await update.message.reply_markdown(msg)
    await session.update_dashboard(context.application)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_sessions = [s for s in engine.sessions.values() if s.chat_id == chat_id]
    
    if not user_sessions:
        await update.message.reply_text("📭 لا توجد مهام نشطة.")
        return

    msg = ""
    for s in user_sessions:
        msg += f"📦 **الجلسة رقم {s.session_id[-4:]}**\n"
        msg += f"📊 **الحالة:** {s.status}\n"
        if s.logs:
            msg += f"📝 **آخر نشاط:** {s.logs[-1]}\n"
        msg += "ـــــــــــــــــــــــــــــــــــــــــــــــــــ\n"
        
    await update.message.reply_markdown(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 **دليل الأوامر - نظام قنص سكاني**\n\n"
        "🔹 `/watch` - **مراقبة التنبيهات الحية** 📡\n"
        "   (يبقي البوت ينتظر أي إشعار جديد في حسابك للانقضاض عليه)\n\n"
        "🔹 `/snipe` - **بدء مهمة قنص جديدة**\n"
        "   (سيقوم بفتح المتصفح وينتظرك تسجل الدخول ثم يبدأ الهجوم)\n\n"
        "🔹 `/status` - **عرض حالة المهام النشطة**\n"
        "   (يعرض لك لوحة التحكم الحية لكل جلسة نشطة)\n\n"
        "🔹 `/cancel` - **إلغاء العملية الحالية**\n"
        "   (لإيقاف المعالج إذا علق في خطوة ما)\n\n"
        "🔹 `/start` - **رسالة الترحيب**\n\n"
        "� `/restart` - **إعادة تشغيل النظام**\n"
        "   (استخدم هذا الأمر لتحديث البوت بعد تعديل الكود)\n\n"
        "🔹 `/stop` - **إيقاف البوت نهائياً**\n\n"
        "�💡 **تلميح:** يمكنك تشغيل عدة مهام في وقت واحد بإرسال /snipe أكثر من مرة."
    )
    await update.message.reply_markdown(help_text)

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ **جاري إعادة تشغيل النظام لتطبيق التحديثات...**")
    # This restarts the current script
    os.execl(sys.executable, sys.executable, *sys.argv)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 **تم إغلاق البوت. يجب تشغيله يدوياً من السيرفر للعودة.**")
    # Force exit
    os._exit(0)

# --- Main ---
async def post_init(app: Application):
    asyncio.create_task(engine.run_loop(app))
    
    # Auto-Start Logic
    if TARGET_URL:
        print(f"🚀 Auto-Starting Sniper Session from Config...")
        chat_id = AUTO_START_CHAT_ID if AUTO_START_CHAT_ID else 0
        session = engine.add_session(chat_id, TARGET_URL)
        
        if TARGET_TIME.lower() == 'now':
            session.set_target_time(datetime.now().strftime("%H:%M:%S"))
        else:
            session.set_target_time(TARGET_TIME)
            
        print(f"✅ Auto-Session Created.")
    
    # Notify Admin that System is Online
    elif AUTO_START_CHAT_ID:
        try:
            welcome_msg = (
                "🤖 **تم تشغيل نظام القنص (SakanBot) بنجاح!**\n\n"
                "الأوامر المتاحة:\n"
                "🎯 `/snipe` - لبدء قنص جديد (سيطلب الرابط)\n"
                "📊 `/status` - لعرض حالة البوت\n"
                "❓ `/help` - عرض المساعدة\n\n"
                "🚀 *أرسل /snipe للبدء!*"
            )
            await app.bot.send_message(chat_id=AUTO_START_CHAT_ID, text=welcome_msg, parse_mode='Markdown')
        except Exception as e:
            print(f"⚠️ Failed to send startup message: {e}")

def main():
    if not TELEGRAM_AVAILABLE: return
    print("🚀 Starting Selenium Sniper Bot (Advanced)...")
    
    # Increase Timeouts to fix TimedOut error
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .connect_timeout(60.0) # Increased from default
        .read_timeout(60.0)    # Increased from default
        .build()
    )
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('snipe', snipe_command)],
        states={
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_url)],
            MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mode)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command)) # Added Help Handler
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("notifications", notifications_command))
    app.add_handler(CommandHandler("watch", watch_command))
    app.add_handler(CommandHandler("restart", restart_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(conv)
    
    app.run_polling()

if __name__ == "__main__":
    main()
