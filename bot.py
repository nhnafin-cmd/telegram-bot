import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@OfficialInstagramSellBD"
ADMIN_ID = 7831606559  # ⚠️ এখানে আপনার আইডি দিন

BALANCE_FILE = "balances.json"

# ব্যালেন্স লোড এবং সেভ করার সিস্টেম
def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            try: return {int(k): float(v) for k, v in json.load(f).items()}
            except: return {}
    return {}

def save_balances(balances):
    with open(BALANCE_FILE, "w") as f:
        json.dump(balances, f, indent=4)

USER_BALANCES = load_balances()
USER_STATES = {}
USER_DATA = {}

async def is_user_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_STATES[user_id] = None
    if user_id not in USER_BALANCES:
        USER_BALANCES[user_id] = 0.0
        save_balances(USER_BALANCES)
    
    if await is_user_joined(context, user_id):
        keyboard = [['📝 কাজ •', '💵 ব্যালেন্স'], ['💰 টাকা উত্তোলন', '🎁 My Referrals'], ['🎧 সাপোর্ট', '🙋‍♂️ আমি নতুন']]
        await update.message.reply_text("🌷 স্বাগতম Official Instagram Sell BD Bot এ!", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    else:
        await update.message.reply_text(f"❌ প্রথমে চ্যানেলে জয়েন করুন: {CHANNEL_USERNAME}", reply_markup=ReplyKeyboardMarkup([['✅ Joined ✅']], resize_keyboard=True))

# এডমিন কমান্ড: /add ইউজার_আইডি পরিমাণ
async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id, amount = int(context.args[0]), float(context.args[1])
        USER_BALANCES[target_id] = USER_BALANCES.get(target_id, 0.0) + amount
        save_balances(USER_BALANCES)
        await update.message.reply_text(f"✅ যোগ হয়েছে: {amount}৳\nইউজার: {target_id}\nবর্তমান: {USER_BALANCES[target_id]}৳")
    except: await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন: /add আইডি পরিমাণ")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text == '✅ Joined ✅':
        if await is_user_joined(context, user_id): await start(update, context)
        else: await update.message.reply_text("⚠️ এখনো জয়েন করেননি!")
        return

    if not await is_user_joined(context, user_id): return

    # টাকা উত্তোলন লজিক
    if USER_STATES.get(user_id) in ['WAITING_FOR_BKASH_NUMBER', 'WAITING_FOR_NAGAD_NUMBER']:
        if user_id not in USER_DATA: USER_DATA[user_id] = {}
        USER_DATA[user_id]['number'] = text
        USER_STATES[user_id] = 'WAITING_FOR_AMOUNT'
        await update.message.reply_text("👇 কত টাকা তুলতে চান? (যেমন: 100)")
        return

    if USER_STATES.get(user_id) == 'WAITING_FOR_AMOUNT':
        try:
            amt = float(text)
            method = "বিকাশ" if 'BKASH' in str(USER_STATES.get(user_id)) else "নগদ"
            if amt < 100 or USER_BALANCES.get(user_id, 0) < amt:
                await update.message.reply_text("❌ রিকোয়েস্ট ক্যানসেল! পর্যাপ্ত ব্যালেন্স নেই বা অ্যামাউন্ট কম।")
            else:
                USER_BALANCES[user_id] -= amt
                save_balances(USER_BALANCES)
                await context.bot.send_message(ADMIN_ID, f"💰 উইথড্র রিকোয়েস্ট!\nআইডি: {user_id}\nমাধ্যম: {method}\nটাকা: {amt}")
                await update.message.reply_text("✅ রিকোয়েস্ট সফল!")
        except: await update.message.reply_text("❌ ভুল অ্যামাউন্ট!")
        USER_STATES[user_id] = None
        return

    # মেনু হ্যান্ডলিং
    if text == '💰 টাকা উত্তোলন':
        await update.message.reply_text("মাধ্যম বেছে নিন:", reply_markup=ReplyKeyboardMarkup([['bKash', 'Nagad'], ['⬅️ ফিরে যান']], resize_keyboard=True))
    elif text in ['bKash', 'Nagad']:
        USER_STATES[user_id] = 'WAITING_FOR_BKASH_NUMBER' if text == 'bKash' else 'WAITING_FOR_NAGAD_NUMBER'
        await update.message.reply_text("আপনার নাম্বারটি দিন:")
    elif text == '💵 ব্যালেন্স':
        await update.message.reply_text(f"🔥 বর্তমান ব্যালেন্স: {USER_BALANCES.get(user_id, 0):.2f} BDT")
    elif text == '⬅️ ফিরে যান': await start(update, context)
    else: await update.message.reply_text("আমি বুঝতে পারিনি।")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_balance))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()

if __name__ == '__main__': main()
        
