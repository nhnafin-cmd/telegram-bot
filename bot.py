import os
import json
import pyotp
import random
import string
import datetime
import telebot
from telebot import types
import gspread
from google.oauth2.service_account import Credentials

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

CHANNEL_USERNAME = "@OfficialInstagramSellBD"
ADMIN_ID = 7831606559  # আপনার টেলিগ্রাম আইডি
WITHDRAW_GROUP_ID = "@igsellonly"  # উইথड्र রিকোয়েস্ট গ্রুপ ইউজারনেম
REFER_BONUS = 2.0      # প্রতি রেফারে কত টাকা বোনাস দিতে চান তা এখানে সেট করুন

BALANCE_FILE = "balances.json"
SPREADSHEET_ID = "1LFnQKiDdoiE0GUtApWbSAsbDUELo1LszhLX64CtpRBM"  # আপনার গুগল শিট আইডি

# 📊 গুগল শিট কানেক্ট করার ফাংশন
def append_to_google_sheet(username, two_fa_key, telegram_id, telegram_name):
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        # বর্তমান সময় বের করা
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # গুগল শিটে নতুন রো (Row) হিসেবে ডেটা যোগ করা
        sheet.append_row([now_time, username, two_fa_key, telegram_id, telegram_name])
        print("Data successfully added to Google Sheet!")
    except Exception as e:
        print(f"Error updating Google Sheet: {e}")

# ডাটা লোড এবং সেভ করার সিস্টেম
def load_data():
    default_data = {
        "balances": {}, 
        "pending_counts": {}, 
        "pending_links": {}, 
        "approved_counts": {}, 
        "rejected_counts": {},
        "referred_by": {},    
        "refer_counts": {}    
    }
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for key in default_data:
                    if key not in data:
                        data[key] = {}
                return data
            except Exception:
                return default_data
    return default_data

def save_data(data):
    with open(BALANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

BOT_DATA = load_data()
USER_STATES = {}
USER_DATA = {}

# 📆 ডাইনামিক ইউজারনেম এবং পাসওয়ার্ড জেনারেটর
def generate_credentials():
    first_names = ["anil", "kamrol", "sabbir", "rafsan", "nafin", "shohan", "tamim", "arif", "joy"]
    last_names = ["azevedo", "khan", "ahmed", "hossain", "chy", "bd", "islam", "rahman"]
    username = f"{random.choice(first_names)}{random.choice(last_names)}{''.join(random.choices(string.digits, k=5))}"
    
    today_date = datetime.datetime.now().strftime("%d")
    password = f"nagi@{today_date}"
    return username, password

# 📱 সাধারণ ইউজারদের জন্য কিবোর্ডের নিচের স্থায়ী মেনু
def send_user_main_menu(chat_id, text_msg="🧭 **মেইন মেনু:**"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('📝 কাজ •'),
        types.KeyboardButton('💵 ব্যালেন্স')
    )
    markup.add(
        types.KeyboardButton('💰 টাকা উত্তোলন'),
        types.KeyboardButton('🎁 My Referrals')
    )
    markup.add(
        types.KeyboardButton('🎧 সাপোর্ট'),
        types.KeyboardButton('🙋‍♂️ আমি নতুন')
    )
    
    if chat_id == ADMIN_ID:
        markup.add(types.KeyboardButton('👑 এডমিন প্যানেল'))
        
    bot.send_message(chat_id, text_msg, reply_markup=markup, parse_mode="Markdown")

# 👑 এডমিনদের জন্য বিশেষ ইনলাইন মেনু
def get_admin_inline_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('📋 পেন্ডিং লিস্ট', callback_data='admin_pending'),
        types.InlineKeyboardButton('🔎 লিংক চেক', callback_data='admin_check')
    )
    markup.add(
        types.InlineKeyboardButton('✅ এপ্রুভ কাজ', callback_data='admin_approve'),
        types.InlineKeyboardButton('❌ রিজেক্ট কাজ', callback_data='admin_reject')
    )
    markup.add(
        types.InlineKeyboardButton('➕ ব্যালেন্স যোগ', callback_data='admin_add_bal'),
        types.InlineKeyboardButton('⚙️ ইউজার মেনু', callback_data='go_to_main_menu')
    )
    return markup

