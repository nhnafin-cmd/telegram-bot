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
WITHDRAW_GROUP_ID = "@igsellonly"  # উইথড্র রিকোয়েস্ট গ্রুপ ইউজারনেম
REFER_BONUS = 2.0      # প্রতি রেফারে ২ টাকা ইনস্ট্যান্ট বোনাস
REFER_COMMISSION_PERCENT = 0.10  # ১০% লাইফটাইম কাজের কমিশন

BALANCE_FILE = "balances.json"
# 📊 দুই কাজের জন্য দুটি আলাদা গুগল শিট আইডি (আপনার দেওয়া ফেসবুক আইডি সেট করা হয়েছে)
INSTA_SPREADSHEET_ID = "1LFnQKiDdoiE0GUtApWbSAsbDUELo1LszhLX64CtpRBM"  # ইনস্টাগ্রাম শিট
FB_SPREADSHEET_ID = "1Bl6y5eHkFVjpqy6NIPCGdZBo0u6Ekod51B6gXJ0sAZk"      # আপনার ফেসবুক শিট আইডি

# 💎 কাস্টম অ্যানিমেটেড ইমোজি ও ডিভাইডার আইডি সেটআপ
DIVIDER = "<tg-emoji emoji-id='5870818207383686839'>━</tg-emoji>"
DIVIDER_LINE = DIVIDER * 7

EMOJI_CRYSTAL = "<tg-emoji emoji-id='5353027129250453493'>🔮</tg-emoji>🔮"
EMOJI_FIRE    = "<tg-emoji emoji-id='5334763399299506604'>🔥</tg-emoji>🔥"
EMOJI_USERS   = "<tg-emoji emoji-id='5420145051336485498'>👥</tg-emoji>👥"
EMOJI_CALENDAR= "<tg-emoji emoji-id='5352585194295564660'>📅</tg-emoji>📅"
EMOJI_LOCK    = "<tg-emoji emoji-id='5337255927735163754'>🔒</tg-emoji>🔒"

# 🔄 মেসেজ ট্র্যাক এবং অটো-ডিলিট করার ফাংশনসমূহ
def track_msg(user_id, message_obj):
    if not message_obj: return
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {}
    if 'msg_ids' not in USER_DATA[user_id]:
        USER_DATA[user_id]['msg_ids'] = []
    USER_DATA[user_id]['msg_ids'].append(message_obj.message_id)

def clear_user_session_messages(chat_id, user_id):
    if user_id in USER_DATA and 'msg_ids' in USER_DATA[user_id]:
        for msg_id in USER_DATA[user_id]['msg_ids']:
            try: bot.delete_message(chat_id, msg_id)
            except Exception: pass
        USER_DATA[user_id]['msg_ids'] = []

# 📆 সন্ধ্যা ৬টার লজিক অনুযায়ী ডাইনামিক পাসওয়ার্ড জেনারেটর
def get_dynamic_password():
    now = datetime.datetime.now()
    if now.hour >= 18:
        target_date = now + datetime.timedelta(days=1)
    else:
        target_date = now
    return f"nagi@{target_date.strftime('%d')}"

