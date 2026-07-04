import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@OfficialInstagramSellBD"

# ⚠️ এইখানে আপনার নিজের টেলিগ্রাম ইউজার আইডি বসান (যা @userinfobot থেকে পেয়েছেন)
ADMIN_ID = 7831606559

# ইউজার কোন স্টেটে আছে তা ট্র্যাক করার জন্য ডিকশনারি
USER_STATES = {}

async def is_user_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except BadRequest:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_STATES[user_id] = None
    
    if await is_user_joined(context, user_id):
        keyboard = [
            ['📝 কাজ •', '💵 ব্যালেন্স'],
            ['💰 টাকা উত্তোলন', '🎁 My Referrals'],
            ['🎧 সাপোর্ট', '🙋‍♂️ আমি নতুন']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🌷স্বাগতম আমাদের Official Instagram Sell BD Bot এ 🫠🤗", 
            reply_markup=reply_markup
        )
    else:
        keyboard = [['✅ Joined ✅']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ আপনি আমাদের অফিশিয়াল চ্যানেলে জয়েন করেননি।\n\n"
            f"প্রথমে এখানে ক্লিক করে জয়েন করুন: {CHANNEL_USERNAME}\n\n"
            f"তারপর নিচে '✅ Joined ✅' বাটনে চাপ দিন।",
            reply_markup=reply_markup
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "No Username"
    first_name = update.effective_user.first_name
    text = update.message.text

    if text == '✅ Joined ✅':
        if await is_user_joined(context, user_id):
            await start(update, context)
        else:
            await update.message.reply_text("⚠️ আপনি এখনো জয়েন করেননি! দয়া করে আগে চ্যানেলে জয়েন করুন।")
        return

    if not await is_user_joined(context, user_id):
        keyboard = [['✅ Joined ✅']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"⚠️ সামনে আগানোর আগে আপনাকে অবশ্যই চ্যানেলে জয়েন থাকতে হবে!\nLink: {CHANNEL_USERNAME}", reply_markup=reply_markup)
        return

    # 📥 [কাজ জমা] স্টেট হ্যান্ডলিং
    if USER_STATES.get(user_id) == 'WAITING_FOR_ID':
        if text == '⬅️ ফিরে যান':
            USER_STATES[user_id] = None
            await start(update, context)
            return
        admin_message = f"📥 **নতুন কাজ জমা পড়েছে!**\n\n👤 নাম: {first_name}\n🆔 আইডি: `{user_id}`\n🔗 @{username}\n\n📝 **জমা দেওয়া আইডি/লিংক:**\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode="Markdown")
        await update.message.reply_text("✅ আপনার ইনস্টাগ্রাম আইডিটি সফলভাবে জমা হয়েছে!")
        USER_STATES[user_id] = None
        return

    # 💰 [টাকা উত্তোলন] স্টেট হ্যান্ডলিং
    if USER_STATES.get(user_id) in ['WAITING_FOR_BKASH', 'WAITING_FOR_NAGAD']:
        if text == '⬅️ ফিরে যান':
            USER_STATES[user_id] = None
            await start(update, context)
            return
        method = "বিকাশ" if USER_STATES[user_id] == 'WAITING_FOR_BKASH' else "নগদ"
        withdraw_msg = f"💰 **উইথড্র রিকোয়েস্ট!**\n\n👤 {first_name}\n🆔 `{user_id}`\n💳 মাধ্যম: {method}\n📱 **ডিটেইলস:**\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=withdraw_msg, parse_mode="Markdown")
        await update.message.reply_text("✅ আপনার উইথড্র রিকোয়েস্টটি পাঠানো হয়েছে!")
        USER_STATES[user_id] = None
        return

    # মেইন মেনু বাটন লজিক
    if text == '📝 কাজ •':
        sub_keyboard = [['ইনস্টাগ্রাম কাজ >'], ['⬅️ ফিরে যান']]
        await update.message.reply_text("সিলেক্ট করুন:", reply_markup=ReplyKeyboardMarkup(sub_keyboard, resize_keyboard=True))

    elif text == 'ইনস্টাগ্রাম কাজ >':
        USER_STATES[user_id] = 'WAITING_FOR_ID'
        await update.message.reply_text("👇 আপনার ইনস্টাগ্রাম আইডি বা কাজের লিংকটি লিখে সেন্ড করুন:", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))

    elif text == '💰 টাকা উত্তোলন':
        withdraw_kbd = [['bKash - সর্বনিম্ন: ১১০৳(-৫)', 'Nagad - সর্বনিম্ন: ১০০৳(-৫)'], ['⬅️ ফিরে যান']]
        await update.message.reply_text("📩 মাধ্যম সিলেক্ট করুন:", reply_markup=ReplyKeyboardMarkup(withdraw_kbd, resize_keyboard=True))

    elif text == 'bKash - সর্বনিম্ন: ১১০৳(-৫)':
        USER_STATES[user_id] = 'WAITING_FOR_BKASH'
        await update.message.reply_text("👇 বিকাশ নাম্বার ও অ্যামাউন্ট লিখে পাঠান:\n(যেমন: 017XXXXXXX - 110 TK)", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))

    elif text == 'Nagad - সর্বনিম্ন: ১০০৳(-৫)':
        USER_STATES[user_id] = 'WAITING_FOR_NAGAD'
        await update.message.reply_text("👇 নগদ নাম্বার ও অ্যামাউন্ট লিখে পাঠান:\n(যেমন: 019XXXXXXX - 100 TK)", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))

    elif text == '💵 ব্যালেন্স':
        bal_text = "💰 **আপনার ব্যালেন্স**\n━━━━━━━━━━━━\n🔥 ব্যালেন্স: 0.00 BDT\n📥 পেন্ডিং: 0.00 BDT\n🍏 Total Income: 0.00 BDT\n━━━━━━━━━━━━\n✅ সম্পন্ন কাজ: 0 টি"
        await update.message.reply_text(bal_text, parse_mode="Markdown")

    elif text == '⬅️ ফিরে যান':
        await start(update, context)

    elif text == '🎁 My Referrals':
        await update.message.reply_text("🔗 আপনার রেফারেল লিংক: (এখানে লিংক জেনারেট হবে)")

    elif text == '🎧 সাপোর্ট':
        await update.message.reply_text("যেকোনো সমস্যায় আমাদের এডমিনের সাথে যোগাযোগ করুন।✅ @nafin_4x_team")

    elif text == '🙋‍♂️ আমি নতুন':
        await update.message.reply_text("বটে কীভাবে কাজ করবেন তা জানতে আমাদের চ্যানেল এ join হন✅ https://t.me/OfficialInstagramSellBD")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
    
