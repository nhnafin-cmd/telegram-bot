import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("8812541901:AAF12HU1Gp2A9arTLaS_manzrS1euql2q4c")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📋 কাজ ▸"],
        ["💰 ব্যালেন্স", "💸 টাকা উত্তোলন"],
        ["👥 My Referrals"],
        ["🛠️ সাপোর্ট", "🆕 আমি নতুন"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🎉 WELCOME TO OFFICIAL INSTAGRAM SELL BD BOT\n\n"
        "নিচের মেনু থেকে একটি অপশন নির্বাচন করুন।",
        reply_markup=reply_markup
    )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

app.run_polling()
    