# 🧾 ক্রেডেনশিয়াল জেনারেটর (ইনস্টাগ্রাম ও ফেসবুকের জন্য আলাদা নাম)
def generate_credentials(is_fb=False):
    if is_fb:
        # ফেসবুকের জন্য বিদেশি নাম
        first_names = ["Alice", "James", "John", "Robert", "Mary", "Patricia", "Jennifer", "Michael", "William", "David", "Elizabeth", "Barbara"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Visser"]
        username = f"{random.choice(first_names)} {random.choice(last_names)}"
    else:
        # ইনস্টাগ্রামের জন্য ইউজারনেম
        first_names = ["anil", "kamrol", "sabbir", "rafsan", "nafin", "shohan", "tamim", "arif", "joy"]
        last_names = ["azevedo", "khan", "ahmed", "hossain", "chy", "bd", "islam", "rahman"]
        username = f"{random.choice(first_names)}{random.choice(last_names)}{''.join(random.choices(string.digits, k=5))}"
        
    password = get_dynamic_password()
    return username, password

# 📊 গুগল শিটে ডেটা সেভ করার ফাংশন (আলাদা শিট আইডি হ্যান্ডেলিং)
def append_to_google_sheet(sheet_id, row_data):
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds_json = os.getenv("GOOGLE_CREDS")
        if not creds_json: return
            
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1
        sheet.append_row(row_data)
    except Exception as e:
        print(f"Error updating Google Sheet: {e}")

# ডাটা লোড এবং সেভ করার সিস্টেম
def load_data():
    default_data = {
        "balances": {}, "pending_counts": {}, "pending_links": {}, 
        "approved_counts": {}, "rejected_counts": {}, "referred_by": {}, "refer_counts": {}    
    }
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for key in default_data:
                    if key not in data: data[key] = {}
                return data
            except Exception: return default_data
    return default_data

def save_data(data):
    with open(BALANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

BOT_DATA = load_data()
USER_STATES = {}
USER_DATA = {}

# 📱 প্রধান মেনু কিবোর্ড ডিজাইন
def send_user_main_menu(chat_id, text_msg=None):
    if text_msg is None:
        text_msg = (
            f"{DIVIDER_LINE}\n"
            f" {EMOJI_CRYSTAL} <b>WELCOME TO INSTA & FB SELL BD</b> {EMOJI_CRYSTAL} \n"
            f"{DIVIDER_LINE}\n"
            f"পেশাদার ও বিশ্বস্ত উপায়ে আপনার তৈরি করা অ্যাকাউন্ট সেল করুন আমাদের বটের মাধ্যমে।\n\n"
            f"{EMOJI_FIRE} <b>নিচের মেনু থেকে আপনার কাঙ্ক্ষিত অপশনটি বেছে নিন:</b>"
        )
        
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('🚀 অ্যাকাউন্ট জমা দিন'), types.KeyboardButton('💰 আমার অ্যাকাউন্ট / ব্যালেন্স'))
    markup.add(types.KeyboardButton('💳 টাকা তুলুন (Withdraw)'), types.KeyboardButton('🎁 রেফার করে আয়'))
    markup.add(types.KeyboardButton('📊 কাজের গাইডলাইন'), types.KeyboardButton('🎧 হেল্প ও সাপোর্ট'))
    
    if chat_id == ADMIN_ID:
        markup.add(types.KeyboardButton('👑 এডমিন কন্ট্রোল'))
        
    bot.send_message(chat_id, text_msg, reply_markup=markup, parse_mode="HTML")

# 📥 অ্যাকাউন্ট সাবমিট করার প্যানেল (ইনস্টাগ্রাম ও ফেসবুক অপশন)
def send_account_submit_panel(chat_id):
    submit_msg = (
        f"{DIVIDER_LINE}\n"
        f" {EMOJI_FIRE} <b>ACCOUNT SUBMISSION</b> {EMOJI_FIRE} \n"
        f"{DIVIDER_LINE}\n"
        f"⚠️ <b>সতর্কতা:</b> অ্যাকাউন্ট জমা দেওয়ার আগে অবশ্যই পাসওয়ার্ড এবং ইমেইল সঠিক আছে কিনা চেক করে নিন।\n\n"
        f"📌 <b>নিচে থেকে আপনি যে অ্যাকাউন্টটি জমা দিতে চান সেটি সিলেক্ট করুন:</b>"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton('🟣 ইনস্টাগ্রাম টাস্ক (৩.০০ BDT)', callback_data='work_insta_start_generate'),
        types.InlineKeyboardButton('🔵 ফেসবুক ২এফএ টাস্ক (৪.০০ BDT)', callback_data='work_fb_start_generate'),
        types.InlineKeyboardButton('🔙 মেইন মেনু', callback_data='go_to_main_menu')
    )
    bot.send_message(chat_id, submit_msg, reply_markup=markup, parse_mode="HTML")

# 💳 উইথড্রাল মেনু (২০ টাকা লিমিট এবং ৫ টাকা ফি)
def send_withdrawal_menu(chat_id, balance=0.0, total_submitted_acc=0, total_refer=0):
    withdraw_msg = (
        f"{DIVIDER_LINE}\n"
        f" {EMOJI_CRYSTAL} <b>ACCOUNT WITHDRAWAL</b> {EMOJI_CRYSTAL} \n"
        f"{DIVIDER_LINE}\n\n"
        f"{EMOJI_FIRE} <b>Total Account Sold:</b> <code>{total_submitted_acc} 🆔</code>\n"
        f"{DIVIDER_LINE}\n"
        f"{EMOJI_USERS} <b>Total Refer:</b> <code>{total_refer} জন</code>\n"
        f"{DIVIDER_LINE}\n"
        f"{EMOJI_CALENDAR} <b>Your Balance:</b> <code>{balance} ৳</code>\n"
        f"{DIVIDER_LINE}\n"
        f"{EMOJI_LOCK} <b>Minimum Withdraw:</b> <code>২০ ৳</code>\n"
        f"⚠️ <b>উইথড্র চার্জ / ফি:</b> <code>৫ ৳ (প্রতি উইথড্রতে কাটবে)</code>\n\n"
        "📌 <b>পেমেন্ট মেথড সিলেক্ট করুন:</b>"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton('📱 bKash', callback_data='withdraw_bkash'), types.InlineKeyboardButton('⚡ Nagad', callback_data='withdraw_nagad'))
    markup.add(types.InlineKeyboardButton('❌ ক্যানসেল', callback_data='go_to_main_menu'))
    bot.send_message(chat_id, withdraw_msg, reply_markup=markup, parse_mode="HTML")

# 🎁 রেফারেল ড্যাশবোর্ড ডিজাইন
def send_refer_panel(chat_id, refer_count=0):
    bot_info = bot.get_me()
    refer_link = f"https://t.me/{bot_info.username}?start={chat_id}"
    refer_msg = (
        f"{DIVIDER_LINE}\n"
        f" {EMOJI_USERS} <b>REFERRAL PANEL</b> {EMOJI_USERS} \n"
        f"{DIVIDER_LINE}\n"
        f"আপনার বন্ধুদের আমাদের বটে আমন্ত্রণ জানিয়ে প্রতি রেফারে আকর্ষণীয় বোনাস লুফে নিন!\n\n"
        f"{EMOJI_FIRE} <b>মোট সফল রেফার:</b> <code>{refer_count} জন</code>\n"
        f"{DIVIDER_LINE}\n"
        f"{EMOJI_CRYSTAL} <b>আপনার রেফারেল লিংক:</b>\n<code>{refer_link}</code>\n\n"
        f"💡 <i>নিয়মাবলী:</i> আপনার লিংকে কেউ জয়েন করলে সাথে সাথে <b>২ টাকা</b> বোনাস পাবেন। "
        f"তাছাড়া সে আজীবন যতগুলো কাজ করবে তার প্রতিটির মূল্যের <b>১০% কমিশন</b> আপনার অ্যাকাউন্টে অটোমেটিক যোগ হবে!"
    )
    bot.send_message(chat_id, refer_msg, parse_mode="HTML")

# 👑 এডমিন ইনলাইন মেনু
def get_admin_inline_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton('📋 পেন্ডিং ভল্ট', callback_data='admin_pending'), types.InlineKeyboardButton('🔎 ইউজার ট্র্যাক', callback_data='admin_check'))
    markup.add(types.InlineKeyboardButton('✅ কাজ এপ্রুভ', callback_data='admin_approve'), types.InlineKeyboardButton('❌ কাজ রিজেক্ট', callback_data='admin_reject'))
    markup.add(types.InlineKeyboardButton('➕ ব্যালেন্স অ্যাড', callback_data='admin_add_bal'), types.InlineKeyboardButton('⚙️ ইউজার ইন্টারফেস', callback_data='go_to_main_menu'))
    return markup

