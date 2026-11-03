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

# إعداد السجلات
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- 1. إعداد قاعدة البيانات ---
conn = sqlite3.connect('referrals.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, invites INTEGER DEFAULT 0)''')
conn.commit()

# --- 2. خادم الويب ---
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

# --- 3. نظام الإحالة ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    is_new_user = cursor.fetchone() is None
    
    if is_new_user:
        cursor.execute("INSERT INTO users (user_id, invites) VALUES (?, 0)", (user_id,))
        conn.commit()
        
        inviter_id = command.args
        if inviter_id and inviter_id.isdigit() and int(inviter_id) != user_id:
            cursor.execute("UPDATE users SET invites = invites + 1 WHERE user_id = ?", (int(inviter_id),))
            conn.commit()
            try:
                await bot.send_message(int(inviter_id), "🎉 مبروك! قام شخص جديد بالدخول عبر رابط الإحالة الخاص بك.")
            except Exception as e:
                logging.error(f"Failed to send notification: {e}")

    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    share_url = f"https://t.me/share/url?url={ref_link}&text=انضم إلينا للحصول على مباريات مضمونة 100%!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 مشاركة الرابط", url=share_url)],
        [InlineKeyboardButton(text="🔄 التحقق من المشاركة", callback_data="check_invites")]
    ])
    
    text = (
        "أهلاً بك في قناة ALGOSPORT-PRO! 🏆\n"
        "خطوة بسيطة تفصلك عن الانضمام إلينا وضمان مكانك بين الفائزين معنا:\n\n"
        "🔗 **الخطوة المطلوبة:** قم بمشاركة رابط القناة مع 10 أشخاص من أصدقائك أو المجموعات المهتمة.\n\n"
        "📥 **ماذا بعد؟** بمجرد إتمام المشاركة بنجاح، سيتم إرسال رابط القناة الأصلي إليك مباشرة للدخول إلى القناة والحصول على مباريات مضمونة 100%.\n\n"
        "نحن بانتظارك، بالتوفيق! 🚀"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

# --- 4. برمجة زر "التحقق من المشاركة" ---
@dp.callback_query(F.data == "check_invites")
async def check_invites_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    cursor.execute("SELECT invites FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    invites = result[0] if result else 0

    if invites >= 10:
        channel_link = "https://t.me/+ZO35DK2257AwMjk8"
        await callback.message.answer(f"🎉 تهانينا! لقد أكملت 10 دعوات بنجاح.\nإليك رابط الانضمام للقناة:\n{channel_link}")
        await callback.answer()
    else:
        remaining = 10 - invites
        await callback.answer(f"❌ لديك {invites} دعوات فقط.\nتحتاج إلى {remaining} دعوات إضافية للحصول على الرابط.", show_alert=True)

async def main():
    threading.Thread(target=run_server, daemon=True).start()
    
    logging.info("تنظيف الاتصالات القديمة...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    logging.info("جاري تشغيل بوت تيليجرام...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not BOT_TOKEN:
        logging.error("خطأ: التوكن غير موجود أو فارغ!")
    else:
        asyncio.run(main())
