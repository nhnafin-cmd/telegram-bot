import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# /start কমান্ড দিলে এই মেনু আসবে
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # প্রধান মেনুর বাটনগুলো তৈরি করা হলো
    keyboard = [
        ['📝 কাজ •', '💵 ব্যালেন্স'],
        ['💰 টাকা উত্তোলন', '🎁 My Referrals'],
        ['🎧 সাপোর্ট', '🙋‍♂️ আমি নতুন']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 WELCOME OUR OFFICIAL INSTAGRAM SELL BOT BD 🤗✅", 
        reply_markup=reply_markup
    )

# বাটনগুলোর ক্লিকের রেসপন্স হ্যান্ডেল করার ফাংশন
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == '📝 কাজ •':
        # 'কাজ' বাটনে চাপ দিলে সাব-মেনু আসবে
        sub_keyboard = [
            ['ইনস্টাগ্রাম কাজ >'],
            ['⬅️ ফিরে যান']
        ]
        sub_markup = ReplyKeyboardMarkup(sub_keyboard, resize_keyboard=True)
        await update.message.reply_text("সিলেক্ট করুন:", reply_markup=sub_markup)

    elif text == 'ইনস্টাগ্রাম কাজ >':
        await update.message.reply_text("এখানে আপনার ইনস্টাগ্রামের কাজের ডিটেইলস বা লিংক দিন।")

    elif text == '⬅️ ফিরে যান':
        # আবার মেইন মেনুতে ব্যাক করবে
        await start(update, context)

    elif text == '💵 ব্যালেন্স':
        await update.message.reply_text("💰 আপনার বর্তমান ব্যালেন্স: 0.00 টাকা")

    elif text == '💰 টাকা উত্তোলন':
        await update.message.reply_text("বিকাশ বা নগদে টাকা তুলতে মিনিমাম অ্যামাউন্ট প্রয়োজন।")

    elif text == '🎁 My Referrals':
        await update.message.reply_text("🔗 আপনার রেফারেল লিংক: (এখানে লিংক জেনারেট হবে)")

    elif text == '🎧 সাপোর্ট':
        await update.message.reply_text("যেকোনো সমস্যায় আমাদের এডমিনের সাথে যোগাযোগ করুন✅ @nafin_4x_team")

    elif text == '🙋‍♂️ আমি নতুন':
        await update.message.reply_text("বটে কীভাবে কাজ করবেন তা জানতে আমাদের গাইডলাইনটি পড়ুন।")

def main():
    app = Application.builder().token(TOKEN).build()
    
    # হ্যান্ডলারগুলো যোগ করা হচ্ছে
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("বটটি সফলভাবে চালু হয়েছে...")
    app.run_polling()

if __name__ == '__main__':
    main()
        
