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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# تحميل متغيرات البيئة
load_dotenv()

# السطر السحري: جلب التوكن ومسح أي مسافات أو أسطر مخفية تلقائياً
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# إعداد السجلات (Logs) لتظهر بوضوح في منصة Render
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# تهيئة البوت
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# خادم ويب مصغر لتلبية شروط منفذ Render المجاني
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")
        
    def log_message(self, format, *args):
        return # كتم سجلات الفحص المتكررة ليبقى السجل نظيفاً

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logging.info(f"Web server started on port {port}")
    server.serve_forever()

# أمر البدء للتجربة
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("أهلاً بك! تم تشغيل البوت بنجاح وتجاوز مشكلة المسافات.")

async def main():
    # تشغيل خادم الويب في الخلفية حتى لا يتعطل البوت
    threading.Thread(target=run_server, daemon=True).start()
    
    # تشغيل بوت تيليجرام
    logging.info("جاري تشغيل بوت تيليجرام...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not BOT_TOKEN:
        logging.error("خطأ: التوكن غير موجود أو فارغ!")
    else:
        asyncio.run(main())
