import os
import json
from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@OfficialInstagramSellBD"
ADMIN_ID = 7831606559  # ⚠️ এখানে আপনার আসল টেলিগ্রাম আইডি দিন

BALANCE_FILE = "balances.json"

# ডাটা লোড এবং সেভ করার সিস্টেম
def load_data():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            try:
                data = json.load(f)
                if "balances" not in data: data["balances"] = {}
                if "pending_counts" not in data: data["pending_counts"] = {}
                if "pending_links" not in data: data["pending_links"] = {}
                if "approved_counts" not in data: data["approved_counts"] = {}
                if "rejected_counts" not in data: data["rejected_counts"] = {}
                return data
            except:
                return {"balances": {}, "pending_counts": {}, "pending_links": {}, "approved_counts": {}, "rejected_counts": {}}
    return {"balances": {}, "pending_counts": {}, "pending_links": {}, "approved_counts": {}, "rejected_counts": {}}

def save_data(data):
    with open(BALANCE_FILE, "w") as f:
        json.dump(data, f, indent=4)

BOT_DATA = load_data()
USER_STATES = {}
USER_DATA = {}

# সাধারণ ইউজারদের জন্য কাস্টম কিবোর্ড লেআউট
USER_KEYBOARD = ReplyKeyboardMarkup([
    ['📝 কাজ •', '💵 ব্যালেন্স'], 
    ['💰 টাকা উত্তোলন', '🎁 My Referrals'], 
    ['🎧 সাপোর্ট', '🙋‍♂️ আমি নতুন']
], resize_keyboard=True)

# এডমিনের জন্য বিশেষ কিবোর্ড লেআউট (রিজেক্ট বাটনসহ সাজানো)
ADMIN_KEYBOARD = ReplyKeyboardMarkup([
    ['📋 পেন্ডিং লিস্ট', '📝 কাজ •', '💵 ব্যালেন্স'], 
    ['🔎 লিংক চেক', '💰 টাকা উত্তোলন', '🎁 My Referrals'], 
    ['✅ এপ্রুভ কাজ', '❌ রিজেক্ট কাজ', '🙋‍♂️ আমি নতুন'],
    ['➕ ব্যালেন্স যোগ', '🎧 সাপোর্ট', '⬅️ ফিরে যান']
], resize_keyboard=True)

async def is_user_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_STATES[user_id] = None
    if user_id in USER_DATA: del USER_DATA[user_id]
    
    str_user_id = str(user_id)
    if str_user_id not in BOT_DATA["balances"]: BOT_DATA["balances"][str_user_id] = 0.0
    if str_user_id not in BOT_DATA["pending_counts"]: BOT_DATA["pending_counts"][str_user_id] = 0
    if str_user_id not in BOT_DATA["pending_links"]: BOT_DATA["pending_links"][str_user_id] = []
    if str_user_id not in BOT_DATA["approved_counts"]: BOT_DATA["approved_counts"][str_user_id] = 0
    if str_user_id not in BOT_DATA["rejected_counts"]: BOT_DATA["rejected_counts"][str_user_id] = 0
    save_data(BOT_DATA)
    
    try:
        await context.bot.set_my_commands([BotCommand("start", "বট রিস্টার্ট করুন")])
    except: pass
    
    if await is_user_joined(context, user_id):
        current_keyboard = ADMIN_KEYBOARD if user_id == ADMIN_ID else USER_KEYBOARD
        await update.message.reply_text("🌷 স্বাগতম আমাদের Official Instagram Sell BD Bot এ 🫠🤗", reply_markup=current_keyboard)
    else:
        await update.message.reply_text(f"❌ প্রথমে আমাদের চ্যানেলে জয়েন করুন: {CHANNEL_USERNAME}\nতারপর নিচে '✅ Joined ✅' বাটনে চাপ দিন।", reply_markup=ReplyKeyboardMarkup([['✅ Joined ✅']], resize_keyboard=True))

