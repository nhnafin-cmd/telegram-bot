import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
# আপনার চ্যানেলের ইউজারনেম (অবশ্যই বটকে এই চ্যানেলের অ্যাডমিন বানাতে হবে)
CHANNEL_USERNAME = "@OfficialInstagramSellBD"

# ইউজার চ্যানেলে জয়েন আছে কি না তা চেক করার সহজ ফাংশন
async def is_user_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except BadRequest:
        return False

# /start কমান্ড দিলে এই মেনু আসবে
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # প্রথমে চেক করবে ইউজার জয়েন করেছে কি না
    if await is_user_joined(context, user_id):
        # জয়েন থাকলে মেইন মেনুর বাটনগুলো তৈরি করা হলো
        keyboard = [
            ['📝 কাজ •', '💵 ব্যালেন্স'],
            ['💰 টাকা উত্তোলন', '🎁 My Referrals'],
            ['🎧 সাপোর্ট', '🙋‍♂️ আমি নতুন']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🤖 WELCOME OUR OFFICIAL INSTAGRAM BOT BD", 
            reply_markup=reply_markup
        )
    else:
        # জয়েন না থাকলে এই সাধারণ বাটন মেনুটি দেখাবে (কোনো কাস্টম জটিল বাটন ছাড়া)
        keyboard = [
            ['✅ Joined ✅']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"❌ আপনি আমাদের অফিশিয়াল চ্যানেলে জয়েন করেননি।\n\n"
            f"প্রথমে এখানে ক্লিক করে জয়েন করুন: {CHANNEL_USERNAME}\n\n"
            f"তারপর নিচে '✅ Joined ✅' বাটনে চাপ দিন।",
            reply_markup=reply_markup
        )

# বাটনগুলোর ক্লিকের রেসপন্স হ্যান্ডেল করার ফাংশন
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # যদি ইউজার '✅ Joined ✅' বাটনে চাপ দেয়
    if text == '✅ Joined ✅':
        if await is_user_joined(context, user_id):
            await start(update, context) # জয়েন থাকলে মেইন মেনু চালু হবে
        else:
            await update.message.reply_text("⚠️ আপনি এখনো জয়েন করেননি! দয়া করে আগে চ্যানেলে জয়েন করুন।")
        return

    # বাকি সব বাটনের জন্য আগে চেক করবে ইউজার এখনো চ্যানেলে আছে কি না
    if not await is_user_joined(context, user_id):
        keyboard = [['✅ Joined ✅']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"⚠️ সামনে আগানোর আগে আপনাকে অবশ্যই আমাদের চ্যানেলে জয়েন থাকতে হবে!\n"
            f"চ্যানেল লিংক: {CHANNEL_USERNAME}", 
            reply_markup=reply_markup
        )
        return

    # আপনার আগের আসল বাটনগুলোর লজিক (যা একদম ঠিকঠাক কাজ করছিল)
    if text == '📝 কাজ •':
        sub_keyboard = [
            ['ইনস্টাগ্রাম কাজ >'],
            ['⬅️ ফিরে যান']
        ]
        sub_markup = ReplyKeyboardMarkup(sub_keyboard, resize_keyboard=True)
        await update.message.reply_text("সিলেক্ট করুন:", reply_markup=sub_markup)

    elif text == 'ইনস্টাগ্রাম কাজ >':
        await update.message.reply_text("এখানে আপনার ইনস্টাগ্রামের কাজের ডিটেইলস বা লিংক দিন।")

    elif text == '⬅️ ফিরে যান':
        await start(update, context)

    elif text == '💵 ব্যালেন্স':
        await update.message.reply_text("💰 আপনার বর্তমান ব্যালেন্স: 0.00 টাকা")

    elif text == '💰 টাকা উত্তোলন':
        await update.message.reply_text("বিকাশ বা নগদে টাকা তুলতে মিনিমাপ অ্যামাউন্ট প্রয়োজন।")

    elif text == '🎁 My Referrals':
        await update.message.reply_text("🔗 আপনার রেফারেল লিংক: (এখানে লিংক জেনারেট হবে)")

    elif text == '🎧 সাপোর্ট':
        await update.message.reply_text("যেকোনো সমস্যায় আমাদের এডমিনের সাথে যোগাযোগ করুন।✅ @nafin_4x_team")

    elif text == '🙋‍♂️ আমি নতুন':
        await update.message.reply_text("বটে কীভাবে কাজ করবেন তা জানতে আমাদের গাইডলাইনটি পড়ুন।")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("বটটি সফলভাবে চালু হয়েছে...")
    app.run_polling()

if __name__ == '__main__':
    main()
        
