import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
  exit("خطأ: يرجى تعيين متغير البيئة BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)


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


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
  user_id = message.from_user.id
  args = message.get_args()

  conn = sqlite3.connect("bot.db")
  cursor = conn.cursor()

  cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
  user = cursor.fetchone()

  bot_info = await bot.get_me()
  bot_username = bot_info.username

  if not user:
    invited_by = None
    if args and args.isdigit():
      referrer_id = int(args)
      if referrer_id != user_id:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (referrer_id,))
        if cursor.fetchone():
          invited_by = referrer_id
          cursor.execute(
              "UPDATE users SET invites = invites + 1 WHERE user_id = ?",
              (referrer_id,),
          )
          conn.commit()

          try:
            cursor.execute(
                "SELECT invites FROM users WHERE user_id = ?", (referrer_id,)
            )
            ref_invites = cursor.fetchone()[0]
            await bot.send_message(
                referrer_id,
                f"🎉 شخص جديد انضم عبر رابطك الخاص!\nعدد دعواتك الآن:"
                f" {ref_invites}/10",
            )
          except Exception:
            pass

    cursor.execute(
        "INSERT INTO users (user_id, invites, invited_by) VALUES (?, 0, ?)",
        (user_id, invited_by),
    )
    conn.commit()
    invites_count = 0
  else:
    invites_count = user[1]

  conn.close()

  ref_link = f"https://t.me/{bot_username}?start={user_id}"

  text = (
      f"مرحباً بك عزيزي .\n"
      f"إن كنت مهتم بالمباريات المضمونة و الفوز معنا ، أدخل للقناة الأصلية.\n\n"
      f"رابط الدعوة الخاص بك:\n{ref_link}\n\n"
      f"دعواتك الحالية: {invites_count}/10\n"
      f"أضف 10 أشخاص و عند الانتهاء سوف يصلك رابط الدخول ، و لن تندم عندما"
      f" تدخل!"
  )

  if invites_count >= 10:
    text += (
        "\n\n🎁 مبروك! لقد أتممت الشروط بنجاح.\nرابط القناة الخاص بك هو:"
        " https://t.me/ALGOLIVESPORTPRO"
    )

  await message.answer(text)


if __name__ == "__main__":
  executor.start_polling(dp, skip_updates=True)
