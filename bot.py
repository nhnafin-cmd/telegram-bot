import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
# আপনার চ্যানেলের ইউজারনেম
CHANNEL_USERNAME = "@OfficialInstagramSellBD"

# ⚠️ এইখানে আপনার নিজের টেলিগ্রাম ইউজার আইডি বসান (যেমন: 584930291)
ADMIN_ID = 7831606559

# ইউজার কোন স্টেটে আছে তা ট্র্যাক করার জন্য ডিকশনারি
USER_STATES = {}

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
    USER_STATES[user_id] = None  # স্টেট ক্লিয়ার করা
    
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
            "🌷স্বাগতম আমাদের Official Instagram Sell BD Bot এ 🫠🤗", 
            reply_markup=reply_markup
        )
    else:
        # জয়েন না থাকলে এই সাধারণ বাটন মেনুটি দেখাবে
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
    username = update.effective_user.username or "No Username"
    first_name = update.effective_user.first_name
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

    # 📥 ইউজার যদি এখন আইডি জমা দেওয়ার স্টেটে থাকে (নতুন অংশ)
    if USER_STATES.get(user_id) == 'WAITING_FOR_ID':
        if text == '⬅️ ফিরে যান':
            USER_STATES[user_id] = None
            await start(update, context)
            return

        # আপনার জন্য সাজানো মেসেজ ফরম্যাট
        admin_message = (
            "📥 **নতুন কাজ জমা পড়েছে!**\n\n"
            f"👤 নাম: {first_name}\n"
            f"🆔 ইউজার আইডি: `{user_id}`\n"
            f"🔗 ইউজারনেম: @{username}\n\n"
            f"📝 **জما দেওয়া আইডি/লিংক:**\n{text}"
        )
        
        try:
            # সরাসরি আপনার পার্সোনাল আইডিতে ডেটা চলে যাবে
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode="Markdown")
            await update.message.reply_text("✅ আপনার ইনস্টাগ্রাম আইডিটি সফলভাবে এডমিনের কাছে জমা হয়েছে! এডমিন চেক করে ব্যালেন্স অ্যাড করে দেবে।")
        except Exception as e:
            await update.message.reply_text("❌ কারিগরি সমস্যার কারণে জমা নেওয়া যায়নি। এডমিনকে বলুন ADMIN_ID ঠিক করতে।")
            print(f"Error sending to admin: {e}")
            
        USER_STATES[user_id] = None  # কাজ শেষ, স্টেট নরমাল করা
        return

    # আপনার আগের আসল বাটনগুলোর লজিক
    if text == '📝 কাজ •':
        sub_keyboard = [
            ['ইনস্টাগ্রাম কাজ >'],
            ['⬅️ ফিরে যান']
        ]
        sub_markup = ReplyKeyboardMarkup(sub_keyboard, resize_keyboard=True)
        await update.message.reply_text("সিলেক্ট করুন:", reply_markup=sub_markup)

    elif text == 'ইনস্টাগ্রাম কাজ >':
        # ইউজারকে ইনপুট স্টেটে নিয়ে যাওয়া হলো
        USER_STATES[user_id] = 'WAITING_FOR_ID'
        back_keyboard = [['⬅️ ফিরে যান']]
        back_markup = ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
        await update.message.reply_text("👇 দয়া করে আপনার ইনস্টাগ্রাম আইডি বা কাজের লিংকটি এখানে লিখে সেন্ড করুন:", reply_markup=back_markup)

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
        await update.message.reply_text("বটে কীভাবে কাজ করবেন তা জানতে আমাদের চেনেল এ join হন✅ https://t.me/OfficialInstagramSellBD")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("বটটি সফলভাবে চালু হয়েছে...")
    app.run_polling()

if __name__ == '__main__':
    main()
