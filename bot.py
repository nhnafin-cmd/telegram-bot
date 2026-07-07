import logging
import random
import pyotp
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# লগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

USER_STATES = {}

# 📲 ১. /start দিলে যে মেইন মেনু আসবে (হুবহু স্ক্রিনশটের টেক্সট ও ইমোজি)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_STATES[user_id] = 7831606559 
    
    # স্ক্রিনশট ১ অনুযায়ী স্বাগতম মেসেজ
    welcome_text = (
        "🧝🏻‍♀️ **স্বাগতম, 💞LEADER💞 👨🏻‍🎤NAGI🎧!**\n"
        "🔹 কাজ শুরু করতে নিচের অপশনগুলো ব্যবহার করুন 🔻"
    )
    
    # স্ক্রিনশটের মেইন ৬টি কালারফুল কীবোর্ড বাটন লেআউট
    main_keyboard = [
        ['📝 কাজ ▸', '💵 ব্যালেন্স'],
        ['💰 টাকা উত্তোলন', '🎁 My Referrals'],
        ['🎯 সাপোর্ট', '👶 আমি নতুন']
    ]
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

# 🔄 ২. বাটন ও টেক্সট মেসেজ হ্যান্ডেলার (স্ক্রিনশটের সব মেনু এখানে আছে)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # '🔙 ফিরে যান' বাটনে চাপ দিলে মেইন মেনুতে নিয়ে যাবে
    if text == "🔙 ফিরে যান":
        USER_STATES[user_id] = None
        await start(update, context)
        return

    # '📝 কাজ ▸' বাটনে চাপ দিলে (স্ক্রিনশট ১ ও ২ অনুযায়ী)
    if text == "📝 কাজ ▸":
        keyboard = [[InlineKeyboardButton("📱 ইনস্টাগ্রাম কাজ >", callback_data="insta_category")]]
        await update.message.reply_text("সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # '💵 ব্যালেন্স' বাটনে চাপ দিলে (স্ক্রিনশট ৬ অনুযায়ী হুবহু টেক্সট)
    if text == "💵 ব্যালেন্স":
        balance_msg = (
            "💰 **আপনার ব্যালেন্স**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🔥 **ব্যালেন্স:** 3.00 BDT\n"
            "📂 **পেন্ডিং (উইথড্র):** 0.00 BDT\n"
            "💹 **Total Income:** 300.09 BDT\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "✅ **সম্পন্ন কাজ:** 97 টি\n"
            "⏳ **রিভিউতে আছে:** 2 টি"
        )
        await update.message.reply_text(balance_msg, parse_mode="Markdown")
        return

    # '🎁 My Referrals' বাটনে চাপ দিলে (স্ক্রিনশট ৭ অনুযায়ী হুবহু টেক্সট)
    if text == "🎁 My Referrals":
        refer_msg = (
            "🎁 **My Referrals**\n"
            "👤 Total Refer: 4\n"
            "💲 Total Refer Income: 14.70 BDT\n"
            "🔗 **আপনার রেফার লিংক:**\n"
            f"https://t.me/EasyIncomeXBot?start={user_id}\n\n"
            "📢 আপনি আপনার প্রতিটি রেফারেলের সম্পূর্ণ করা কাজ থেকে আয়ের ১০% কমিশন পাবেন।\n"
            "📌 বিস্তারিত জানতে নিচের Rules বাটনে চাপ দিন ⤵️"
        )
        keyboard = [
            [InlineKeyboardButton("📜 Rules", callback_data="show_rules")],
            [InlineKeyboardButton("👥 Team Leaderboard", callback_data="show_leaderboard")]
        ]
        await update.message.reply_text(refer_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # '🎯 সাপোর্ট' বাটনে চাপ দিলে (স্ক্রিনশট ৮ ও ৯ অনুযায়ী হুবহু টেক্সট)
    if text == "🎯 সাপোর্ট":
        support_msg = (
            "📞 **গ্রাহক সেবা কেন্দ্র**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "সম্মানিত মেম্বার,\n"
            "আপনার যেকোনো সমস্যা বা জিজ্ঞাসার জন্য আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করুন। আমরা দ্রুত সমাধানের চেষ্টা করব।\n\n"
            "⚠️ **নোট:** অযথা মেসেজ দেওয়া থেকে বিরত থাকুন। ধন্যবাদ!"
        )
        keyboard = [
            [InlineKeyboardButton("✅ 🕵🏻‍♂️ অ্যাডমিন সাপোর্ট", url="https://t.me/your_admin_username")],
            [InlineKeyboardButton("📢 অফিশিয়াল চ্যানেল", url="https://t.me/your_channel_username")]
        ]
        await update.message.reply_text(support_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # '👶 আমি নতুন' বাটনে চাপ দিলে (স্ক্রিনশট ৯ অনুযায়ী হুবহু টেক্সট)
    if text == "👶 আমি নতুন":
        newbie_msg = (
            "🆕✨ আপনি যেহেতু নতুন, তাই আগে কাজ শিখতে হবে।\n\n"
            "নিচের কোন ক্যাটাগরির কাজ শিখতে চান সিলেক্ট করুন👇"
        )
        await update.message.reply_text(newbie_msg, parse_mode="Markdown")
        return

    # ইউজার যদি ২এফএ কি সাবমিট করার স্টেটে থাকে (স্ক্রিনশট ৪ ও ৫ অনুযায়ী ওটিপি জেনারেশন)
    if USER_STATES.get(user_id) == 'WAITING_FOR_2FA':
        clean_key = text.replace(" ", "").upper().rstrip('=')
        try:
            missing_padding = len(clean_key) % 8
            if missing_padding:
                clean_key += '=' * (8 - missing_padding)
            totp = pyotp.TOTP(clean_key)
            real_otp = totp.now()
        except Exception:
            real_otp = None

        if real_otp and real_otp.isdigit():
            # ওটিপি কোড জেনারেট হলে স্ক্রিনশট ৪ এর মতো মেসেজ ও কপি বাটন আসবে
            response_text = "নিচের বাটনে চাপ দিয়ে কোডটি কপি করুন ⤵️"
            keyboard = [
                [InlineKeyboardButton(f"📋 🗳️ {real_otp}", callback_data=f"copy_{real_otp}")],
                [InlineKeyboardButton("✅ অ্যাকাউন্ট খোলা শেষ", callback_data="finish_task")]
            ]
            await update.message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard))
            USER_STATES[user_id] = None
        else:
            await update.message.reply_text("⚠️ **ভুল ২এফএ কি!** দয়া করে সঠিক কি-টি কপি করে আবার পাঠান।")

# 🔘 ৩. ইনলাইন ক্লিক বা সাব-মেনু হ্যান্ডেলার
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # '📱 ইনস্টাগ্রাম কাজ >' বাটনে ক্লিক করলে রেট বাটন আসবে (স্ক্রিনশট ১ ও ২ অনুযায়ী)
    if query.data == "insta_category":
        keyboard = [[InlineKeyboardButton("📸 ইনস্টাগ্রাম 2fa (৳৩.০০)", callback_data="start_insta_job")]]
        await query.message.reply_text("সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
        
    # রেট বাটনে ক্লিক করলে ইউজারনেম-পাসওয়ার্ড ও 2FA Set বাটন আসবে (স্ক্রিনশট ২ ও ৩ অনুযায়ী)
    if query.data == "start_insta_job":
        random_suffix = random.randint(10, 99)
        generated_username = f"mirniackumarbb{random_suffix}"
        current_password = f"kamrol@07"
        
        USER_STATES[user_id] = 'WAITING_FOR_2FA'
        
        task_msg = (
            f"👤 Username: `{generated_username}`\n"
            f"🔐 Password: `{current_password}`\n\n"
            "📸 উপরের ইউজারনেম এবং পাসওয়ার্ড দিয়ে অ্যাকাউন্ট খুলুন। তারপর নিচে 2FA Set বাটন ক্লিক করুন 🤪"
        )
        
        keyboard = [[InlineKeyboardButton("🔐 2FA Set", callback_data="show_2fa_prompt")]]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=task_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # '🔐 2FA Set' বাটনে ক্লিক করলে কি (Key) চাওয়ার প্রম্পট (স্ক্রিনশট ৩ ও ৪ অনুযায়ী)
    if query.data == "show_2fa_prompt":
        # নিচে '❌ বাতিল' কীবোর্ড বাটন সেট হবে
        cancel_markup = ReplyKeyboardMarkup([['❌ বাতিল']], resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="🔑 **2FA Key টি দিন:** ⤵️", parse_mode="Markdown", reply_markup=cancel_markup)
        return
        
    # '✅ অ্যাকাউন্ট খোলা শেষ' বাটনে ক্লিক করলে সাকসেস মেসেজ (স্ক্রিনশট ৫ ও ৬ অনুযায়ী)
    if query.data == "finish_task":
        success_msg = (
            "👍 **আপনার কাজ সফলভাবে গ্রহণ করা হয়েছে।**\n\n"
            "📢 পেমেন্ট ঠিক কখন পাবেন, সেই আপডেট এই গ্রুপেই জানিয়ে দেওয়া হবে।\n"
            "https://t.me/instagramsellbdbot"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=success_msg, parse_mode="Markdown")
        
        # আবার মেইন মেনু কীবোর্ড ফিরিয়ে আনা
        await start(update, context)
        return

# 🚀 ৪. মেইন ইঞ্জিন
def main():
    # 🛑 নিচে আপনার আসল টোকেনটি কোটেশনের ভেতরে বসিয়ে দিন
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 আপনার হুবহু ডিজাইনের ওটিপি বট সফলভাবে চালু হয়েছে...")
    app.run_polling()

if __name__ == '__main__':
    main()
                         
