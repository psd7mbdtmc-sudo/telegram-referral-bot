import os
import sys
import logging
import sqlite3
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# تحميل متغيرات البيئة
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# إعداد السجلات (Logs)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- 1. إعداد قاعدة البيانات ---
conn = sqlite3.connect('referrals.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, invites INTEGER DEFAULT 0)''')
conn.commit()

# --- 2. خادم الويب (للبقاء مجانياً على Render) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")
    def log_message(self, format, *args):
        return 

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logging.info(f"Web server started on port {port}")
    server.serve_forever()

# --- 3. نظام الإحالة (الرد على أمر start) ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    
    # التحقق هل المستخدم جديد؟
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    is_new_user = cursor.fetchone() is None
    
    if is_new_user:
        # تسجيل المستخدم الجديد
        cursor.execute("INSERT INTO users (user_id, invites) VALUES (?, 0)", (user_id,))
        conn.commit()
        
        # التحقق من الداعي
        inviter_id = command.args
        if inviter_id and inviter_id.isdigit() and int(inviter_id) != user_id:
            cursor.execute("UPDATE users SET invites = invites + 1 WHERE user_id = ?", (int(inviter_id),))
            conn.commit()
            try:
                await bot.send_message(int(inviter_id), "🎉 مبروك! قام شخص جديد بالدخول عبر رابط الإحالة الخاص بك.")
            except Exception as e:
                logging.error(f"Failed to send notification: {e}")

    # الرابط الأول: تكوين رابط الإحالة الخاص بالبوت تلقائياً للمشاركة
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    share_url = f"