def check_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# /start কমান্ড
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    USER_STATES[user_id] = None
    if user_id in USER_DATA: del USER_DATA[user_id]
    
    str_user_id = str(user_id)
    
    if str_user_id not in BOT_DATA["balances"]: BOT_DATA["balances"][str_user_id] = 0.0
    if str_user_id not in BOT_DATA["pending_counts"]: BOT_DATA["pending_counts"][str_user_id] = 0
    if str_user_id not in BOT_DATA["pending_links"]: BOT_DATA["pending_links"][str_user_id] = []
    if str_user_id not in BOT_DATA["approved_counts"]: BOT_DATA["approved_counts"][str_user_id] = 0
    if str_user_id not in BOT_DATA["rejected_counts"]: BOT_DATA["rejected_counts"][str_user_id] = 0
    if str_user_id not in BOT_DATA["refer_counts"]: BOT_DATA["refer_counts"][str_user_id] = 0
    
    args = message.text.split()
    if len(args) > 1:
        referrer_id = args[1]
        if str_user_id not in BOT_DATA["referred_by"] and referrer_id != str_user_id and referrer_id in BOT_DATA["balances"]:
            BOT_DATA["referred_by"][str_user_id] = referrer_id
            
    save_data(BOT_DATA)
    
    if check_joined(user_id):
        bot.send_message(message.chat.id, "🌷 স্বাগতম আমাদের Official Instagram Sell BD Bot এ 🫠🤗")
        if user_id == ADMIN_ID:
            bot.send_message(message.chat.id, "👑 **এডমিন কন্ট্রোল প্যানেল:**", reply_markup=get_admin_inline_keyboard(), parse_mode="Markdown")
        else:
            send_user_main_menu(message.chat.id)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('✅ Joined ✅', callback_data='check_joined_btn'))
        bot.send_message(message.chat.id, f"❌ প্রথমে আমাদের চ্যানেলে জয়েন করুন: {CHANNEL_USERNAME}\n\nতারপর নিচে '✅ Joined ✅' বাটনে চাপ দিন।", reply_markup=markup)

# এডমিন কমান্ড ১: পেন্ডিং কাজের লিস্ট দেখা
@bot.message_handler(commands=['pending'])
def view_pending(message):
    if message.from_user.id != ADMIN_ID: return
    msg = "📋 **পেন্ডিং কাজের তালিকা:**\n━━━━━━━━━━━━━━━\n"
    has_pending = False
    for uid, count in BOT_DATA["pending_counts"].items():
        if count > 0:
            msg += f"👤 আইডি: `{uid}` ➡️ পেন্ডিং কাজ: **{count}টি**\n"
            has_pending = True
    if not has_pending: msg += "ভল্ট খালি! কোনো পেন্ডিং কাজ নেই।"
    msg += "\n\n💡 *লিংক দেখতে লিখুন:* `/check [আইডি]`\n💡 *এপ্রুভ করতে:* `/approve [আইডি] [টাকা] [কয়টি]`\n💡 *রিজেক্ট করতে:* `/reject [আইডি] [কয়টি] [কারণ]`"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# 🔎 এডমিন কমান্ড ৪: লিংক চেক
@bot.message_handler(commands=['check'])
def check_user_links_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()[1:]
    if not args:
        USER_STATES[message.from_user.id] = 'WAITING_FOR_CHECK_ID'
        bot.send_message(message.chat.id, "👇 যে ইউজারের লিংক দেখতে চান তার টেলিগ্রাম আইডি-টি পাঠান:")
        return
    
    target_id = args[0]
    links = BOT_DATA.get("pending_links", {}).get(str(target_id), [])
    if not links:
        bot.send_message(message.chat.id, f"❌ ইউজার `{target_id}` এর কোনো পেন্ডিং কাজের লিংক পাওয়া যায়নি।", parse_mode="Markdown")
        return
        
    msg = f"🔎 **ইউজার `{target_id}` এর জমা দেওয়া কাজসমূহ:**\n━━━━━━━━━━━━━━━\n"
    for i, link in enumerate(links, start=1):
        try:
            if "|" in link and "Uname:" in link and "2FA:" in link:
                parts = link.split("|")
                uname_part = parts[0].replace("Uname:", "").strip()
                fa_part = parts[1].replace("2FA:", "").strip()
                msg += f"<b>{i}. Unames:</b> <code>{uname_part}</code>\n<b>   2FA:</b> <code>{fa_part}</code>\n\n"
            else:
                msg += f"{i}. <code>{link}</code>\n\n"
        except Exception:
            msg += f"{i}. <code>{link}</code>\n\n"
            
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

