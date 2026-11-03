import os
import asyncio
from aiogram import Bot, Dispatcher
from aiohttp import web

# جلب توكن البوت من المتغيرات (تأكد من عدم وجود مسافات)
TOKEN = os.environ.get("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# رسالة رد وهمية لإرضاء فحص منصة Render
async def health_check(request):
    return web.Response(text="البوت يعمل بنجاح على الخطة المجانية!")

async def main():
    # إعداد السيرفر الوهمي
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render يمرر رقم المنفذ إجبارياً عبر المتغير PORT
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    # تشغيل بوت تيليجرام
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