# 📋 এডমিন কমান্ড ১: পেন্ডিং কাজের লিস্ট দেখা (/pending)
async def view_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = "📋 **পেন্ডিং কাজের তালিকা:**\n━━━━━━━━━━━━━━━\n"
    has_pending = False
    for uid, count in BOT_DATA["pending_counts"].items():
        if count > 0:
            msg += f"👤 আইডি: `{uid}` ➡️ পেন্ডিং কাজ: **{count}টি**\n"
            has_pending = True
    if not has_pending: msg += "ভল্ট খালি! কোনো পেন্ডিং কাজ নেই।"
    msg += "\n\n💡 *লিংক দেখতে লিখুন:* `/check [আইডি]`\n💡 *এপ্রুভ করতে:* `/approve [আইডি] [টাকা] [কয়টি]`\n💡 *রিজেক্ট করতে:* `/reject [আইডি] [কয়টি] [কারণ]`"
    await update.message.reply_text(msg, parse_mode="Markdown")

# 🔎 এডমিন কমান্ড ৪: লিংক চেক (/check)
async def check_user_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = context.args[0] if context.args else ""
        if not target_id:
            USER_STATES[update.effective_user.id] = 'WAITING_FOR_CHECK_ID'
            await update.message.reply_text("👇 যে ইউজারের লিংক দেখতে চান তার টেলিগ্রাম আইডি-টি পাঠান:")
            return
            
        links = BOT_DATA.get("pending_links", {}).get(str(target_id), [])
        if not links:
            await update.message.reply_text(f"❌ ইউজার `{target_id}` এর কোনো পেন্ডিং কাজের লিংক পাওয়া যায়নি।", parse_mode="Markdown")
            return
            
        msg = f"🔎 **ইউজার `{target_id}` এর জমা দেওয়া কাজসমূহ:**\n━━━━━━━━━━━━━━━\n"
        for i, link in enumerate(links, start=1): msg += f"{i}. {link}\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন: `/check ইউজার_আইডি`")

# ✅ এডমিন কমান্ড ২: কাজ এপ্রুভ করা (/approve) - কাস্টম সংখ্যাসহ
async def approve_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = context.args[0]
        amount = float(context.args[1])
        count_to_approve = int(context.args[2]) if len(context.args) > 2 else None
        
        if target_id in BOT_DATA["pending_counts"] and BOT_DATA["pending_counts"][target_id] > 0:
            total_pending = BOT_DATA["pending_counts"][target_id]
            
            if count_to_approve is None or count_to_approve >= total_pending:
                count_to_approve = total_pending
            
            if str(target_id) in BOT_DATA["pending_links"]:
                BOT_DATA["pending_links"][str(target_id)] = BOT_DATA["pending_links"][str(target_id)][count_to_approve:]
            
            BOT_DATA["pending_counts"][target_id] -= count_to_approve
            BOT_DATA["balances"][target_id] = BOT_DATA["balances"].get(target_id, 0.0) + amount
            BOT_DATA["approved_counts"][target_id] = BOT_DATA["approved_counts"].get(target_id, 0) + count_to_approve
            save_data(BOT_DATA)
            
            await update.message.reply_text(f"✅ ইউজার `{target_id}` এর {count_to_approve}টি কাজ এপ্রুভ করা হয়েছে এবং {amount}৳ মূল ব্যালেন্সে যোগ হয়েছে।\n📊 বাকি পেন্ডিং কাজ: {BOT_DATA['pending_counts'][target_id]}টি", parse_mode="Markdown")
            try:
                await context.bot.send_message(chat_id=int(target_id), text=f"🎉 আপনার জমা দেওয়া {count_to_approve}টি কাজ এডমিন চেক করে এপ্রুভ করেছেন!\n📥 মেইন ব্যালেন্সে {amount} BDT যোগ করা হয়েছে।\n🔥 বর্তমান ব্যালেন্স: {BOT_DATA['balances'][target_id]:.2f} BDT\n⏳ বাকি পেন্ডিং কাজ: {BOT_DATA['pending_counts'][target_id]}টি")
            except: pass
        else:
            await update.message.reply_text("❌ এই ইউজারের কোনো পেন্ডিং কাজ নেই!")
    except:
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন: `/approve ইউজার_আইডি টাকার_পরিমাণ কয়টি_কাজ` (যেমন: `/approve 12345678 20 1`)")