# ✅ এডমিন কমান্ড ২: কাজ এপ্রুভ করা
@bot.message_handler(commands=['approve'])
def approve_work(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()[1:]
        target_id = args[0]
        amount = float(args[1])
        count_to_approve = int(args[2]) if len(args) > 2 else None
        
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
            
            bot.send_message(message.chat.id, f"✅ ইউজার `{target_id}` এর {count_to_approve}টি কাজ এপ্রুভ করা হয়েছে এবং {amount}৳ মূল ব্যালেন্সে যোগ হয়েছে।\n📊 বাকি পেন্ডিং কাজ: {BOT_DATA['pending_counts'][target_id]}টি", parse_mode="Markdown")
            try:
                bot.send_message(int(target_id), f"🎉 আপনার জমা দেওয়া {count_to_approve}টি কাজ এডমিন চেক করে এপ্রুভ করেছেন!\n📥 মেইন ব্যালেন্সে {amount} BDT যোগ করা হয়েছে।\n🔥 বর্তমান ব্যালেন্স: {BOT_DATA['balances'][target_id]:.2f} BDT\n⏳ বাকি পেন্ডিং কাজ: {BOT_DATA['pending_counts'][target_id]}টি")
            except Exception: pass
        else:
            bot.send_message(message.chat.id, "❌ এই ইউজারের কোনো পেন্ডিং কাজ নেই!")
    except Exception:
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট! লিখুন: `/approve ইউজার_আইডি টাকার_পরিমাণ কয়টি_কাজ`")

# ❌ এডমিন কমান্ড ৫: কাজ রিজেক্ট করা
@bot.message_handler(commands=['reject'])
def reject_work(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()[1:]
        target_id = args[0]
        count_to_reject = int(args[1])
        reason = " ".join(args[2:]) if len(args) > 2 else "নিয়ম মানা হয়নি"
        
        if target_id in BOT_DATA["pending_counts"] and BOT_DATA["pending_counts"][target_id] > 0:
            total_pending = BOT_DATA["pending_counts"][target_id]
            if count_to_reject >= total_pending: count_to_reject = total_pending
            
            if str(target_id) in BOT_DATA["pending_links"]:
                BOT_DATA["pending_links"][str(target_id)] = BOT_DATA["pending_links"][str(target_id)][count_to_reject:]
            
            BOT_DATA["pending_counts"][target_id] -= count_to_reject
            BOT_DATA["rejected_counts"][target_id] = BOT_DATA["rejected_counts"].get(target_id, 0) + count_to_reject
            save_data(BOT_DATA)
            
            bot.send_message(message.chat.id, f"❌ ইউজার `{target_id}` এর {count_to_reject}টি কাজ রিজেক্ট করা হয়েছে।\n💬 কারণ: {reason}\n📊 বাকি পেন্ডিং কাজ: {BOT_DATA['pending_counts'][target_id]}টি", parse_mode="Markdown")
            try:
                bot.send_message(int(target_id), f"⚠️ আপনার জমা দেওয়া {count_to_reject}টি কাজ এডমিন রিজেক্ট করেছেন!\n💬 কারণ: {reason}\n⏳ বাকি পেন্ডিং কাজ: {BOT_DATA['pending_counts'][target_id]}টি")
            except Exception: pass
        else:
            bot.send_message(message.chat.id, "❌ এই ইউজারের কোনো পেন্ডিং কাজ নেই!")
    except Exception:
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট! লিখুন: `/reject ইউজার_আইডি কয়টি_কাজ কারণ`")

# ➕ এডমিন কমান্ড ৩: সরাসরি ব্যালেন্স যোগ করা
@bot.message_handler(commands=['add'])
def add_balance(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()[1:]
        target_id = args[0]
        amount = float(args[1])
        BOT_DATA["balances"][target_id] = BOT_DATA["balances"].get(target_id, 0.0) + amount
        save_data(BOT_DATA)
        bot.send_message(message.chat.id, f"✅ সফলভাবে যোগ হয়েছে: {amount}৳\n👤 ইউজার আইডি: {target_id}\n🔥 বর্তমান ব্যালেন্স: {BOT_DATA['balances'][target_id]}৳")
        try:
            bot.send_message(int(target_id), f"💰 আপনার অ্যাকাউন্টে এডমিন {amount} BDT যোগ করেছেন!\n🔥 বর্তমান ব্যালেন্স: {BOT_DATA['balances'][target_id]:.2f} BDT")
        except Exception: pass
    except Exception:
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট! লিখুন: `/add ইউজার_আইডি পরিমাণ`")

# সাধারণ মেসেজ ও বটম কিবোর্ড টেক্সট হ্যান্ডেলার
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    str_user_id = str(user_id)
    text = message.text

    if not check_joined(user_id): return

    if user_id == ADMIN_ID and USER_STATES.get(user_id) in ['WAITING_FOR_CHECK_ID', 'WAITING_FOR_APPROVE_DATA', 'WAITING_FOR_REJECT_DATA', 'WAITING_FOR_ADD_DATA']:
        current_state = USER_STATES[user_id]
        USER_STATES[user_id] = None
        
        if current_state == 'WAITING_FOR_CHECK_ID':
            message.text = f"/check {text}"
            check_user_links_cmd(message)
            return
        elif current_state == 'WAITING_FOR_APPROVE_DATA':
            message.text = f"/approve {text}"
            approve_work(message)
        elif current_state == 'WAITING_FOR_REJECT_DATA':
            message.text = f"/reject {text}"
            reject_work(message)
        elif current_state == 'WAITING_FOR_ADD_DATA':
            message.text = f"/add {text}"
            add_balance(message)
            
        bot.send_message(message.chat.id, "👑 **এডমিন কন্ট্রোল প্যানেল:**", reply_markup=get_admin_inline_keyboard(), parse_mode="Markdown")
        return

    # --- কিবোর্ড বাটন ক্লিক হ্যান্ডেলিং ---
    if text == '📝 কাজ •':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('ইনস্টাগ্রাম কাজ >', callback_data='work_insta_step'))
        bot.send_message(message.chat.id, "সিলেক্ট করুন:", reply_markup=markup)
        return

    elif text == '💵 ব্যালেন্স':
        bal = BOT_DATA["balances"].get(str_user_id, 0.0)
        msg = f"💰 **আপনার ব্যালেন্স ও কাজের রিপোর্ট**\n━━━━━━━━━━━━━━━\n🔥 মূল ব্যালেন্স: {bal:.2f} BDT\n📥 পেন্ডিং কাজ: {BOT_DATA['pending_counts'].get(str_user_id, 0)}টি\n✅ এপ্রুভড কাজ: {BOT_DATA['approved_counts'].get(str_user_id, 0)}টি\n❌ রিজেক্টেড কাজ: {BOT_DATA['rejected_counts'].get(str_user_id, 0)}টি"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        return

    elif text == '💰 টাকা উত্তোলন':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('bKash', callback_data='withdraw_bkash'), types.InlineKeyboardButton('Nagad', callback_data='withdraw_nagad'))
        bot.send_message(message.chat.id, "📩 মাধ্যম সিলেক্ট করুন:", reply_markup=markup)
        return

    elif text == '🎁 My Referrals':
        bot_info = bot.get_me()
        refer_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"🎁 **আপনার রেফারেল ড্যাশবোর্ড**\n━━━━━━━━━━━━━━━━━━━━━\n👥 মোট সফল রেফার: **{BOT_DATA['refer_counts'].get(str_user_id, 0)} জন**\n💰 বোনাস: **{REFER_BONUS:.2f} BDT**\n\n🔗 **লিংক:**\n`{refer_link}`"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        return

    elif text == '🙋‍♂️ আমি নতুন':
        msg = f"আমাদের অফিশিয়াল চ্যানেলে জয়েন হয়ে কাজ শুরু করে দিন।\nLink: {CHANNEL_USERNAME}"
        bot.send_message(message.chat.id, msg)
        return

    elif text == '🎧 সাপোর্ট':
        msg = "🎧 যেকোনো সমস্যায় সাপোর্ট আইডিতে মেসেজ দিন:\n👉 @nafin_4x_team"
        bot.send_message(message.chat.id, msg)
        return

    elif text == '👑 এডমিন প্যানেল' and user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 **এডমিন কন্ট্রোল প্যানেল:**", reply_markup=get_admin_inline_keyboard(), parse_mode="Markdown")
        return

    # 📋 ২এফএ কি সাবমিট করার প্রসেস ওায়নামিক টাচ-টু-কпи সিস্টেম
    if USER_STATES.get(user_id) == 'WAITING_FOR_2FA_KEY':
        user_input = text.strip().replace(" ", "").upper()
        try:
            missing_padding = len(user_input) % 8
            if missing_padding: user_input += '=' * (8 - missing_padding)
            totp = pyotp.TOTP(user_input)
            code = totp.now()
            
            if user_id not in USER_DATA: USER_DATA[user_id] = {}
            USER_DATA[user_id]['2fa_key'] = user_input
            
            bot.send_message(message.chat.id, "অ্যাকাউন্ট খোলা শেষ হলে নিচের বাটনে চাপ দিন:")
            bot.send_message(message.chat.id, "নিচের কোডটির ওপর টাচ করে কপি করুন 📊")
            
            bot.send_message(message.chat.id, f"👇 কোডটি কপি করতে নিচের সংখ্যার ওপর ক্লিক করুন:\n\n<code>{code}</code>", parse_mode="HTML")
            
            finish_markup = types.InlineKeyboardMarkup()
            finish_markup.add(types.InlineKeyboardButton('✅ অ্যাকাউন্ট খোলা শেষ', callback_data='work_finish_done'))
            bot.send_message(message.chat.id, "👇 কাজ সম্পূর্ণ সাবমিট করতে নিচের বাটনে ক্লিক করুন:", reply_markup=finish_markup)
            USER_STATES[user_id] = 'WAITING_FOR_FINISH'
        except Exception:
            bot.send_message(message.chat.id, "❌ **ভুল 2FA Key!** দয়া করে সঠিক কী দিন।")
            send_user_main_menu(message.chat.id)
            USER_STATES[user_id] = None
        return
        
    if USER_STATES.get(user_id) in ['WAITING_FOR_BKASH_NUMBER', 'WAITING_FOR_NAGAD_NUMBER']:
        if user_id not in USER_DATA: USER_DATA[user_id] = {}
        USER_DATA[user_id]['number'] = text
        method_type = "BKASH" if USER_STATES[user_id] == 'WAITING_FOR_BKASH_NUMBER' else "NAGAD"
        USER_DATA[user_id]['method'] = method_type
        
        USER_STATES[user_id] = 'WAITING_FOR_AMOUNT'
        min_limit = "💡১১০৳" if method_type == "BKASH" else "১০০৳"
        bot.send_message(message.chat.id, f"👇 কত টাকা উত্তোলন করতে চান? (সর্বনিম্ন {min_limit}):")
        return

    if USER_STATES.get(user_id) == 'WAITING_FOR_AMOUNT':
        try:
            amt = float(text)
            saved_method = USER_DATA.get(user_id, {}).get('method', 'BKASH')
            method_name = "বিকাশ" if saved_method == "BKASH" else "নগদ"
            min_amt = 110.0 if saved_method == "BKASH" else 100.0
            
            if amt < min_amt:
                bot.send_message(message.chat.id, f"❌ রিকোয়েস্ট ক্যানসেল! {method_name}-এ সর্বনিম্ন {min_amt:.0f}৳ উত্তোলন করতে হবে।")
            else:
                user_bal = BOT_DATA["balances"].get(str_user_id, 0.0)
                if user_bal < amt:
                    bot.send_message(message.chat.id, f"❌ রিকোয়েস্ট ক্যানসেল! আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই।\n🔥 বর্তমান ব্যালেন্স: {user_bal:.2f} BDT")
                else:
                    BOT_DATA["balances"][str_user_id] -= amt
                    save_data(BOT_DATA)
                    num = USER_DATA.get(user_id, {}).get('number', 'N/A')
                    
                    withdraw_group_msg = (
                        f"📥 **নতুন উইথড্র রিকোয়েস্ট**\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 নাম: {message.from_user.first_name}\n"
                        f"🆔 ইউজার আইডি: `{user_id}`\n"
                        f"💳 মাধ্যম: **{method_name}**\n"
                        f"📱 নাম্বার: `{num}`\n"
                        f"💰 পরিমাণ: **{amt:.2f} BDT**\n"
                        f"━━━━━━━━━━━━━━━━━━━"
                    )
                    
                    try:
                        bot.send_message(WITHDRAW_GROUP_ID, withdraw_group_msg, parse_mode="Markdown")
                    except Exception as e:
                        print(f"Error sending to channel/group: {e}")
                        
                    admin_msg = f"💰 **উইথড্র রিকোয়েস্ট!**\n\n👤 নাম: {message.from_user.first_name}\n🆔 আইডি: `{user_id}`\n💳 মাধ্যম: {method_name}\n📱 নাম্বার: `{num}`\n💵 পরিমাণ: **{amt:.2f} BDT**"
                    bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
                    
                    bot.send_message(message.chat.id, f"✅ আপনার উইথড্র রিকোয়েস্টটি সফল হয়েছে!\n📉 কেটে নেওয়া হয়েছে: {amt:.2f} BDT\n🔥 বর্তমান মূল ব্যালেন্স: {BOT_DATA['balances'][str_user_id]:.2f} BDT")
        except ValueError:
            bot.send_message(message.chat.id, "❌ ভুল অ্যামাউন্ট! শুধুমাত্র সংখ্যায় টাকার পরিমাণ লিখুন।")
        
        send_user_main_menu(message.chat.id)
        USER_STATES[user_id] = None
        if user_id in USER_DATA: del USER_DATA[user_id]
        return

# 🎛️ ইনলাইন বাটন ক্লিক হ্যান্ডেলার
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    str_user_id = str(user_id)
    
    if call.data == 'check_joined_btn':
        if check_joined(user_id):
            if str_user_id in BOT_DATA["referred_by"]:
                referrer = BOT_DATA["referred_by"][str_user_id]
                if referrer in BOT_DATA["balances"]:
                    BOT_DATA["balances"][referrer] += REFER_BONUS
                    BOT_DATA["refer_counts"][referrer] = BOT_DATA["refer_counts"].get(referrer, 0) + 1
                    try:
                        bot.send_message(int(referrer), f"🎁 **সফল রেফারেল বোনাস!**\n\n👤 আপনার লিংক ব্যবহার করে একজন নতুন ইউজার জয়েন করেছে।\n💰 আপনার অ্যাকাউন্টে **{REFER_BONUS:.2f} BDT** যোগ করা হয়েছে।")
                    except Exception: pass
                del BOT_DATA["referred_by"][str_user_id]
                save_data(BOT_DATA)
            
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "🌷 স্বাগতম আমাদের Official Instagram Sell BD Bot এ 🫠🤗")
            send_user_main_menu(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "⚠️ আপনি অন্তত জয়েন করেননি!", show_alert=True)
        return

    if not check_joined(user_id): return

    if call.data == 'work_insta_step':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('ইনস্টাগ্রাম 2fa (৳৩.০০)', callback_data='work_insta_start_generate'))
        bot.edit_message_text("🟣 সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif call.data == 'work_insta_start_generate':
        uname, upass = generate_credentials()
        if user_id not in USER_DATA: USER_DATA[user_id] = {}
        USER_DATA[user_id]['generated_username'] = uname
        
        msg = (
            f"👤 Username: <code>{uname}</code> (কপি করতে টাচ করুন)\n"
            f"🔐 Password: <code>{upass}</code> (কপি করতে টাচ করুন)\n\n"
            f"📸 উপরের ইউজারনেম এবং পাসওয়ার্ড দিয়ে অ্যাকাউন্ট খুলুন। তারপর নিচে 2FA Set বাটনে ক্লিক করুন 🤪"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔒 2FA Set", callback_data="open_2fa_input"))
        bot.send_message(call.message.chat.id, msg, parse_mode="HTML", reply_markup=markup)
        bot.answer_callback_query(call.id)
        
    elif call.data == "open_2fa_input":
        USER_STATES[user_id] = 'WAITING_FOR_2FA_KEY'
        bot.send_message(call.message.chat.id, "🔑 **2FA Key টি দিন:** ⤵️")
        bot.answer_callback_query(call.id)
        
    elif call.data == 'work_finish_done':
        generated_uname = USER_DATA.get(user_id, {}).get('generated_username', 'Unknown_User')
        saved_2fa = USER_DATA.get(user_id, {}).get('2fa_key', 'No_Key_Provided')
        
        if "pending_links" not in BOT_DATA: BOT_DATA["pending_links"] = {}
        if str_user_id not in BOT_DATA["pending_links"]: BOT_DATA["pending_links"][str_user_id] = []
        
        work_details = f"Uname: {generated_uname} | 2FA: {saved_2fa}"
        BOT_DATA["pending_links"][str_user_id].append(work_details)
        BOT_DATA["pending_counts"][str_user_id] = BOT_DATA["pending_counts"].get(str_user_id, 0) + 1
        save_data(BOT_DATA)
        
        # 🚀 ইউজার কাজ সফলভাবে শেষ করার সাথে সাথে গুগল শিটেও ডেটা চলে যাবে
        append_to_google_sheet(generated_uname, saved_2fa, str_user_id, call.from_user.first_name)
        
        admin_msg = f"📥 **নতুন কাজ জমা পড়েছে!**\n\n👤 নাম: {call.from_user.first_name}\n🆔 আইডি: `{user_id}`\n📝 **কাজ:** `{work_details}`"
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        
        bot.send_message(call.message.chat.id, "👍 আপনার কাজ সফলভাবে গ্রহণ করা হয়েছে এবং গুগল শিটে সংরক্ষণ করা হয়েছে।\n\n📢 পেমেন্ট ঠিক কখন পাবেন, সেই আপডেট এই গ্রুপেই জানিয়ে দেওয়া হবে।\nhttps://t.me/OfficialInstagramSellBD")
        send_user_main_menu(call.message.chat.id)
        
        if user_id in USER_DATA: del USER_DATA[user_id]
        USER_STATES[user_id] = None
        bot.answer_callback_query(call.id)

    elif call.data in ['withdraw_bkash', 'withdraw_nagad']:
        method = "বিকাশ" if call.data == 'withdraw_bkash' else "নগদ"
        USER_STATES[user_id] = 'WAITING_FOR_BKASH_NUMBER' if call.data == 'withdraw_bkash' else 'WAITING_FOR_NAGAD_NUMBER'
        bot.send_message(call.message.chat.id, f"👇 আপনার {method} নাম্বারটি লিখুন:")
        bot.answer_callback_query(call.id)

    elif call.data == 'go_to_main_menu':
        USER_STATES[user_id] = None
        send_user_main_menu(call.message.chat.id, "🧭 **মেইন মেনু চালু করা হয়েছে নিচে:**")
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_pending':
        bot.answer_callback_query(call.id)
        class DummyMessage:
            def __init__(self, uid, cid):
                self.from_user = type('User', (object,), {'id': uid})()
                self.chat = type('Chat', (object,), {'id': cid})()
        dummy = DummyMessage(user_id, call.message.chat.id)
        view_pending(dummy)
        
    elif call.data == 'admin_check':
        USER_STATES[user_id] = 'WAITING_FOR_CHECK_ID'
        bot.send_message(call.message.chat.id, "👇 যে ইউজারের লিংক দেখতে চান তার টেলিগ্রাম আইডি দিন:")
        bot.answer_callback_query(call.id)
        
    elif call.data == 'admin_approve':
        USER_STATES[user_id] = 'WAITING_FOR_APPROVE_DATA'
        bot.send_message(call.message.chat.id, "👇 ইউজার আইডি, টাকার পরিমাণ এবং কয়টি কাজ স্পেস দিয়ে লিখুন (যেমন: `12345678 20 2`):")
        bot.answer_callback_query(call.id)
        
    elif call.data == 'admin_reject':
        USER_STATES[user_id] = 'WAITING_FOR_REJECT_DATA'
        bot.send_message(call.message.chat.id, "👇 ইউজার আইডি, কয়টি কাজ এবং রিজেক্ট করার কারণ স্পেস দিয়ে লিখুন (যেমন: `12345678 1 pass_vul`):")
        bot.answer_callback_query(call.id)
        
    elif call.data == 'admin_add_bal':
        USER_STATES[user_id] = 'WAITING_FOR_ADD_DATA'
        bot.send_message(call.message.chat.id, "👇 ইউজার আইডি এবং অ্যাড করার টাকার পরিমাণ স্পেস দিয়ে লিখুন (যেমন: `12345678 50`):")
        bot.answer_callback_query(call.id)

if __name__ == '__main__':
    try:
        bot.set_my_commands([
            telebot.types.BotCommand("start", "🤖 বট চালু করুন / মেইন মেনু"),
            telebot.types.BotCommand("pending", "📋 পেন্ডিং কাজ দেখুন (এডমিন)"),
            telebot.types.BotCommand("check", "🔎 ইউজারের লিংক চেক করুন (এডমিন)")
        ])
    except Exception as e:
        print(f"Error setting commands: {e}")

    bot.infinity_polling(skip_pending=True)
