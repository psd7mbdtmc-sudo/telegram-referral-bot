import os
import sys
import asyncio
import logging
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# تحميل متغيرات البيئة
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# إعداد السجلات (Logs) لتظهر بوضوح في منصة Render
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# ==========================================
# 1. خادم ويب مصغر لتلبية شروط منفذ الويب على Render
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

    def log_message(self, format, *args):
        return  # كتم سجلات الفحص المتكررة ليبقى السجل نظيفاً

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logging.info(f"Web server started on port {port}")
    server.serve_forever()

# تشغيل خادم الويب في الخلفية
threading.Thread(target=run_server, daemon=True).start()


# ==========================================
# 2. قاعدة بيانات لحفظ المستخدمين والإحالات
# ==========================================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    referred_by INTEGER,
    referrals_count INTEGER DEFAULT 0
)
""")
conn.commit()

def register_user(user_id: int, username: str, full_name: str, referred_by: int = None) -> bool:
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is not None:
        return False  # المستخدم مسجل مسبقاً

    cursor.execute(
        "INSERT INTO users (user_id, username, full_name, referred_by, referrals_count) VALUES (?, ?, ?, ?, 0)",
        (user_id, username, full_name, referred_by)
    )
    if referred_by and referred_by != user_id:
        cursor.execute(
            "UPDATE users SET referrals_count = referrals_count + 1 WHERE user_id = ?",
            (referred_by,)
        )
    conn.commit()
    return True

def get_referrals_count(user_id: int) -> int:
    cursor.execute("SELECT referrals_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

def get_top_users(limit: int = 10):
    cursor.execute("SELECT full_name, referrals_count FROM users ORDER BY referrals_count DESC LIMIT ?", (limit,))
    return cursor.fetchall()


# ==========================================
# 3. إعداد البوت والأوامر التفاعلية (Aiogram 3)
# ==========================================
dp = Dispatcher()
BOT_USERNAME = "Algolivesporttbot"

def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    share_url = f"https://t.me/share/url?url={ref_link}&text=انضم إلى بوت الرياضة المباشر عبر الرابط الخاص بي!"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 مشاركة رابط الإحالة", url=share_url)],
        [
            InlineKeyboardButton(text="📊 إحالاتي", callback_data="my_stats"),
            InlineKeyboardButton(text="🏆 المتصدرين", callback_data="leaderboard")
        ]
    ])

@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or "مستخدم"

    referred_by = None
    if command.args and command.args.isdigit():
        referred_by = int(command.args)

    is_new = register_user(user_id, username, full_name, referred_by)

    # إشعار الشخص الذي قام بالدعوة عند انضمام عضو جديد
    if is_new and referred_by and referred_by != user_id:
        try:
            new_count = get_referrals_count(referred_by)
            await bot.send_message(
                referred_by,
                f"🎉 مبروك! انضم **{full_name}** عبر رابط الإحالة الخاص بك.\n"
                f"📊 إجمالي إحالاتك الآن: **{new_count}**",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"Could not notify referrer {referred_by}: {e}")

    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    count = get_referrals_count(user_id)

    welcome_text = (
        f"أهلاً بك يا **{full_name}** في بوت الإحالات الرياضي! ⚽🔥\n\n"
        f"🔗 **رابط الإحالة الخاص بك:**\n`{ref_link}`\n\n"
        f"👥 **عدد إحالاتك الحالية:** {count}\n\n"
        f"شارك الرابط مع أصدقائك لزيادة رصيدك من الإحالات!"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")

@dp.callback_query(F.data == "my_stats")
async def show_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    count = get_referrals_count(user_id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    text = (
        f"📊 **إحصائيات حسابك:**\n\n"
        f"👤 الاسم: {callback.from_user.full_name}\n"
        f"👥 عدد الدعوات الناجحة: **{count}**\n\n"
        f"🔗 رابط الدعوة الخاص بك:\n`{ref_link}`"
    )
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: types.CallbackQuery):
    top_users = get_top_users(10)
    if not top_users:
        text = "🏆 لا يوجد متصدرون حتى الآن."
    else:
        lines = ["🏆 **قائمة أفضل 10 داعمين (المتصدرين):**\n"]
        for idx, (name, count) in enumerate(top_users, start=1):
            lines.append(f"{idx}. {name} — **{count}** إحالة")
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=get_main_keyboard(callback.from_user.id), parse_mode="Markdown")
    await callback.answer()


# ==========================================
# 4. نقطة التشغيل الرئيسية
# ==========================================
async def main():
    if not BOT_TOKEN:
        logging.error("خطأ: لم يتم العثور على BOT_TOKEN في متغيرات البيئة (Environment Variables) في Render!")
        # إبقاء البرنامج حياً لكي ترى الرسالة في السجل بدلاً من الإغلاق المفاجئ
        while True:
            await asyncio.sleep(3600)

    bot = Bot(token=BOT_TOKEN)
    logging.info("Starting Telegram Bot Polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
