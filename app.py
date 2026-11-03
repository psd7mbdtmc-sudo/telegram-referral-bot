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

# تحميل متغيرات البيئة وتنظيف التوكن من المسافات
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
@dp.
