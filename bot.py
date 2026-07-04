import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@OfficialInstagramSellBD"

# ⚠️ এইখানে আপনার নিজের টেলিগ্রাম ইউজার আইডি বসান
ADMIN_ID = 7831606559

# ইউজার কোন স্টেটে আছে এবং কী ডেটা দিচ্ছে তা ট্র্যাক করার জন্য ডিকশনারি
USER_STATES = {}
USER_DATA = {}

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
    if user_id in USER_DATA: del USER_DATA[user_id]
    
    if await is_user_joined(context, user_id):
        keyboard = [
            ['📝 কাজ •', '💵 ব্যালেন্স'],
            ['💰 টাকা উত্তোলন', '🎁 My Referrals'],
            ['🎧 সাপোর্ট', '🙋‍♂️ আমি নতুন']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("🌷স্বাগতম আমাদের Official Instagram Sell BD Bot এ 🫠🤗", reply_markup=reply_markup)
    else:
        keyboard = [['✅ Joined ✅']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"❌ আপনি আমাদের চ্যানেলে জয়েন করেননি।\nপ্রথমে জয়েন করুন: {CHANNEL_USERNAME}\nতারপর নিচে '✅ Joined ✅' বাটনে চাপ দিন।", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "No Username"
    first_name = update.effective_user.first_name
    text = update.message.text

    if text == '✅ Joined ✅':
        if await is_user_joined(context, user_id): await start(update, context)
        else: await update.message.reply_text("⚠️ আপনি এখনো জয়েন করেননি!")
        return

    if not await is_user_joined(context, user_id):
        await update.message.reply_text(f"⚠️ আগে চ্যানেলে জয়েন থাকতে হবে!\nLink: {CHANNEL_USERNAME}")
        return

    # [কাজ জমা]
    if USER_STATES.get(user_id) == 'WAITING_FOR_ID':
        if text == '⬅️ ফিরে যান': 
            USER_STATES[user_id] = None
            await start(update, context)
            return
        msg = f"📥 **নতুন কাজ জমা পড়েছে!**\n\n👤 নাম: {first_name}\n🆔 আইডি: `{user_id}`\n🔗 @{username}\n\n📝 **লিংক:**\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
        await update.message.reply_text("✅ আপনার ইনস্টাগ্রাম আইডিটি সফলভাবে জমা হয়েছে!")
        USER_STATES[user_id] = None
        return

    # [টাকা উত্তোলন - ধাপ ১: নাম্বার]
    if USER_STATES.get(user_id) in ['WAITING_FOR_BKASH_NUMBER', 'WAITING_FOR_NAGAD_NUMBER']:
        if text == '⬅️ ফিরে যান':
            USER_STATES[user_id] = None
            await start(update, context)
            return
        if user_id not in USER_DATA: USER_DATA[user_id] = {}
        USER_DATA[user_id]['number'] = text
        if USER_STATES[user_id] == 'WAITING_FOR_BKASH_NUMBER':
            USER_STATES[user_id] = 'WAITING_FOR_BKASH_AMOUNT'
            await update.message.reply_text("👇 কত টাকা উত্তোলন করতে চান? (যেমন: 110 TK)", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
        else:
            USER_STATES[user_id] = 'WAITING_FOR_NAGAD_AMOUNT'
            await update.message.reply_text("👇 কত টাকা উত্তোলন করতে চান? (যেমন: 100 TK)", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
        return

    # [টাকা উত্তোলন - ধাপ ২: অ্যামাউন্ট ও সেন্ডিং]
    if USER_STATES.get(user_id) in ['WAITING_FOR_BKASH_AMOUNT', 'WAITING_FOR_NAGAD_AMOUNT']:
        if text == '⬅️ ফিরে যান':
            USER_STATES[user_id] = None
            await start(update, context)
            return
        method = "বিকাশ" if USER_STATES[user_id] == 'WAITING_FOR_BKASH_AMOUNT' else "নগদ"
        num = USER_DATA.get(user_id, {}).get('number', 'N/A')
        msg = f"💰 **উইথড্র রিকোয়েস্ট!**\n\n👤 {first_name}\n🆔 `{user_id}`\n💳 মাধ্যম: {method}\n📱 নাম্বার: `{num}`\n💵 পরিমাণ: **{text}**"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
        await update.message.reply_text("✅ আপনার উইথড্র রিকোয়েস্টটি এডমিনের কাছে পাঠানো হয়েছে!")
        USER_STATES[user_id] = None
        if user_id in USER_DATA: del USER_DATA[user_id]
        return

    # মেইন মেনু হ্যান্ডলিং
    if text == '📝 কাজ •':
        await update.message.reply_text("সিলেক্ট করুন:", reply_markup=ReplyKeyboardMarkup([['ইনস্টাগ্রাম কাজ >'], ['⬅️ ফিরে যান']], resize_keyboard=True))
    elif text == 'ইনস্টাগ্রাম কাজ >':
        USER_STATES[user_id] = 'WAITING_FOR_ID'
        await update.message.reply_text("👇 আইডি বা কাজের লিংকটি পাঠান:", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
    elif text == '💰 টাকা উত্তোলন':
        await update.message.reply_text("📩 মাধ্যম সিলেক্ট করুন:", reply_markup=ReplyKeyboardMarkup([['bKash - সর্বনিম্ন: ১১০৳(-৫)', 'Nagad - সর্বনিম্ন: ১০০৳(-৫)'], ['⬅️ ফিরে যান']], resize_keyboard=True))
    elif 'bKash' in text:
        USER_STATES[user_id] = 'WAITING_FOR_BKASH_NUMBER'
        await update.message.reply_text("👇 আপনার বিকাশ নাম্বারটি লিখুন:", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
    elif 'Nagad' in text:
        USER_STATES[user_id] = 'WAITING_FOR_NAGAD_NUMBER'
        await update.message.reply_text("👇 আপনার নগদ নাম্বারটি লিখুন:", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
    elif text == '💵 ব্যালেন্স':
        await update.message.reply_text("💰 **আপনার ব্যালেন্স**\n🔥 ব্যালেন্স: 0.00 BDT\n📥 পেন্ডিং: 0.00 BDT", parse_mode="Markdown")
    elif text == '⬅️ ফিরে যান': await start(update, context)
    elif text == '🎧 সাপোর্ট': await update.message.reply_text("সাপোর্ট: @nafin_4x_team")
    elif text == '🙋‍♂️ আমি নতুন': await update.message.reply_text("চ্যানেলে জয়েন হন: " + CHANNEL_USERNAME)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__': main()
        