# ❌ এডমিন কমান্ড ৫: কাজ রিজেক্ট করা (/reject) - কাস্টম সংখ্যাসহ
async def reject_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = context.args[0]
        count_to_reject = int(context.args[1])
        reason = " ".join(context.args[2:]) if len(context.args) > 2 else "নিয়ম মানা হয়নি"
        
        if target_id in BOT_DATA["pending_counts"] and BOT_DATA["pending_counts"][target_id] > 0:
            total_pending = BOT_DATA["pending_counts"][target_id]
            
            if count_to_reject >= total_pending:
                count_to_reject = total_pending
            
            if str(target_id) in BOT_DATA["pending_links"]:
                BOT_DATA["pending_links"][str(target_id)] = BOT_DATA["pending_links"][str(target_id)][count_to_reject:]
            
            BOT_DATA["pending_counts"][target_id] -= count_to_reject
            BOT_DATA["rejected_counts"][target_id] = BOT_DATA["rejected_counts"].get(target_id, 0) + count_to_reject
            save_data(BOT_DATA)
            
            await update.message.reply_text(f"❌ ইউজার `{target_id}` এর {count_to_reject}টি কাজ রিজেক্ট করা হয়েছে।\n💬 কারণ: {reason}\n📊 বাকি পেন্ডিং কাজ: {BOT_DATA['pending_counts'][target_id]}টি", parse_mode="Markdown")
            try:
                await context.bot.send_message(chat_id=int(target_id), text=f"⚠️ আপনার জমা দেওয়া {count_to_reject}টি কাজ এডমিন রিজেক্ট করেছেন!\n💬 কারণ: {reason}\n⏳ বাকি পেন্ডিং কাজ: {BOT_DATA['pending_counts'][target_id]}টি")
            except: pass
        else:
            await update.message.reply_text("❌ এই ইউজারের কোনো পেন্ডিং কাজ নেই!")
    except:
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন: `/reject ইউজার_আইডি কয়টি_কাজ রিজেক্টের_কারণ` (যেমন: `/reject 12345678 1 pass_vul`)")

