import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@OfficialInstagramSellBD"
ADMIN_ID = 7831606559  # ⚠️ এখানে আপনার আসল টেলিগ্রাম আইডি দিন

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
    if user_id in USER_DATA: del USER_DATA[user_id]
    
    if user_id not in USER_BALANCES:
        USER_BALANCES[user_id] = 0.0
        save_balances(USER_BALANCES)
    
    if await is_user_joined(context, user_id):
        keyboard = [
            ['📝 কাজ •', '💵 ব্যালেন্স'], 
            ['💰 টাকা উত্তোলন', '🎁 My Referrals'], 
            ['🎧 সাপোর্ট', '🙋‍♂️ আমি নতুন']
        ]
        await update.message.reply_text("🌷 স্বাগতম আমাদের Official Instagram Sell BD Bot এ 🫠🤗", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    else:
        await update.message.reply_text(f"❌ প্রথমে আমাদের চ্যানেলে জয়েন করুন: {CHANNEL_USERNAME}\nতারপর নিচে '✅ Joined ✅' বাটনে চাপ দিন।", reply_markup=ReplyKeyboardMarkup([['✅ Joined ✅']], resize_keyboard=True))

# এডমিন কমান্ড: /add ইউজার_আইডি পরিমাণ
async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id, amount = int(context.args[0]), float(context.args[1])
        USER_BALANCES[target_id] = USER_BALANCES.get(target_id, 0.0) + amount
        save_balances(USER_BALANCES)
        await update.message.reply_text(f"✅ সফলভাবে যোগ হয়েছে: {amount}৳\n👤 ইউজার আইডি: {target_id}\n🔥 বর্তমান ব্যালেন্স: {USER_BALANCES[target_id]}৳")
        
        # ইউজারকে নোটিফিকেশন পাঠানো
        try:
            await context.bot.send_message(chat_id=target_id, text=f"💰 আপনার অ্যাকাউন্টে এডমিন {amount} BDT যোগ করেছেন!\n🔥 বর্তমান ব্যালেন্স: {USER_BALANCES[target_id]} BDT")
        except: pass
    except: 
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন: `/add ইউজার_আইডি পরিমাণ` \nযেমন: `/add 783160655 50`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "No Username"
    first_name = update.effective_user.first_name
    text = update.message.text

    if text == '✅ Joined ✅':
        if await is_user_joined(context, user_id): await start(update, context)
        else: await update.message.reply_text("⚠️ আপনি এখনো জয়েন করেননি!")
        return

    if not await is_user_joined(context, user_id): return

    # [কাজ জমা নেওয়ার লজিক]
    if USER_STATES.get(user_id) == 'WAITING_FOR_ID':
        if '⬅️ ফিরে যান' in text:
            USER_STATES[user_id] = None
            await start(update, context)
            return
        msg = f"📥 **নতুন কাজ জমা পড়েছে!**\n\n👤 নাম: {first_name}\n🆔 আইডি: `{user_id}`\n🔗 @{username}\n\n📝 **লিংক/আইডি:**\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
        await update.message.reply_text("✅ আপনার ইনস্টাগ্রাম আইডি/লিংকটি সফলভাবে জমা হয়েছে!")
        USER_STATES[user_id] = None
        return

    # [টাকা উত্তোলন - নাম্বার ইনপুট]
    if USER_STATES.get(user_id) in ['WAITING_FOR_BKASH_NUMBER', 'WAITING_FOR_NAGAD_NUMBER']:
        if '⬅️ ফিরে যান' in text:
            USER_STATES[user_id] = None
            await start(update, context)
            return
        if user_id not in USER_DATA: USER_DATA[user_id] = {}
        USER_DATA[user_id]['number'] = text
        
        # কোন মাধ্যমে টাকা তুলছে সেটা ট্র্যাকিং-এর জন্য সেভ রাখা
        method_type = "BKASH" if USER_STATES[user_id] == 'WAITING_FOR_BKASH_NUMBER' else "NAGAD"
        USER_DATA[user_id]['method'] = method_type
        
        USER_STATES[user_id] = 'WAITING_FOR_AMOUNT'
        min_limit = "১১০৳" if method_type == "BKASH" else "১০০৳"
        await update.message.reply_text(f"👇 কত টাকা উত্তোলন করতে চান? (সর্বনিম্ন {min_limit}):", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
        return

    # [টাকা উত্তোলন - অ্যামাউন্ট ভেরিফিকেশন]
    if USER_STATES.get(user_id) == 'WAITING_FOR_AMOUNT':
        if '⬅️ ফিরে যান' in text:
            USER_STATES[user_id] = None
            if user_id in USER_DATA: del USER_DATA[user_id]
            await start(update, context)
            return
        try:
            amt = float(text)
            saved_method = USER_DATA.get(user_id, {}).get('method', 'BKASH')
            method_name = "বিকাশ" if saved_method == "BKASH" else "নগদ"
            min_amt = 110.0 if saved_method == "BKASH" else 100.0
            
            if amt < min_amt:
                await update.message.reply_text(f"❌ রিকোয়েস্ট ক্যানসেল! {method_name}-এ সর্বনিম্ন {min_amt:.0f}৳ উত্তোলন করতে হবে।")
                USER_STATES[user_id] = None
                if user_id in USER_DATA: del USER_DATA[user_id]
                return
                
            if USER_BALANCES.get(user_id, 0.0) < amt:
                await update.message.reply_text(f"❌ রিকোয়েস্ট ক্যানসেল! আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই।\n🔥 বর্তমান ব্যালেন্স: {USER_BALANCES.get(user_id, 0.0):.2f} BDT")
            else:
                USER_BALANCES[user_id] -= amt
                save_balances(USER_BALANCES)
                num = USER_DATA.get(user_id, {}).get('number', 'N/A')
                
                admin_msg = f"💰 **উইথড্র রিকোয়েস্ট!**\n\n👤 নাম: {first_name}\n🆔 আইডি: `{user_id}`\n💳 মাধ্যম: {method_name}\n📱 নাম্বার: `{num}`\n💵 পরিমাণ: **{amt:.2f} BDT**"
                await context.bot.send_message(ADMIN_ID, text=admin_msg, parse_mode="Markdown")
                await update.message.reply_text(f"✅ আপনার উইথড্র রিকোয়েস্টটি সফল হয়েছে!\n📉 কেটে নেওয়া হয়েছে: {amt:.2f} BDT\n🔥 বর্তমান মূল ব্যালেন্স: {USER_BALANCES[user_id]:.2f} BDT")
        except ValueError:
            await update.message.reply_text("❌ ভুল অ্যামাউন্ট! শুধুমাত্র সংখ্যায় টাকার পরিমাণ লিখুন।")
            
        USER_STATES[user_id] = None
        if user_id in USER_DATA: del USER_DATA[user_id]
        return

    # 🛠️ মেইন মেনু কন্ডিশন ফিক্সড (বাটনগুলোর সাথে ১০০% মিল রাখা হয়েছে)
    if '📝 কাজ •' in text:
        await update.message.reply_text("সিলেক্ট করুন:", reply_markup=ReplyKeyboardMarkup([['ইনস্টাগ্রাম কাজ >'], ['⬅️ ফিরে যান']], resize_keyboard=True))
    elif text == 'ইনস্টাগ্রাম কাজ >':
        USER_STATES[user_id] = 'WAITING_FOR_ID'
        await update.message.reply_text("👇 আইডি বা কাজের লিংকটি পাঠান:", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
    elif '💰 টাকা উত্তোলন' in text:
        await update.message.reply_text("📩 মাধ্যম সিলেক্ট করুন:", reply_markup=ReplyKeyboardMarkup([['bKash', 'Nagad'], ['⬅️ ফিরে যান']], resize_keyboard=True))
    elif text == 'bKash':
        USER_STATES[user_id] = 'WAITING_FOR_BKASH_NUMBER'
        await update.message.reply_text("👇 আপনার বিকাশ নাম্বারটি লিখুন:", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
    elif text == 'Nagad':
        USER_STATES[user_id] = 'WAITING_FOR_NAGAD_NUMBER'
        await update.message.reply_text("👇 আপনার নগদ নাম্বারটি লিখুন:", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
    elif '💵 ব্যালেন্স' in text:
        bal = USER_BALANCES.get(user_id, 0.0)
        await update.message.reply_text(f"💰 **আপনার ব্যালেন্স**\n━━━━━━━━━━━━\n🔥 ব্যালেন্স: {bal:.2f} BDT\n📥 পেন্ডিং: 0.00 BDT", parse_mode="Markdown")
    elif '🙋‍♂️ আমি নতুন' in text:
        await update.message.reply_text(f"আমাদের অফিশিয়াল চ্যানেলে জয়েন হয়ে কাজ শুরু করে দিন।\nLink: {CHANNEL_USERNAME}")
    elif '🎧 সাপোর্ট' in text:
        await update.message.reply_text("🎧 যেকোনো সমস্যায় সাপোর্ট আইডিতে মেসেজ দিন:\n👉 @nafin_4x_team")
    elif '🎁 My Referrals' in text:
        await update.message.reply_text("🎁 আপনার রেফারেল সিস্টেমটি খুব শীঘ্রই চালু করা হবে!")
    elif '⬅️ ফিরে যান' in text: 
        await start(update, context)
    else: 
        await update.message.reply_text("আমি বুঝতে পারিনি। অনুগ্রহ করে নিচের বাটনগুলো ব্যবহার করুন।")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_balance))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__': main()
                                                   
