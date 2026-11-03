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