# ➕ এডমিন কমান্ড ৩: সরাসরি ব্যালেন্স যোগ করা (/add)
async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = context.args[0]
        amount = float(context.args[1])
        BOT_DATA["balances"][target_id] = BOT_DATA["balances"].get(target_id, 0.0) + amount
        save_data(BOT_DATA)
        await update.message.reply_text(f"✅ সফলভাবে যোগ হয়েছে: {amount}৳\n👤 ইউজার আইডি: {target_id}\n🔥 বর্তমান ব্যালেন্স: {BOT_DATA['balances'][target_id]}৳")
        try:
            await context.bot.send_message(chat_id=int(target_id), text=f"💰 আপনার অ্যাকাউন্টে এডমিন {amount} BDT যোগ করেছেন!\n🔥 বর্তমান ব্যালেন্স: {BOT_DATA['balances'][target_id]:.2f} BDT")
        except: pass
    except: 
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন: `/add ইউজার_আইডি পরিমাণ`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    str_user_id = str(user_id)
    username = update.effective_user.username or "No Username"
    first_name = update.effective_user.first_name
    text = update.message.text
    
    current_keyboard = ADMIN_KEYBOARD if user_id == ADMIN_ID else USER_KEYBOARD

    if text == '✅ Joined ✅':
        if await is_user_joined(context, user_id): await start(update, context)
        else: await update.message.reply_text("⚠️ আপনি এখনো জয়েন করেননি!")
        return

    if not await is_user_joined(context, user_id): return

    # 🛠️ এডমিন বাটন কন্ডিশনসমূহ
    if user_id == ADMIN_ID:
        if text == '📋 পেন্ডিং লিস্ট':
            await view_pending(update, context)
            return
        elif text == '🔎 লিংক চেক':
            USER_STATES[user_id] = 'WAITING_FOR_CHECK_ID'
            await update.message.reply_text("👇 যে ইউজারের লিংক দেখতে চান তার টেলিগ্রাম আইডি দিন:", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
            return
        elif text == '✅ এপ্রুভ কাজ':
            USER_STATES[user_id] = 'WAITING_FOR_APPROVE_DATA'
            await update.message.reply_text("👇 ইউজার আইডি, টাকার পরিমাণ এবং কয়টি কাজ স্পেস দিয়ে লিখুন\n(যেমন: `7831606559 20 1`):", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
            return
        elif text == '❌ রিজেক্ট কাজ':
            USER_STATES[user_id] = 'WAITING_FOR_REJECT_DATA'
            await update.message.reply_text("👇 ইউজার আইডি, কয়টি কাজ এবং রিজেক্ট করার কারণ স্পেস দিয়ে লিখুন\n(যেমন: `7831606559 1 pass_vul`):", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
            return
        elif text == '➕ ব্যালেন্স যোগ':
            USER_STATES[user_id] = 'WAITING_FOR_ADD_DATA'
            await update.message.reply_text("👇 ইউজার আইডি এবং অ্যাড করার টাকার পরিমাণ স্পেস দিয়ে লিখুন\n(যেমন: `12345678 50`):", reply_markup=ReplyKeyboardMarkup([['⬅️ ফিরে যান']], resize_keyboard=True))
            return

    # এডমিন ইনপুট হ্যান্ডেলার
    if user_id == ADMIN_ID and USER_STATES.get(user_id) in ['WAITING_FOR_CHECK_ID', 'WAITING_FOR_APPROVE_DATA', 'WAITING_FOR_REJECT_DATA', 'WAITING_FOR_ADD_DATA']:
        if '⬅️ ফিরে যান' in text:
            USER_STATES[user_id] = None
            await start(update, context)
            return
        
        current_state = USER_STATES[user_id]
        USER_STATES[user_id] = None
        
        if current_state == 'WAITING_FOR_CHECK_ID':
            context.args = text.strip().split()
            await check_user_links(update, context)
        elif current_state == 'WAITING_FOR_APPROVE_DATA':
            context.args = text.strip().split()
            await approve_work(update, context)
        elif current_state == 'WAITING_FOR_REJECT_DATA':
            context.args = text.strip().split()
            await reject_work(update, context)
        elif current_state == 'WAITING_FOR_ADD_DATA':
            context.args = text.strip().split()
            await add_balance(update, context)
        return

    # [কাজ জমা নেওয়ার লজিক]
    if USER_STATES.get(user_id) == 'WAITING_FOR_ID':
        if '⬅️ ফিরে যান' in text:
            USER_STATES[user_id] = None
            await start(update, context)
            return
            
        if "pending_links" not in BOT_DATA: BOT_DATA["pending_links"] = {}
        if str_user_id not in BOT_DATA["pending_links"]: BOT_DATA["pending_links"][str_user_id] = []
        
        BOT_DATA["pending_links"][str_user_id].append(text)
        BOT_DATA["pending_counts"][str_user_id] = BOT_DATA["pending_counts"].get(str_user_id, 0) + 1
        save_data(BOT_DATA)
        
        msg = f"📥 **নতুন কাজ জমা পড়েছে!**\n\n👤 নাম: {first_name}\n🆔 আইডি: `{user_id}`\n🔗 @{username}\n\n📝 **লিংক/আইডি:**\n{text}\n\n📊 এই ইউজারের মোট পেন্ডিং কাজ: {BOT_DATA['pending_counts'][str_user_id]}টি"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
        await update.message.reply_text(f"✅ আপনার ইনস্টাগ্রাম আইডি/লিংকটি সফলভাবে জমা হয়েছে!\n📥 আপনার মোট {BOT_DATA['pending_counts'][str_user_id]}টি কাজ পেন্ডিং আছে। এডমিন চেক করে মেইন ব্যালেন্সে টাকা দিয়ে দেবেন।", reply_markup=current_keyboard)
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
                await update.message.reply_text(f"❌ রিকোয়েস্ট ক্যানসেল! {method_name}-এ সর্বনিম্ন {min_amt:.0f}৳ উত্তোলন করতে হবে।", reply_markup=current_keyboard)
                USER_STATES[user_id] = None
                if user_id in USER_DATA: del USER_DATA[user_id]
                return
                
            user_bal = BOT_DATA["balances"].get(str_user_id, 0.0)
            if user_bal < amt:
                await update.message.reply_text(f"❌ রিকোয়েস্ট ক্যানসেল! আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই।\n🔥 বর্তমান ব্যালেন্স: {user_bal:.2f} BDT", reply_markup=current_keyboard)
            else:
                BOT_DATA["balances"][str_user_id] -= amt
                save_data(BOT_DATA)
                num = USER_DATA.get(user_id, {}).get('number', 'N/A')
                
                admin_msg = f"💰 **উইথড্র রিকোয়েস্ট!**\n\n👤 নাম: {first_name}\n🆔 আইডি: `{user_id}`\n💳 মাধ্যম: {method_name}\n📱 নাম্বার: `{num}`\n💵 পরিমাণ: **{amt:.2f} BDT**"
                await context.bot.send_message(ADMIN_ID, text=admin_msg, parse_mode="Markdown")
                await update.message.reply_text(f"✅ আপনার উইথড্র রিকোয়েস্টটি সফল হয়েছে!\n📉 কেটে নেওয়া হয়েছে: {amt:.2f} BDT\n🔥 বর্তমান মূল ব্যালেন্স: {BOT_DATA['balances'][str_user_id]:.2f} BDT", reply_markup=current_keyboard)
        except ValueError:
            await update.message.reply_text("❌ ভুল অ্যামাউন্ট! শুধুমাত্র সংখ্যায় টাকার পরিমাণ লিখুন।", reply_markup=current_keyboard)
            
        USER_STATES[user_id] = None
        if user_id in USER_DATA: del USER_DATA[user_id]
        return

    # 🛠️ মেইন মেনু কন্ডিশন
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
        bal = BOT_DATA["balances"].get(str_user_id, 0.0)
        pending_work = BOT_DATA["pending_counts"].get(str_user_id, 0)
        approved_work = BOT_DATA["approved_counts"].get(str_user_id, 0)
        rejected_work = BOT_DATA["rejected_counts"].get(str_user_id, 0)
        
        msg = (
            f"💰 **আপনার ব্যালেন্স ও কাজের রিপোর্ট**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔥 মূল ব্যালেন্স: {bal:.2f} BDT\n\n"
            f"📥 পেন্ডিং কাজ: {pending_work}টি\n"
            f"✅ এপ্রুভড কাজ: {approved_work}টি\n"
            f"❌ রিজেক্টেড কাজ: {rejected_work}টি"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=current_keyboard)
    elif '🙋‍♂️ আমি নতুন' in text:
        await update.message.reply_text(f"আমাদের অফিশিয়াল চ্যানেলে জয়েন হয়ে কাজ শুরু করে দিন।\nLink: {CHANNEL_USERNAME}", reply_markup=current_keyboard)
    elif '🎧 সাপোর্ট' in text:
        await update.message.reply_text("🎧 যেকোনো সমস্যায় সাপোর্ট আইডিতে মেসেজ দিন:\n👉 @nafin_4x_team", reply_markup=current_keyboard)
    elif '🎁 My Referrals' in text:
        await update.message.reply_text("🎁 আপনার রেফারেল সিস্টেমটি খুব শীঘ্রই চালু করা হবে!", reply_markup=current_keyboard)
    elif '⬅️ ফিরে যান' in text: 
        await start(update, context)
    else: 
