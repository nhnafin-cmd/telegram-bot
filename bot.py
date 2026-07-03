import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
# আপনার চ্যানেলের ইউজারনেম (অবশ্যই বটকে এই চ্যানেলের অ্যাডমিন বানাতে হবে)
CHANNEL_USERNAME = "@OfficialInstagramSellBD"

# ইউজার চ্যানেলে জয়েন আছে কি না তা চেক করার ফাংশন
async def is_user_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # যদি ইউজার মেম্বার, অ্যাডমিন বা ক্রিয়েটর হয়
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except BadRequest:
        # যদি কোনো কারণে চেক করতে না পারে
        return False

# /start কমান্ড দিলে এই ফাংশন কাজ করবে
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # প্রথমে চেক করবে ইউজার জয়েন করেছে কি না
    if await is_user_joined(context, user_id):
        # জয়েন থাকলে মেইন মেনু দেখাবে
        await show_main_menu(update)
    else:
        # জয়েন না থাকলে ফোর্সব্যাক বাটন দেখাবে (Welcome মেসেজ দেখাবে না)
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("✅ Joined ✅", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ আপনি আমাদের অফিশিয়াল চ্যানেলে জয়েন করেননি।\n\nবটটি ব্যবহার করতে নিচের বাটনে ক্লিক করে জয়েন করুন, তারপর 'Joined' বাটনে চাপ দিন।",
            reply_markup=reply_markup
        )

# মেইন মেনু দেখানোর ফাংশন
async def show_main_menu(update: Update):
    keyboard = [
        ['📝 কাজ •', '💵 ব্যালেন্স'],
        ['💰 টাকা উত্তোলন', '🎁 My Referrals'],
        ['🎧 সাপোর্ট', '🙋‍♂️ আমি নতুন']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # জয়েন করার পরই কেবল এই মেসেজটি আসবে
    if update.message:
        await update.message.reply_text(
            "🤖 WELCOME OUR OFFICIAL INSTAGRAM BOT BD", 
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "🤖 WELCOME OUR OFFICIAL INSTAGRAM BOT BD", 
            reply_markup=reply_markup
        )

# Inline Button (Joined ✅) ক্লিকের হ্যান্ডলার
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "check_join":
        if await is_user_joined(context, user_id):
            await query.message.delete() # আগের জয়েন করার মেসেজটি মুছে দেবে
            await show_main_menu(update)
        else:
            await query.message.reply_text("⚠️ আপনি এখনো জয়েন করেননি! দয়া করে আগে চ্যানেলে জয়েন করুন।")

# অন্যান্য বাটন ক্লিকের মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # প্রতিটা মেসেজ বা বাটন চাপে চেক করবে সে এখনো চ্যানেলে আছে কি না
    if not await is_user_joined(context, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("✅ Joined ✅", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ সামনে আগানোর আগে আপনাকে অবশ্যই চ্যানেলে জয়েন থাকতে হবে!", reply_markup=reply_markup)
        return

    text = update.message.text

    if text == '📝 কাজ •':
        sub_keyboard = [['ইনস্টাগ্রাম কাজ >'], ['⬅️ ফিরে যান']]
        sub_markup = ReplyKeyboardMarkup(sub_keyboard, resize_keyboard=True)
        await update.message.reply_text("সিলেক্ট করুন:", reply_markup=sub_markup)

    elif text == 'ইনস্টাগ্রাম কাজ >':
        await update.message.reply_text("এখানে আপনার ইনস্টাগ্রামের কাজের ডিটেইলস বা লিংক দিন।")

    elif text == '⬅️ ফিরে যান':
        await show_main_menu(update)

    elif text == '💵 ব্যালেন্স':
        await update.message.reply_text("💰 আপনার বর্তমান ব্যালেন্স: 0.00 টাকা")

    elif text == '💰 টাকা উত্তোলন':
        await update.message.reply_text("বিকাশ বা নগদে টাকা তুলতে মিনিমাম অ্যামাউন্ট প্রয়োজন।")

    elif text == '🎁 My Referrals':
        await update.message.reply_text("🔗 আপনার রেফারেল লিংক: (এখানে লিংক জেনারেট হবে)")

    elif text == '🎧 সাপোর্ট':
        await update.message.reply_text("যেকোনো সমস্যায় আমাদের এডমিনের সাথে যোগাযোগ করুন।")

    elif text == '🙋‍♂️ আমি নতুন':
        await update.message.reply_text("বটে কীভাবে কাজ করবেন তা জানতে আমাদের গাইডলাইনটি পড়ুন।")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(update.callback_query_handlers if hasattr(update, 'callback_query_handlers') else MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Callback query handler যোগ করা হলো inline button এর জন্য
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("বটটি সফলভাবে চালু হয়েছে...")
    app.run_polling()

if __name__ == '__main__':
    main()
        