def check_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception: return False

# /start কমান্ড
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    USER_STATES[user_id] = None
    clear_user_session_messages(message.chat.id, user_id)
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
        send_user_main_menu(message.chat.id)
        if user_id == ADMIN_ID:
            bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} <b>এডমিন কন্ট্রোল প্যানেল:</b>", reply_markup=get_admin_inline_keyboard(), parse_mode="HTML")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🔗 জয়েন চ্যানেল', url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(types.InlineKeyboardButton('✅ জয়েন কমপ্লিট ✅', callback_data='check_joined_btn'))
        
        join_msg = (
            f"{EMOJI_LOCK} <b>ইউজার ভেরিফিকেশন রিকোয়ার্ড!</b>\n"
            f"{DIVIDER_LINE}\n"
            f"বটটি ব্যবহার করতে প্রথমে আমাদের অফিশিয়াল চ্যানেলে জয়েন করুন: {CHANNEL_USERNAME}\n\n"
            f"তারপর নিচে থাকা <b>'✅ জয়েন কমপ্লিট ✅'</b> বাটনে চাপ দিন।"
        )
        bot.send_message(message.chat.id, join_msg, reply_markup=markup, parse_mode="HTML")

# এডমিন কমান্ড ১: পেন্ডিং কাজের লিস্ট দেখা
@bot.message_handler(commands=['pending'])
def view_pending(message):
    if message.from_user.id != ADMIN_ID: return
    msg = f"{EMOJI_CRYSTAL} <b>পেন্ডিং কাজের তালিকা:</b>\n{DIVIDER_LINE}\n"
    has_pending = False
    for uid, count in BOT_DATA["pending_counts"].items():
        if count > 0:
            msg += f"{EMOJI_USERS} আইডি: <code>{uid}</code> ➡️ পেন্ডিং কাজ: <b>{count}টি</b>\n"
            has_pending = True
    if not has_pending: msg += f"{EMOJI_LOCK} ভল্ট খালি! কোনো পেন্ডিং কাজ নেই।"
    msg += f"\n\n{EMOJI_FIRE} <i>লিংক দেখতে:</i> <code>/check [আইডি]</code>\n{EMOJI_CALENDAR} <i>এপ্রুভ করতে:</i> <code>/approve [আইডি] [টাকা] [কয়টি]</code>"
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

# 🔎 এডমিন কমান্ড ৪: লিংক চেক
@bot.message_handler(commands=['check'])
def check_user_links_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()[1:]
    if not args:
        USER_STATES[message.from_user.id] = 'WAITING_FOR_CHECK_ID'
        bot.send_message(message.chat.id, f"{EMOJI_FIRE} যে ইউজারের লিংক দেখতে চান তার টেলিগ্রাম আইডি-টি পাঠান:", parse_mode="HTML")
        return
    
    target_id = args[0]
    links = BOT_DATA.get("pending_links", {}).get(str(target_id), [])
    if not links:
        bot.send_message(message.chat.id, f"{EMOJI_LOCK} ইউজার <code>{target_id}</code> এর কোনো পেন্ডিং কাজের লিংক পাওয়া যায়নি।", parse_mode="HTML")
        return
        
    username_list = []
    for link in links:
        username_list.append(link)
            
    copy_text = "".join([f"{uname}\n" for uname in username_list])
    msg = f"{EMOJI_CRYSTAL} <b>ইউজার <code>{target_id}</code> এর সকল ডাটা:</b>\n{DIVIDER_LINE}\n<code>{copy_text.strip()}</code>"
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
        str_target_id = str(target_id)
        
        if str_target_id in BOT_DATA["pending_counts"] and BOT_DATA["pending_counts"][str_target_id] > 0:
            total_pending = BOT_DATA["pending_counts"][str_target_id]
            if count_to_approve is None or count_to_approve >= total_pending: count_to_approve = total_pending
            
            if str_target_id in BOT_DATA["pending_links"]:
                BOT_DATA["pending_links"][str_target_id] = BOT_DATA["pending_links"][str_target_id][count_to_approve:]
            
            BOT_DATA["pending_counts"][str_target_id] -= count_to_approve
            BOT_DATA["balances"][str_target_id] = BOT_DATA["balances"].get(str_target_id, 0.0) + amount
            BOT_DATA["approved_counts"][str_target_id] = BOT_DATA["approved_counts"].get(str_target_id, 0) + count_to_approve
            
            referrer_id = BOT_DATA.get("referred_by", {}).get(str_target_id)
            if referrer_id and str(referrer_id) in BOT_DATA["balances"]:
                commission_added = amount * REFER_COMMISSION_PERCENT
                BOT_DATA["balances"][str(referrer_id)] += commission_added
                try:
                    ref_msg = (
                        f"{EMOJI_CRYSTAL} <b>রেফারেল কমিশন আপডেট!</b>\n{DIVIDER_LINE}\n"
                        f"{EMOJI_USERS} আপনার বন্ধুর <b>[{count_to_approve}]</b> টি কাজ এপ্রুভ হয়েছে।\n"
                        f"💰 আপনার মূল ব্যালেন্সে লাইফটাইম কমিশন <b>{commission_added:.2f} BDT</b> যোগ করা হয়েছে!"
                    )
                    bot.send_message(int(referrer_id), ref_msg, parse_mode="HTML")
                except Exception: pass
            
            save_data(BOT_DATA)
            bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} ইউজার <code>{target_id}</code> এর {count_to_approve}টি কাজ এপ্রুভ হয়েছে।\n📊 বাকি পেন্ডিং: {BOT_DATA['pending_counts'][str_target_id]}টি", parse_mode="HTML")
            try:
                user_notif = (
                    f"{EMOJI_CRYSTAL} <b>কাজের পেমেন্ট নোটিফিকেশন!</b>\n{DIVIDER_LINE}\n"
                    f"📥 আপনার জমা দেওয়া <b>{count_to_approve}</b>টি কাজ সফলভাবে এপ্রুভ করা হয়েছে।\n"
                    f"💰 ব্যালেন্সে যোগ হয়েছে: <b>{amount} BDT</b>\n"
                    f"{EMOJI_FIRE} বর্তমান ব্যালেন্স: <b>{BOT_DATA['balances'][str_target_id]:.2f} BDT</b>"
                )
                bot.send_message(int(target_id), user_notif, parse_mode="HTML")
            except Exception: pass
        else: bot.send_message(message.chat.id, f"{EMOJI_LOCK} এই ইউজারের কোনো পেন্ডিং কাজ নেই!", parse_mode="HTML")
    except Exception:
        bot.send_message(message.chat.id, f"{EMOJI_LOCK} ভুল ফরম্যাট! লিখুন: <code>/approve ইউজার_আইডি টাকা কয়টি</code>", parse_mode="HTML")

