import logging
import os
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, executor, types

# --- خادم الويب لتلبية متطلبات منصة Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()
# ---------------------------------------------

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    exit("خطأ: يرجى تعيين متغير البيئة BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# قاعدة البيانات
def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            invites INTEGER DEFAULT 0,
            invited_by INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

CHANNEL_URL = "https://t.me/ALGOLIVESPORTPRO"
REQUIRED_INVITES = 10

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()
    
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT invites FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        invited_by = None
        if args and args.isdigit():
            inviter_id = int(args)
            if inviter_id != user_id:
                invited_by = inviter_id
                cursor.execute("SELECT invites FROM users WHERE user_id = ?", (inviter_id,))
                inviter = cursor.fetchone()
                if inviter:
                    new_invites = inviter[0] + 1
                    cursor.execute("UPDATE users SET invites = ? WHERE user_id = ?", (new_invites, inviter_id))
                    try:
                        await bot.send_message(inviter_id, f"🎉 انضم شخص عبر رابطك! أصبح عدد دعواتك: {new_invites}/{REQUIRED_INVITES}")
                    except:
                        pass
        
        cursor.execute("INSERT OR IGNORE INTO users (user_id, invites, invited_by) VALUES (?, 0, ?)", (user_id, invited_by))
        conn.commit()
        invites = 0
    else:
        invites = user[0]
        
    conn.close()
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    if invites >= REQUIRED_INVITES:
        await message.answer(
            f"🎉 مبروك! لقد أكملت دعوة {REQUIRED_INVITES} أشخاص.\n\n"
            f"إليك رابط القناة الخاصة بالمباريات المضمونة:\n{CHANNEL_URL}"
        )
    else:
        await message.answer(
            f"مرحباً بك عزيزي في بوت المباريات المضمونة والفوز معنا!\n\n"
            f"🔗 دعوة أصدقائك للحصول على رابط القناة الخاصة:\n"
            f"{ref_link}\n\n"
            f"📊 عدد دعواتك الحالية: {invites}/{REQUIRED_INVITES}\n"
            f"يجب عليك دعوة 10 أشخاص لفتح رابط القناة."
        )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
