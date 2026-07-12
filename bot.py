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

‎# ⚙️ BOT TOKEN & CONFIG
‎TOKEN = os.getenv("BOT_TOKEN")
‎bot = telebot.TeleBot(TOKEN)
‎
‎# 🔄 নতুন চ্যানেল/গ্রুপ ইউজারনেম আপডেট করা হয়েছে
‎CHANNEL_USERNAME = "@facebook_account_sell_bot_group"
‎ADMIN_ID = 6345226762  # আপনার টেলিগ্রাম আইডি
‎WITHDRAW_GROUP_ID = "@igsellonly"  # উইথড্র রিকোয়েস্ট গ্রুপ ইউজারনেম
‎BALANCE_FILE = "balances.json"
‎
‎# 📊 গুগল শিট আইডি (ঠিক করা হয়েছে)
‎INSTA_SPREADSHEET_ID = "1kcQNx7bSfesKzL_zzS0u2pmU1bxoZzhV0rvB0Nq5ODU"
‎FB_SPREADSHEET_ID = "1FNpws7CqVDdhN00c-fksi_r517B7rtmnixze1ibNlbE"
‎
‎# 💎 কাস্টম অ্যানিমেটেড ইমোজি ও ডিভাইডার আইডি সেটআপ
‎DIVIDER = "<tg-emoji emoji-id='5870818207383686839'>━</tg-emoji>"
‎DIVIDER_LINE = DIVIDER * 7
‎
‎EMOJI_CRYSTAL = "<tg-emoji emoji-id='5353027129250453493'>🔮</tg-emoji>"
‎EMOJI_FIRE    = "<tg-emoji emoji-id='5334763399299506604'>🔥</tg-emoji>"
‎EMOJI_USERS   = "<tg-emoji emoji-id='5420145051336485498'>👥</tg-emoji>"
‎EMOJI_CALENDAR= "<tg-emoji emoji-id='5352585194295564660'>📅</tg-emoji>"
‎EMOJI_LOCK    = "<tg-emoji emoji-id='5337255927735163754'>🔒</tg-emoji>"
‎
‎USER_STATES = {}
‎USER_DATA = {}
‎
‎
‎# ডাটা লোড এবং সেভ করার সিস্টেম (নিশ্চিত করে ডাটা লস হবে না)
‎def load_data():
‎    default_data = {
‎        "balances": {}, "pending_counts": {}, "pending_links": {}, 
‎        "approved_counts": {}, "rejected_counts": {}, "referred_by": {}, "refer_counts": {},
‎        "config": {
‎            "REFER_BONUS": 2.0,
‎            "REFER_COMMISSION_PERCENT": 0.10,
‎            "INSTA_RATE": 3.00,
‎            "FB_RATE": 4.00,
‎            "MIN_WITHDRAW": 20.0,
‎            "WITHDRAW_FEE": 5.0
‎        }
‎    }
‎    if os.path.exists(BALANCE_FILE):
‎        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
‎            try:
‎                data = json.load(f)
‎                for key in default_data:
‎                    if key not in data: data[key] = default_data[key]
‎                # জোড়পূর্বক config কী-গুলো নিশ্চিত করা
‎                for ckey in default_data["config"]:
‎                    if ckey not in data["config"]: data["config"][ckey] = default_data["config"][ckey]
‎                return data
‎            except Exception: return default_data
‎    return default_data
‎
‎def save_data(data):
‎    with open(BALANCE_FILE, "w", encoding="utf-8") as f:
‎        json.dump(data, f, indent=4, ensure_ascii=False)
‎
‎BOT_DATA = load_data()
‎
‎# ডাইনামিক কনফিগারেশন সহজে অ্যাক্সেস করার শর্টকাট ফাংশন
‎def get_cfg(key):
‎    return BOT_DATA["config"].get(key)
‎
‎# 🔄 মেসেজ ট্র্যাক এবং অটো-ডিলিট করার ফাংশনসমূহ
‎def track_msg(user_id, message_obj):
‎    if not message_obj: return
‎    if user_id not in USER_DATA: USER_DATA[user_id] = {}
‎    if 'msg_ids' not in USER_DATA[user_id]: USER_DATA[user_id]['msg_ids'] = []
‎    USER_DATA[user_id]['msg_ids'].append(message_obj.message_id)
‎
‎def clear_user_session_messages(chat_id, user_id):
‎    if user_id in USER_DATA and 'msg_ids' in USER_DATA[user_id]:
‎        for msg_id in USER_DATA[user_id]['msg_ids']:
‎            try: bot.delete_message(chat_id, msg_id)
‎            except Exception: pass
‎        USER_DATA[user_id]['msg_ids'] = []
‎
‎# 📆 Passwords Generation Logic
‎def get_dynamic_password():
‎    now = datetime.datetime.now()
‎    if now.hour >= 18: target_date = now + datetime.timedelta(days=1)
‎    else: target_date = now
‎    return f"nagi@{target_date.strftime('%d')}"
‎
‎# 🧾 ক্রেডেনশিয়াল জেনারেটর
‎def generate_credentials(is_fb=False):
‎    if is_fb:
‎        first_names = ["Alice", "James", "John", "Robert", "Mary", "Patricia", "Jennifer", "Michael", "William", "David", "Elizabeth", "Barbara"]
‎        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Visser"]
‎        username = f"{random.choice(first_names)} {random.choice(last_names)}"
‎    else:
‎        first_names = ["anil", "kamrol", "sabbir", "rafsan", "nafin", "shohan", "tamim", "arif", "joy"]
‎        last_names = ["azevedo", "khan", "ahmed", "hossain", "chy", "bd", "islam", "rahman"]
‎        username = f"{random.choice(first_names)}{random.choice(last_names)}{''.join(random.choices(string.digits, k=5))}"
‎    return username, get_dynamic_password()
‎
‎# 📊 গুগল শিটে ডেটা সেভ করার ফাংশন
‎def append_to_google_sheet(sheet_id, row_data):
‎    try:
‎        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
‎        creds_json = os.getenv("GOOGLE_CREDS")
‎        if not creds_json: return
‎        creds_dict = json.loads(creds_json)
‎        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
‎        client = gspread.authorize(creds)
‎        sheet = client.open_by_key(sheet_id).sheet1
‎        
‎        # 🛠️ অটোমেটিক কলাম সিরিয়াল ঠিক করার ট্রিক:
‎        # row_data এর ভেতর থেকে টেলিগ্রাম আইডি (যা শুধু সংখ্যা) খুঁজে বের করা
‎        telegram_id = None
‎        username_val = "Unknown"
‎        
‎        for item in row_data:
‎            cleaned = str(item).strip()
‎            if cleaned.isdigit() and len(cleaned) >= 8:  # সাধারণত টেলিগ্রাম আইডি ৮-১০ ডিজিটের সংখ্যা হয়
‎                telegram_id = cleaned
‎                break
‎                
‎        # যদি আইডি পাওয়া যায়, তবে সেটিকে ঠিক ৬ নম্বর (F) কলামে এবং নামটিকে ৭ নম্বর (G) কলামে সেট করা
‎        if telegram_id:
‎            # প্রথমে row_data থেকে আইডি এবং নাম (যদি থাকে) সাময়িকভাবে রিমুভ করে ক্লিন করা
‎            clean_row = [x for x in row_data if str(x).strip() != telegram_id]
‎            
‎            # যদি সিস্টেমে কোনো ইউজারনেম/লিংক থাকে, সেটাকে আলাদা করা
‎            if len(clean_row) > 0:
‎                username_val = clean_row[-1] # শেষের ডাটাটিই সাধারণত ইউজারনেম বা লিংক হয়
‎                clean_row = clean_row[:-1]
‎            
‎            # এখন নতুনভাবে কলাম সাজানো: A, B, C, D, E কলামে আগের তথ্য থাকবে
‎            final_row = clean_row[:5]
‎            
‎            # যদি আগের তথ্য ৫টির কম হয়, তবে খালি ঘর দিয়ে ৫টি কলাম পূরণ করা
‎            while len(final_row) < 5:
‎                final_row.append("")
‎                
‎            final_row.append(str(telegram_id)) # কলাম ৬ (F) -> এখানে বসবে শুধু সংখ্যা আইডি
‎            final_row.append(str(username_val)) # কলাম ৭ (G) -> এখানে বসবে ইউজারনেম বা লিংক
‎            
‎            # যদি আরও অতিরিক্ত কোনো ডাটা থাকে (যেমন পাসওয়ার্ড), তা এরপরে বসবে
‎            if len(clean_row) > 5:
‎                final_row.extend(clean_row[5:])
‎                
‎            row_data = final_row
‎
‎        sheet.append_row(row_data)
‎    except Exception as e: 
‎        print(f"Error updating Google Sheet: {e}")
‎        
‎# 📱 প্রধান মেনু কিবোর্ড ডিজাইন
‎def send_user_main_menu(chat_id, text_msg=None):
‎    if text_msg is None:
‎        text_msg = (
‎            f"{DIVIDER_LINE}\n"
‎            f" {EMOJI_CRYSTAL} <b>WELCOME TO INSTA & FB SELL BD</b> {EMOJI_CRYSTAL} \n"
‎            f"{DIVIDER_LINE}\n"
‎            f"পেশাদার ও বিশ্বস্ত উপায়ে আপনার তৈরি করা অ্যাকাউন্ট সেল করুন আমাদের বটের মাধ্যমে।\n\n"
‎            f"{EMOJI_FIRE} <b>নিচের মেনু থেকে আপনার কাঙ্ক্ষিত অপশনটি বেছে নিন:</b>"
‎        )
‎    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
‎    markup.add(types.KeyboardButton('🚀 অ্যাকাউন্ট জমা দিন'), types.KeyboardButton('💰 আমার অ্যাকাউন্ট / ব্যালেন্স'))
‎    markup.add(types.KeyboardButton('💳 টাকা তুলুন (Withdraw)'), types.KeyboardButton('🎁 রেফার করে আয়'))
‎    markup.add(types.KeyboardButton('📊 কাজের গাইডলাইন'), types.KeyboardButton('🎧 হেল্প ও সাপোর্ট'))
‎    if chat_id == ADMIN_ID: markup.add(types.KeyboardButton('👑 এডমিন কন্ট্রোল'))
‎    bot.send_message(chat_id, text_msg, reply_markup=markup, parse_mode="HTML")
‎
‎# 📥 অ্যাকাউন্ট সাবমিট করার প্যানেল
‎def send_account_submit_panel(chat_id):
‎    submit_msg = (
‎        f"{DIVIDER_LINE}\n"
‎        f" {EMOJI_FIRE} <b>ACCOUNT SUBMISSION</b> {EMOJI_FIRE} \n"
‎        f"{DIVIDER_LINE}\n"
‎        f"⚠️ <b>সতর্কতা:</b> অ্যাকাউন্ট জমা দেওয়ার আগে অবশ্যই পাসওয়ার্ড এবং ইমেইল সঠিক আছে কিনা চেক করে নিন।\n\n"
‎        f"📌 <b>নিচে থেকে আপনি যে অ্যাকাউন্টটি জমা দিতে চান সেটি সিলেক্ট করুন:</b>"
‎    )
‎    markup = types.InlineKeyboardMarkup(row_width=1)
‎    markup.add(
‎        types.InlineKeyboardButton(f'🟣 ইনস্টাগ্রাম টাস্ক ({get_cfg("INSTA_RATE"):.2f} BDT)', callback_data='work_insta_start_generate'),
‎        types.InlineKeyboardButton(f'🔵 ফেসবুক ২ কুকিজ টাস্ক ({get_cfg("FB_RATE"):.2f} BDT)', callback_data='work_fb_start_generate'),
‎        types.InlineKeyboardButton('🔙 মেইন মেনু', callback_data='go_to_main_menu')
‎    )
‎    bot.send_message(chat_id, submit_msg, reply_markup=markup, parse_mode="HTML")
‎
‎# 💳 উইথড্রাল মেনু
‎def send_withdrawal_menu(chat_id, balance=0.0, total_submitted_acc=0, total_refer=0):
‎    withdraw_msg = (
‎        f"{DIVIDER_LINE}\n"
‎        f" {EMOJI_CRYSTAL} <b>ACCOUNT WITHDRAWAL</b> {EMOJI_CRYSTAL} \n"
‎        f"{DIVIDER_LINE}\n\n"
‎        f"{EMOJI_FIRE} <b>Total Account Sold:</b> <code>{total_submitted_acc} 🆔</code>\n"
‎        f"{DIVIDER_LINE}\n"
‎        f"{EMOJI_USERS} <b>Total Refer:</b> <code>{total_refer} জন</code>\n"
‎        f"{DIVIDER_LINE}\n"
‎        f"{EMOJI_CALENDAR} <b>Your Balance:</b> <code>{balance:.2f} ৳</code>\n"
‎        f"{DIVIDER_LINE}\n"
‎        f"{EMOJI_LOCK} <b>Minimum Withdraw:</b> <code>{get_cfg('MIN_WITHDRAW'):.0f} ৳</code>\n"
‎        f"⚠️ <b>উইথড্র চার্জ / ফি:</b> <code>{get_cfg('WITHDRAW_FEE'):.0f} ৳ (প্রতি উইথড্রতে কাটবে)</code>\n\n"
‎        "📌 <b>পেমেন্ট মেথড সিলেক্ট করুন:</b>"
‎    )
‎    markup = types.InlineKeyboardMarkup(row_width=2)
‎    markup.add(types.InlineKeyboardButton('📱 bKash', callback_data='withdraw_bkash'), types.InlineKeyboardButton('⚡ Nagad', callback_data='withdraw_nagad'))
‎    markup.add(types.InlineKeyboardButton('❌ ক্যানসেল', callback_data='go_to_main_menu'))
‎    bot.send_message(chat_id, withdraw_msg, reply_markup=markup, parse_mode="HTML")
‎
‎# 🎁 রেফারেল ড্যাশবোর্ড
‎def send_refer_panel(chat_id, refer_count=0):
‎    bot_info = bot.get_me()
‎    refer_link = f"https://t.me/{bot_info.username}?start={chat_id}"
‎    refer_msg = (
‎        f"{DIVIDER_LINE}\n"
‎        f" {EMOJI_USERS} <b>REFERRAL PANEL</b> {EMOJI_USERS} \n"
‎        f"{DIVIDER_LINE}\n"
‎        f"আপনার বন্ধুদের আমাদের বটে আমন্ত্রণ জানিয়ে প্রতি রেফারে আকর্ষণীয় বোনাস লুফে নিন!\n\n"
‎        f"{EMOJI_FIRE} <b>মোট সফল রেফার:</b> <code>{refer_count} জন</code>\n"
‎        f"{DIVIDER_LINE}\n"
‎        f"{EMOJI_CRYSTAL} <b>আপনার রেফারেল লিংক:</b>\n<code>{refer_link}</code>\n\n"
‎        f"💡 <i>নিয়মাবলী:</i> আপনার লিংকে কেউ জয়েন করলে সাথে সাথে <b>{get_cfg('REFER_BONUS'):.0f} টাকা</b> বোনাস পাবেন। "
‎        f"তাছাড়া সে আজীবন যতগুলো কাজ করবে তার প্রতিটির মূল্যের <b>{get_cfg('REFER_COMMISSION_PERCENT')*100:.0f}% কমিশন</b> আপনার অ্যাকাউন্টে অটোমেটিক যোগ হবে!"
‎    )
‎    bot.send_message(chat_id, refer_msg, parse_mode="HTML")
‎
‎# 👑 এডমিন ইনলাইন মেনু (সুপার এডমিন কন্ট্রোল প্যানেল)
‎def get_admin_inline_keyboard():
‎    markup = types.InlineKeyboardMarkup(row_width=2)
‎    markup.add(types.InlineKeyboardButton('📋 পেন্ডিং ভল্ট', callback_data='ask_admin_pending'), types.InlineKeyboardButton('🔎 ইউজার ট্র্যাক', callback_data='admin_check'))
‎    markup.add(types.InlineKeyboardButton('✅ কাজ এপ্রুভ', callback_data='admin_approve'), types.InlineKeyboardButton('❌ কাজ রিজেক্ট', callback_data='admin_reject'))
‎    markup.add(types.InlineKeyboardButton('➕ ব্যালেন্স অ্যাড', callback_data='admin_add_bal'), types.InlineKeyboardButton('📩 ইউজারকে মেসেজ পাঠান', callback_data='admin_msg_user'))
‎    markup.add(types.InlineKeyboardButton('⚙️ বটের রেট/সেটিংস পরিবর্তন', callback_data='admin_change_rates'))
‎    markup.add(types.InlineKeyboardButton('🏠 ইউজার ইন্টারফেস', callback_data='go_to_main_menu'))
‎    return markup
‎
‎def check_joined(user_id):
‎    try:
‎        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
‎        return member.status in ['member', 'administrator', 'creator']
‎    except Exception: return False
‎
‎# /start কমান্ড
‎@bot.message_handler(commands=['start'])
‎def start_cmd(message):
‎    user_id = message.from_user.id
‎    USER_STATES[user_id] = None
‎    clear_user_session_messages(message.chat.id, user_id)
‎    if user_id in USER_DATA: del USER_DATA[user_id]
‎    
‎    str_user_id = str(user_id)
‎    if str_user_id not in BOT_DATA["balances"]: BOT_DATA["balances"][str_user_id] = 0.0
‎    if str_user_id not in BOT_DATA["pending_counts"]: BOT_DATA["pending_counts"][str_user_id] = 0
‎    if str_user_id not in BOT_DATA["pending_links"]: BOT_DATA["pending_links"][str_user_id] = []
‎    if str_user_id not in BOT_DATA["approved_counts"]: BOT_DATA["approved_counts"][str_user_id] = 0
‎    if str_user_id not in BOT_DATA["rejected_counts"]: BOT_DATA["rejected_counts"][str_user_id] = 0
‎    if str_user_id not in BOT_DATA["refer_counts"]: BOT_DATA["refer_counts"][str_user_id] = 0
‎    
‎    args = message.text.split()
‎    if len(args) > 1:
‎        referrer_id = args[1]
‎        if str_user_id not in BOT_DATA["referred_by"] and referrer_id != str_user_id and referrer_id in BOT_DATA["balances"]:
‎            BOT_DATA["referred_by"][str_user_id] = referrer_id
‎            
‎    save_data(BOT_DATA)
‎    
‎    if check_joined(user_id):
‎        send_user_main_menu(message.chat.id)
‎        if user_id == ADMIN_ID:
‎            bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} <b>এডমিন কন্ট্রোল প্যানেল:</b>", reply_markup=get_admin_inline_keyboard(), parse_mode="HTML")
‎    else:
‎        markup = types.InlineKeyboardMarkup()
‎        # 🔗 নতুন জয়েন চ্যানেল লিংক আপডেট করা হয়েছে
‎        markup.add(types.InlineKeyboardButton('🔗 জয়েন চ্যানেল', url="https://t.me/facebook_account_sell_bot_group"))
‎        markup.add(types.InlineKeyboardButton('✅ জয়েন কমপ্লিট ✅', callback_data='check_joined_btn'))
‎        
‎        join_msg = (
‎            f"{EMOJI_LOCK} <b>ইউজার ভেরিফিকেশন রিকোয়ার্ড!</b>\n"
‎            f"{DIVIDER_LINE}\n"
‎            f"বটটি ব্যবহার করতে প্রথমে আমাদের অফিশিয়াল চ্যানেলে জয়েন করুন: {CHANNEL_USERNAME}\n\n"
‎            f"তারপর নিচে থাকা <b>'✅ জয়েন কমপ্লিট ✅'</b> বাটনে চাপ দিন।"
‎        )
‎        bot.send_message(message.chat.id, join_msg, reply_markup=markup, parse_mode="HTML")
‎
‎# 📋 এডমিন কমান্ড ১: পেন্ডিং কাজের লিস্ট দেখা
‎def process_view_pending(chat_id, platform_type):
‎    msg = f"{EMOJI_CRYSTAL} <b>পেন্ডিং কাজের তালিকা ({platform_type}):</b>\n{DIVIDER_LINE}\n"
‎    has_pending = False
‎    for uid, links in BOT_DATA.get("pending_links", {}).items():
‎        platform_count = sum(1 for link in links if f"Type: {platform_type}" in link)
‎        if platform_count > 0:
‎            msg += f"{EMOJI_USERS} আইডি: <code>{uid}</code> ➡️ পেন্ডিং কাজ: <b>{platform_count}টি</b>\n"
‎            has_pending = True
‎    if not has_pending: msg += f"{EMOJI_LOCK} এই প্ল্যাটফর্মে কোনো পেন্ডিং কাজ নেই।"
‎    msg += f"\n\n{EMOJI_FIRE} <i>লিংক দেখতে:</i> <code>/check [আইডি]</code>\n{EMOJI_CALENDAR} <i>এপ্রুভ করতে:</i> <code>/approve [আইডি] [টাকা] [কয়টি]</code>"
‎    bot.send_message(chat_id, msg, parse_mode="HTML")
‎
‎# 🔎 এডমিন কমান্ড ৪: এক ক্লিকে পুরো লিস্ট একসাথে কপি করার সিস্টেম
‎def process_check_user_links(chat_id, target_id, platform_type):
‎    links = BOT_DATA.get("pending_links", {}).get(str(target_id), [])
‎    filtered_links = [link for link in links if f"Type: {platform_type}" in link]
‎    if not filtered_links:
‎        bot.send_message(chat_id, f"{EMOJI_LOCK} ইউজার <code>{target_id}</code> এর কোনো পেন্ডিং <b>{platform_type}</b> কাজ পাওয়া যায়নি।", parse_mode="HTML")
‎        return
‎    raw_list = ""
‎    for link in filtered_links:
‎        if platform_type == "INSTA":
‎            try: raw_list += f"{link.split('Uname: ')[1].split(' |')[0]}\n"
‎            except Exception: raw_list += f"{link}\n"
‎        else:
‎            try: raw_list += f"{link.split('UID: ')[1].split(' |')[0]}\n"
‎            except Exception: raw_list += f"{link}\n"
‎    msg = f"{EMOJI_CRYSTAL} <b>ইউজার {target_id} এর সকল {'ইউজারনেম' if platform_type == 'INSTA' else 'ইউআইডি'}:</b>\n👇 (কপি করতে চাপুন)\n\n<code>{raw_list.strip()}</code>"
‎    bot.send_message(chat_id, msg, parse_mode="HTML")
‎
‎@bot.message_handler(commands=['check'])
‎def check_user_links_cmd(message):
‎    if message.from_user.id != ADMIN_ID: return
‎    args = message.text.split()[1:]
‎    if not args:
‎        USER_STATES[message.from_user.id] = 'WAITING_FOR_CHECK_ID'
‎        bot.send_message(message.chat.id, f"{EMOJI_FIRE} যে ইউজারের লিংক দেখতে চান তার টেলিগ্রাম আইডি-টি পাঠান:", parse_mode="HTML")
‎        return
‎    USER_DATA[message.from_user.id] = {'check_target_id': args[0]}
‎    markup = types.InlineKeyboardMarkup(row_width=2)
‎    markup.add(types.InlineKeyboardButton('🟣 Instagram Data', callback_data='check_platform_INSTA'), types.InlineKeyboardButton('🔵 Facebook Data', callback_data='check_platform_FB'))
‎    bot.send_message(message.chat.id, f"🔮 ইউজার <code>{args[0]}</code> এর কোন প্ল্যাটফর্মের ডাটা দেখতে চান?", reply_markup=markup, parse_mode="HTML")
‎
‎# ✅ এডমিন কমান্ড ২: কাজ এপ্রুভ করা 
‎@bot.message_handler(commands=['approve'])
‎def approve_work(message):
‎    if message.from_user.id != ADMIN_ID: return
‎    try:
‎        args = message.text.split()[1:]
‎        target_id, amount = args[0], float(args[1])
‎        count_to_approve = int(args[2]) if len(args) > 2 else None
‎        str_target_id = str(target_id)
‎        
‎        if str_target_id in BOT_DATA["pending_counts"] and BOT_DATA["pending_counts"][str_target_id] > 0:
‎            total_pending = BOT_DATA["pending_counts"][str_target_id]
‎            if count_to_approve is None or count_to_approve >= total_pending: count_to_approve = total_pending
‎            if str_target_id in BOT_DATA["pending_links"]: BOT_DATA["pending_links"][str_target_id] = BOT_DATA["pending_links"][str_target_id][count_to_approve:]
‎            
‎            BOT_DATA["pending_counts"][str_target_id] -= count_to_approve
‎            BOT_DATA["balances"][str_target_id] = BOT_DATA["balances"].get(str_target_id, 0.0) + amount
‎            BOT_DATA["approved_counts"][str_target_id] = BOT_DATA["approved_counts"].get(str_target_id, 0) + count_to_approve
‎            
‎            referrer_id = BOT_DATA.get("referred_by", {}).get(str_target_id)
‎            if referrer_id and str(referrer_id) in BOT_DATA["balances"]:
‎                commission_added = amount * get_cfg('REFER_COMMISSION_PERCENT')
‎                BOT_DATA["balances"][str(referrer_id)] += commission_added
‎                try: bot.send_message(int(referrer_id), f"{EMOJI_CRYSTAL} <b>রেফারেল কমিশন আপডেট!</b>\n\n💰 ব্যালেন্সে লাইফটাইম কমিশন <b>{commission_added:.2f} BDT</b> যোগ করা হয়েছে!", parse_mode="HTML")
‎                except Exception: pass
‎            
‎            save_data(BOT_DATA)
‎            bot.send_message(message.chat.id, f"{EMOJI_CRYSTAL} ইউজার <code>{target_id}</code> এর {count_to_approve}টি কাজ এপ্রুভ হয়েছে।", parse_mode="HTML")
‎            try: bot.send_message(int(target_id), f"{EMOJI_CRYSTAL} <b>কাজের পেমেন্ট নোটিফিকেশন!</b>\n\n📥 আপনার জমা দেওয়া <b>{count_to_approve}</b>টি কাজ সফলভাবে এপ্রুভ করে ব্যালেন্সে <b>{amount} BDT</b> যোগ করা হয়েছে!", parse_mode="HTML")
‎            except Exception: pass
‎        else: bot.send_message(message.chat.id, f"{EMOJI_LOCK} এই ইউজারের কোনো পেন্ডিং কাজ নেই!", parse_mode="HTML")
‎    except Exception: bot.send_message(message.chat.id, f"{EMOJI_LOCK} ভুল ফরম্যাট! <code>/approve ইউজার_আইডি টাকা কয়টি</code>", parse_mode="HTML")
‎
‎# ❌ এডমিন কমান্ড ৫: কাজ রিজেক্ট করা
‎@bot.message_handler(commands=['reject'])
‎def reject_work(message):
‎    if message.from_user.id != ADMIN_ID: return
‎    try:
‎        args = message.text.split()[1:]
‎        target_id, count_to_reject = args[0], int(args[1])
‎        reason = " ".join(args[2:]) if len(args) > 2 else "নিয়ম মানা হয়নি"
‎        str_target_id = str(target_id)
‎        
‎        if str_target_id in BOT_DATA["pending_c