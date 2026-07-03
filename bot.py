from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 WELCOME OUR OFFICIAL INSTAGRAM BOT BD")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler(from telegram import ReplyKeyboardMarkup

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
    ))

app.run_polling()