# ❌ এডমিন কমান্ড ৫: কাজ রিজেক্ট করা
@bot.message_handler(commands=['reject'])
def reject_work(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()[1:]
        target_id = args[0]
        count_to_reject = int(args[1])
        reason = " ".join(args[2:]) if len(args) > 2 else "নিয়ম মানা হয়নি"
        str_target_id = str(target_id)
        
        if str_target_id in BOT_DATA["pending_counts"] and BOT_DATA["pending_counts"][str_target_id] > 0:
            total_pending = BOT_DATA["pending_counts"][str_target_id]
            if count_to_reject >= total_pending: count_to_reject = total_pending
            if str_target_id in BOT_DATA["pending_links"]:
                BOT_DATA["pending_links"][str_target_id] = BOT_DATA["pending_links"][str_target_id][count_to_reject:]
            
            BOT_DATA["pending_counts"][str_target_id] -= count_to_reject
            BOT_DATA["rejected_counts"][str_target_id] = BOT_DATA["rejected_counts"].get(str_target_id, 0) + count_to_reject
            save_data(BOT_DATA)
            
            bot.send_message(message.chat.id, f"{EMOJI_LOCK} ইউজার <code>{target_id}</code> এর {count_to_reject}টি কাজ রিজেক্ট করা হয়েছে।", parse_mode="HTML")
            try:
                user_rej_msg = (
                    f"{EMOJI_LOCK} <b>কাজ রিজেক্টের সতর্কবার্তা!</b>\n{DIVIDER_LINE}\n"
                    f"❌ আপনার জমা দেওয়া <b>{count_to_reject}</b>টি কাজ রিজেক্ট করা হয়েছে।\n"
                    f"💬 কারণ: <i>{reason}</i>"
                )
                bot.send_message(int(target_id), user_rej_msg, parse_mode="HTML")
            except Exception: pass
        else: bot.send_message(message.chat.id, f"{EMOJI_LOCK} এই ইউজারের কোনো পেন্ডিং কাজ নেই!", parse_mode="HTML")
    except Exception: bot.send_message(message.chat.id, f"{EMOJI_LOCK} ভুল ফরম্যাট!", parse_mode="HTML")

# ➕ এডমিন কমান্ড ৩: সরাসরি ব্যালেন্স যোগ করা
@bot.message_handler(commands=['add'])
def add_balance(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()[1:]
        target_id = args[0]
        amount = float(args[1])
        str_target_id = str(target_id)
        BOT_DATA["balances"][str_target_id] = BOT_DATA["balances"].get(str_target_id, 0.0) + amount
        save_data(BOT_DATA)
        bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} সফলভাবে যোগ হয়েছে: {amount}৳", parse_mode="HTML")
        try:
            bot.send_message(int(target_id), f"{EMOJI_CRYSTAL} আপনার অ্যাকাউন্টে এডমিন <b>{amount} BDT</b> সরাসরি যোগ করেছেন!", parse_mode="HTML")
        except Exception: pass
    except Exception: bot.send_message(message.chat.id, f"{EMOJI_LOCK} ভুল ফরম্যাট!", parse_mode="HTML")

# সাধারণ মেসেজ ও বটম কিবোর্ড টেক্সট হ্যান্ডেলার
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    str_user_id = str(user_id)
    text = message.text

    if not check_joined(user_id): return

    if text in ['❌ বাতিল করুন', '🔙 ফিরে যান', '❌ বাতিল']:
        USER_STATES[user_id] = None
        clear_user_session_messages(message.chat.id, user_id)
        if user_id in USER_DATA: del USER_DATA[user_id]
        bot.send_message(message.chat.id, f"{EMOJI_LOCK} <b>প্রসেসটি সফলভাবে বাতিল করা হয়েছে।</b>", parse_mode="HTML")
        send_user_main_menu(message.chat.id)
        return

    if user_id == ADMIN_ID and USER_STATES.get(user_id) in ['WAITING_FOR_CHECK_ID', 'WAITING_FOR_APPROVE_DATA', 'WAITING_FOR_REJECT_DATA', 'WAITING_FOR_ADD_DATA']:
        current_state = USER_STATES[user_id]
        USER_STATES[user_id] = None
        if current_state == 'WAITING_FOR_CHECK_ID':
            message.text = f"/check {text}"
            check_user_links_cmd(message)
            return
        elif current_state == 'WAITING_FOR_APPROVE_DATA': message.text = f"/approve {text}"; approve_work(message)
        elif current_state == 'WAITING_FOR_REJECT_DATA': message.text = f"/reject {text}"; reject_work(message)
        elif current_state == 'WAITING_FOR_ADD_DATA': message.text = f"/add {text}"; add_balance(message)
        bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} <b>এডমিন কন্ট্রোল প্যানেল:</b>", reply_markup=get_admin_inline_keyboard(), parse_mode="HTML")
        return

    if text == '🚀 অ্যাকাউন্ট জমা দিন':
        send_account_submit_panel(chat_id=message.chat.id)
        return

    elif text == '💰 আমার অ্যাকাউন্ট / ব্যালেন্স':
        bal = BOT_DATA["balances"].get(str_user_id, 0.0)
        acc_info = (
            f"{DIVIDER_LINE}\n"
            f" {EMOJI_CALENDAR} <b>MY ACCOUNT PROFILE</b> {EMOJI_CALENDAR} \n"
            f"{DIVIDER_LINE}\n\n"
            f"{EMOJI_USERS} <b>ইউজার আইডি:</b> <code>{message.chat.id}</code>\n"
            f"{DIVIDER_LINE}\n"
            f"💰 <b>বর্তমান ব্যালেন্স:</b> <code>{bal:.2f} ৳</code>\n"
            f"{DIVIDER_LINE}\n"
            f"⏳ <b>পেন্ডিং কাজ:</b> <code>{BOT_DATA['pending_counts'].get(str_user_id, 0)}</code> টি\n"
            f"{DIVIDER_LINE}\n"
            f"✅ <b>এপ্রুভড কাজ:</b> <code>{BOT_DATA['approved_counts'].get(str_user_id, 0)}</code> টি\n"
            f"{DIVIDER_LINE}\n"
            f"❌ <b>রিজেক্টেড কাজ:</b> <code>{BOT_DATA['rejected_counts'].get(str_user_id, 0)}</code> টি\n"
            f"{DIVIDER_LINE}"
        )
        bot.send_message(message.chat.id, acc_info, parse_mode="HTML")
        return

    elif text == '💳 টাকা তুলুন (Withdraw)':
        user_balance = BOT_DATA["balances"].get(str_user_id, 0.0)
        sold_accounts = BOT_DATA["approved_counts"].get(str_user_id, 0)
        total_refers = BOT_DATA["refer_counts"].get(str_user_id, 0)
        send_withdrawal_menu(message.chat.id, balance=user_balance, total_submitted_acc=sold_accounts, total_refer=total_refers)
        return

    elif text == '🎁 রেফার করে আয়':
        send_refer_panel(message.chat.id, refer_count=BOT_DATA["refer_counts"].get(str_user_id, 0))
        return

    elif text == '📊 কাজের গাইডলাইন':
        msg = f"{EMOJI_CRYSTAL} <b>আমাদের অফিশিয়াল চ্যানেলে কাজের ভিডিও গাইডলাইন দেওয়া আছে।</b>\n\n📢 লিংক: {CHANNEL_USERNAME}"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")
        return

    elif text == '🎧 হেল্প ও সাপোর্ট':
        msg = f"{EMOJI_USERS} <b>যেকোনো সমস্যায় সরাসরি আমাদের কাস্টমার সাপোর্ট আইডিতে মেসেজ দিন:</b>\n\n👉 @nafin_4x_team"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")
        return

    elif text == '👑 এডমিন কন্ট্রোল' and user_id == ADMIN_ID:
        bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} <b>এডমিন কন্ট্রোল প্যানেল:</b>", reply_markup=get_admin_inline_keyboard(), parse_mode="HTML")
        return

    # 👤 ফেসবুক কাজের জন্য UID ভ্যালিডেশন স্টেট
    if USER_STATES.get(user_id) == 'WAITING_FOR_FB_UID':
        uid_input = text.strip()
        # চেক করা হচ্ছে UID ১৪-১৬ সংখ্যার মধ্যে শুধু নাম্বার কিনা
        if not uid_input.isdigit() or not (14 <= len(uid_input) <= 16):
            bot.send_message(message.chat.id, "❌ <b>ভুল UID!</b> আপনার ফেসবুক অ্যাকাউন্টের সঠিক ১৪ থেকে ১৬ সংখ্যার UID-টি দিন। কম বা বেশি দিলে গ্রহণ করা হবে না।", parse_mode="HTML")
            return
        
        if user_id not in USER_DATA: USER_DATA[user_id] = {}
        USER_DATA[user_id]['fb_uid'] = uid_input
        
        USER_STATES[user_id] = 'WAITING_FOR_FB_2FA'
        m_2fa = bot.send_message(message.chat.id, f"{EMOJI_LOCK} <b>আপনার ফেসবুক অ্যাকাউন্টের 2FA Secret Key-টি এখানে পাঠান:</b> ⤵️", parse_mode="HTML")
        track_msg(user_id, m_2fa)
        return

    # 🔑 ফেসবুক ২এফএ কী সাবমিট প্রসেস
    if USER_STATES.get(user_id) == 'WAITING_FOR_FB_2FA':
        user_input = text.strip().replace(" ", "").upper()
        try:
            missing_padding = len(user_input) % 8
            if missing_padding: user_input += '=' * (8 - missing_padding)
            totp = pyotp.TOTP(user_input)
            code = totp.now()
            
            USER_DATA[user_id]['2fa_key'] = user_input
            
            m1 = bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} ফেসবুক অ্যাকাউন্ট সম্পূর্ণ ভেরিফাই হলে নিচের বাটনে প্রেস করবেন।", parse_mode="HTML")
            m2 = bot.send_message(message.chat.id, f"{EMOJI_FIRE} <b>নিচের ওটিপি কোডটি টাচ করে কপি করুন:</b>\n\n<code>{code}</code>", parse_mode="HTML")
            
            finish_markup = types.InlineKeyboardMarkup()
            finish_markup.add(types.InlineKeyboardButton('✅ ফেসবুক অ্যাকাউন্ট তৈরি শেষ', callback_data='work_fb_finish_done'))
            finish_markup.add(types.InlineKeyboardButton('❌ বাতিল', callback_data='go_to_main_menu'))
            m3 = bot.send_message(message.chat.id, f"{EMOJI_LOCK} <b>ফাইনাল সাবমিট করার বাটন:</b>", reply_markup=finish_markup, parse_mode="HTML")
            
            track_msg(user_id, message)
            track_msg(user_id, m1)
            track_msg(user_id, m2)
            track_msg(user_id, m3)
            
            USER_STATES[user_id] = 'WAITING_FOR_FINISH'
        except Exception:
            bot.send_message(message.chat.id, f"{EMOJI_LOCK} <b>ভুল 2FA Key!</b> সঠিক সিক্রেট কী আবার দিন।", parse_mode="HTML")
            send_user_main_menu(message.chat.id)
            USER_STATES[user_id] = None
        return

    # 📋 ইনস্টাগ্রাম ২এফএ কি সাবমিট করার প্রসেস
    if USER_STATES.get(user_id) == 'WAITING_FOR_2FA_KEY':
        user_input = text.strip().replace(" ", "").upper()
        try:
            missing_padding = len(user_input) % 8
            if missing_padding: user_input += '=' * (8 - missing_padding)
            totp = pyotp.TOTP(user_input)
            code = totp.now()
            
            if user_id not in USER_DATA: USER_DATA[user_id] = {}
            USER_DATA[user_id]['2fa_key'] = user_input
            
            m1 = bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} অ্যাকাউন্ট সম্পূর্ণ রেডি হলে নিচের বাটনে প্রেস করবেন।", parse_mode="HTML")
            m2 = bot.send_message(message.chat.id, f"{EMOJI_FIRE} <b>নিচের ওটিপি কোডটি টাচ করে কপি করুন:</b>\n\n<code>{code}</code>", parse_mode="HTML")
            
            finish_markup = types.InlineKeyboardMarkup()
            finish_markup.add(types.InlineKeyboardButton('✅ অ্যাকাউন্ট তৈরি শেষ', callback_data='work_finish_done'))
            finish_markup.add(types.InlineKeyboardButton('❌ বাতিল', callback_data='go_to_main_menu'))
            m3 = bot.send_message(message.chat.id, f"{EMOJI_LOCK} <b>ফাইনাল সাবমিট করার বাটন:</b>", reply_markup=finish_markup, parse_mode="HTML")
            
            track_msg(user_id, message)
            track_msg(user_id, m1)
            track_msg(user_id, m2)
            track_msg(user_id, m3)
            
            USER_STATES[user_id] = 'WAITING_FOR_FINISH'
        except Exception:
            bot.send_message(message.chat.id, f"{EMOJI_LOCK} <b>ভুল 2FA Key!</b> সঠিক সিক্রেট কী আবার দিন।", parse_mode="HTML")
            send_user_main_menu(message.chat.id)
            USER_STATES[user_id] = None
        return
        
    if USER_STATES.get(user_id) in ['WAITING_FOR_BKASH_NUMBER', 'WAITING_FOR_NAGAD_NUMBER']:
        if user_id not in USER_DATA: USER_DATA[user_id] = {}
        USER_DATA[user_id]['number'] = text
        method_type = "BKASH" if USER_STATES[user_id] == 'WAITING_FOR_BKASH_NUMBER' else "NAGAD"
        USER_DATA[user_id]['method'] = method_type
        
        USER_STATES[user_id] = 'WAITING_FOR_AMOUNT'
        
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton('❌ বাতিল করুন'))
        bot.send_message(message.chat.id, f"{EMOJI_CALENDAR} কত টাকা উত্তোলন করতে চান? (সর্বনিম্ন ২০৳ এবং উইথড্র ফি ৫৳):", reply_markup=cancel_markup, parse_mode="HTML")
        return

    # 💳 উইথড্রাল অ্যামাউন্ট ভ্যালিডেশন এবং ৫ টাকা ফি লজিক সেটআপ
    if USER_STATES.get(user_id) == 'WAITING_FOR_AMOUNT':
        try:
            amt = float(text)
            saved_method = USER_DATA.get(user_id, {}).get('method', 'BKASH')
            method_name = "বিকাশ" if saved_method == "BKASH" else "নগদ"
            min_amt = 20.0  
            fee_amt = 5.0   
            total_deduction = amt + fee_amt 
            
            if amt < min_amt:
                bot.send_message(message.chat.id, f"{EMOJI_LOCK} রিকোয়েস্ট ক্যানসেল! সর্বনিম্ন {min_amt:.0f}৳ উত্তোলন করতে হবে।", parse_mode="HTML")
            else:
                user_bal = BOT_DATA["balances"].get(str_user_id, 0.0)
                if user_bal < total_deduction:
                    bot.send_message(message.chat.id, f"{EMOJI_LOCK} পর্যাপ্ত ব্যালেন্স নেই!\n🔥 ৫৳ উইথড্র ফি সহ আপনার মোট প্রয়োজন: <b>{total_deduction:.2f} BDT</b>\n📌 আপনার বর্তমান ব্যালেন্স: {user_bal:.2f} BDT", parse_mode="HTML")
                else:
                    BOT_DATA["balances"][str_user_id] -= total_deduction
                    save_data(BOT_DATA)
                    num = USER_DATA.get(user_id, {}).get('number', 'N/A')
                    
                    withdraw_group_msg = (
                        f"{EMOJI_CRYSTAL} <b>নতুন উইথड्र রিকোয়েস্ট</b>\n{DIVIDER_LINE}\n"
                        f"👤 নাম: {message.from_user.first_name}\n"
                        f"🆔 আইডি: <code>{user_id}</code>\n"
                        f"💳 মাধ্যম: <b>{method_name}</b>\n"
                        f"📱 নাম্বার: <code>{num}</code>\n"
                        f"💰 ইউজার পাবে: <b>{amt:.2f} BDT</b>\n"
                        f"⛽ উইথড্র ফি কাটা হয়েছে: <b>{fee_amt:.2f} BDT</b>\n"
                        f"📊 মোট কাটা হয়েছে: <b>{total_deduction:.2f} BDT</b>"
                    )
                    try: bot.send_message(WITHDRAW_GROUP_ID, withdraw_group_msg, parse_mode="HTML")
                    except Exception: pass
                    
                    bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} আপনার উইথড্র রিকোয়েস্ট সফল হয়েছে!\n📉 (৫৳ ফি সহ মোট {total_deduction:.2f}৳ কাটা হয়েছে)\n🔥 বর্তমান মূল ব্যালেন্স: {BOT_DATA['balances'][str_user_id]:.2f} BDT", parse_mode="HTML")
        except ValueError:
            bot.send_message(message.chat.id, f"{EMOJI_LOCK} ভুল অ্যামাউন্ট! শুধুমাত্র সংখ্যায় টাকার পরিমাণ লিখুন।", parse_mode="HTML")
        
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
                    try: bot.send_message(int(referrer), f"{EMOJI_CRYSTAL} <b>রেফার বোনাস সফল!</b>\n\n💰 ব্যালেন্সে <b>{REFER_BONUS:.2f} Tk</b> যোগ হয়েছে।", parse_mode="HTML")
                    except Exception: pass
                save_data(BOT_DATA)
            
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception: pass
            bot.send_message(call.message.chat.id, f"{EMOJI_CRYSTAL} স্বাগতম আমাদের Official Sell BD Bot এ 🫠🤗", parse_mode="HTML")
            send_user_main_menu(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "⚠️ আপনি এখনও চ্যানেলে জয়েন করেননি!", show_alert=True)
        return

    if not check_joined(user_id): return
        
    # 🟣 ইনস্টাগ্রাম টাস্ক স্টার্ট জেনারেটর
    if call.data == 'work_insta_start_generate':
        uname, upass = generate_credentials(is_fb=False)
        if user_id not in USER_DATA: USER_DATA[user_id] = {}
        USER_DATA[user_id]['generated_username'] = uname
        USER_DATA[user_id]['generated_password'] = upass
        USER_DATA[user_id]['task_type'] = 'INSTA'
        
        msg = (
            f"{DIVIDER_LINE}\n"
            f"🧾 <b>ইনস্টাগ্রাম ক্রেডেনশিয়াল:</b>\n"
            f"{DIVIDER_LINE}\n"
            f"👤 Username: <code>{uname}</code>\n"
            f"🔐 Password: <code>{upass}</code>\n"
            f"{DIVIDER_LINE}\n"
            f"{EMOJI_FIRE} এই তথ্যগুলো দিয়ে অ্যাকাউন্ট খুলে নিচের <b>🔒 2FA Set</b> বাটনে ক্লিক করুন।"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔒 2FA Set করুন", callback_data="open_2fa_input"))
        markup.add(types.InlineKeyboardButton("❌ বাতিল", callback_data="go_to_main_menu"))
        m_gen = bot.send_message(call.message.chat.id, msg, parse_mode="HTML", reply_markup=markup)
        track_msg(user_id, m_gen)
        bot.answer_callback_query(call.id)

    # 🔵 ফেসবুক টাস্ক স্টার্ট জেনারেটর (বিদেশি নাম সহ)
    elif call.data == 'work_fb_start_generate':
        fullname, upass = generate_credentials(is_fb=True)
        name_parts = fullname.split(" ")
        first_n = name_parts[0]
        last_n = name_parts[1]
        
        if user_id not in USER_DATA: USER_DATA[user_id] = {}
        USER_DATA[user_id]['fb_name'] = fullname
        USER_DATA[user_id]['generated_password'] = upass
        USER_DATA[user_id]['task_type'] = 'FACEBOOK'
        
        msg = (
            f"👤 First name: <code>{first_n}</code>\n"
            f"👤 Last name: <code>{last_n}</code>\n"
            f"🔐 Password: <code>{upass}</code>\n\n"
            f"📱 উপরের তথ্য দিয়ে অ্যাকাউন্ট খুলে নিচে <b>Send UID</b> বাটনে চাপ দিন😁"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("Send UID", callback_data="open_fb_uid_input"),
            types.InlineKeyboardButton("❓ কিভাবে কাজ করব", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            types.InlineKeyboardButton("❌ বাতিল", callback_data="go_to_main_menu")
        )
        m_gen = bot.send_message(call.message.chat.id, msg, parse_mode="HTML", reply_markup=markup)
        track_msg(user_id, m_gen)
        bot.answer_callback_query(call.id)

    elif call.data == "open_fb_uid_input":
        USER_STATES[user_id] = 'WAITING_FOR_FB_UID'
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton('❌ বাতিল করুন'))
        bot.send_message(call.message.chat.id, "📝 আপনার ফেসবুক অ্যাকাউন্টের ১৪ থেকে ১৬ সংখ্যার UID-টি দিন:", reply_markup=cancel_markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)
        
    elif call.data == "open_2fa_input":
        USER_STATES[user_id] = 'WAITING_FOR_2FA_KEY'
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton('❌ বাতিল করুন'))
        m_input = bot.send_message(call.message.chat.id, f"{EMOJI_LOCK} <b>আপনার অ্যাকাউন্টের 2FA Secret Key-টি এখানে পাঠান:</b> ⤵️", reply_markup=cancel_markup, parse_mode="HTML")
        track_msg(user_id, m_input)
        bot.answer_callback_query(call.id)
        
    # 🟣 ইনস্টাগ্রাম ফাইনাল সাবমিট
    elif call.data == 'work_finish_done':
        generated_uname = USER_DATA.get(user_id, {}).get('generated_username')
        generated_upass = USER_DATA.get(user_id, {}).get('generated_password')
        saved_2fa = USER_DATA.get(user_id, {}).get('2fa_key')
        
        if not generated_uname or not saved_2fa:
            clear_user_session_messages(call.message.chat.id, user_id)
            bot.send_message(call.message.chat.id, f"{EMOJI_LOCK} কোনো সেশন ডাটা পাওয়া যায়নি।", parse_mode="HTML")
            send_user_main_menu(call.message.chat.id)
            return

        if str_user_id not in BOT_DATA["pending_links"]: BOT_DATA["pending_links"][str_user_id] = []
        
        work_details = f"Type: INSTA | Uname: {generated_uname} | Pass: {generated_upass} | 2FA: {saved_2fa}"
        BOT_DATA["pending_links"][str_user_id].append(work_details)
        BOT_DATA["pending_counts"][str_user_id] = BOT_DATA["pending_counts"].get(str_user_id, 0) + 1
        save_data(BOT_DATA)
        
        # ইনস্টাগ্রাম ডেটা ইনস্টাগ্রাম শিটে সেভ হবে
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        append_to_google_sheet(INSTA_SPREADSHEET_ID, [now_time, generated_uname, generated_upass, saved_2fa, str_user_id, call.from_user.first_name])
        
        clear_user_session_messages(call.message.chat.id, user_id)
        bot.send_message(call.message.chat.id, f"{EMOJI_CRYSTAL} <b>ইনস্টাগ্রাম অ্যাকাউন্টটি সফলভাবে সাবমিট করা হয়েছে!</b>", parse_mode="HTML")
        send_user_main_menu(call.message.chat.id)
        if user_id in USER_DATA: del USER_DATA[user_id]
        USER_STATES[user_id] = None
        bot.answer_callback_query(call.id)

     # 🔵 ফেসবুক ফাইনাল সাবমিট
    elif call.data == 'work_fb_finish_done':
        fb_name = USER_DATA.get(user_id, {}).get('fb_name')
        generated_upass = USER_DATA.get(user_id, {}).get('generated_password')
        fb_uid = USER_DATA.get(user_id, {}).get('fb_uid')
        saved_2fa = USER_DATA.get(user_id, {}).get('2fa_key')
        
        if not fb_uid or not saved_2fa:
            clear_user_session_messages(call.message.chat.id, user_id)
            bot.send_message(call.message.chat.id, f"{EMOJI_LOCK} ডাটা ত্রুটি! আবার চেষ্টা করুন।", parse_mode="HTML")
            send_user_main_menu(call.message.chat.id)
            return

        if str_user_id not in BOT_DATA["pending_links"]: BOT_DATA["pending_links"][str_user_id] = []
        
        work_details = f"Type: FB | UID: {fb_uid} | Name: {fb_name} | Pass: {generated_upass} | 2FA: {saved_2fa}"
        BOT_DATA["pending_links"][str_user_id].append(work_details)
        BOT_DATA["pending_counts"][str_user_id] = BOT_DATA["pending_counts"].get(str_user_id, 0) + 1
        save_data(BOT_DATA)
        
        # ফেসবুক ডেটা সম্পূর্ণ আলাদা ফেসবুক শিটে সেভ হবে
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        append_to_google_sheet(FB_SPREADSHEET_ID, [now_time, fb_uid, fb_name, generated_upass, saved_2fa, str_user_id, call.from_user.first_name])
        
        clear_user_session_messages(call.message.chat.id, user_id)
        bot.send_message(call.message.chat.id, f"{EMOJI_CRYSTAL} <b>ফেসবুক অ্যাকাউন্টটি সফলভাবে আলাদা ডাটাবেজে সাবমিট করা হয়েছে!</b>", parse_mode="HTML")
        send_user_main_menu(call.message.chat.id)
        if user_id in USER_DATA: del USER_DATA[user_id]
        USER_STATES[user_id] = None
        bot.answer_callback_query(call.id)

    elif call.data in ['withdraw_bkash', 'withdraw_nagad']:
        method = "বিকাশ" if call.data == 'withdraw_bkash' else "নগদ"
        USER_STATES[user_id] = 'WAITING_FOR_BKASH_NUMBER' if call.data == 'withdraw_bkash' else 'WAITING_FOR_NAGAD_NUMBER'
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton('❌ বাতিল করুন'))
        bot.send_message(call.message.chat.id, f"{EMOJI_FIRE} আপনার পার্সোনাল <b>{method}</b> নাম্বারটি এখানে টাইপ করুন:", reply_markup=cancel_markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)

    elif call.data == 'go_to_main_menu':
        USER_STATES[user_id] = None
        clear_user_session_messages(call.message.chat.id, user_id)
        if user_id in USER_DATA: del USER_DATA[user_id]
        bot.send_message(call.message.chat.id, f"{EMOJI_LOCK} প্রসেসটি বাতিল করা হয়েছে।", parse_mode="HTML")
        send_user_main_menu(call.message.chat.id, f"{DIVIDER_LINE}\n{EMOJI_CRYSTAL} <b>মেইন মেনু:</b>")
        bot.answer_callback_query(call.id)

    elif call.data == 'admin_pending':
        bot.answer_callback_query(call.id)
        class DummyMessage:
            def __init__(self, uid, cid):
                self.from_user = type('User', (object,), {'id': uid})()
                self.chat = type('Chat', (object,), {'id': cid})()
        view_pending(DummyMessage(user_id, call.message.chat.id))
        
    elif call.data == 'admin_check':
        USER_STATES[user_id] = 'WAITING_FOR_CHECK_ID'
        bot.send_message(call.message.chat.id, f"{EMOJI_FIRE} যে ইউজারের লিংক দেখতে চান তার আইডি দিন:", parse_mode="HTML")
        bot.answer_callback_query(call.id)
        
    elif call.data == 'admin_approve':
        USER_STATES[user_id] = 'WAITING_FOR_APPROVE_DATA'
        bot.send_message(call.message.chat.id, f"{EMOJI_CRYSTAL} ফরম্যাট: <code>আইডি টাকা কয়টি</code>", parse_mode="HTML")
        bot.answer_callback_query(call.id)
        
    elif call.data == 'admin_reject':
        USER_STATES[user_id] = 'WAITING_FOR_REJECT_DATA'
        bot.send_message(call.message.chat.id, f"{EMOJI_LOCK} ফরম্যাট: <code>আইডি কয়টি কারণ</code>", parse_mode="HTML")
        bot.answer_callback_query(call.id)
        
    elif call.data == 'admin_add_bal':
        USER_STATES[user_id] = 'WAITING_FOR_ADD_DATA'
        bot.send_message(call.message.chat.id, f"{EMOJI_CRYSTAL} ফরম্যাট: <code>আইডি টাকা</code>", parse_mode="HTML")
        bot.answer_callback_query(call.id)

if __name__ == '__main__':
    bot.infinity_polling(skip_pending=True)
