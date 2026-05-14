import telebot
import requests
import re
import os
from telebot import types, apihelper
from flask import Flask
from threading import Thread

# --- 0. FLASK SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 1. TIMEOUT SETTINGS ---
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

# --- 2. CONFIGURATION ---
API_TOKEN = '8657098039:AAE4qoR5ayJCawBAnsM726bVn8cZO2WXu-0'
CHANNELS = ['@CODEX_habesha', '@officialcoders'] 
BOT_OWNER_ID = 8700421304 
BOT_OWNER_USERNAME = "@Tiktokantiwatermarkbot"
TIKTOK_API = "https://www.tikwm.com/api/"

bot = telebot.TeleBot(API_TOKEN)
URL_PATTERN = r'(https?://[^\s]+)'

# --- 3. DATABASE LOGIC ---
def add_user(user_id):
    if not os.path.exists('users.txt'):
        with open('users.txt', 'w') as f: f.write(str(user_id) + '\n')
    else:
        with open('users.txt', 'r') as f:
            users = f.read().splitlines()
        if str(user_id) not in users:
            with open('users.txt', 'a') as f:
                f.write(str(user_id) + '\n')

def get_users_count():
    if not os.path.exists('users.txt'): return 0
    with open('users.txt', 'r') as f:
        return len(f.read().splitlines())

# --- 4. HELPERS ---
def is_user_member(user_id):
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status in ['left', 'kicked']: return False
        except: return False
    return True

def get_join_keyboard():
    markup = types.InlineKeyboardMarkup()
    for channel in CHANNELS:
        markup.add(types.InlineKeyboardButton(text="✨ Join Our Channel", url=f"https://t.me/{channel.replace('@', '')}"))
    markup.add(types.InlineKeyboardButton(text="✅ Verify Membership", callback_data="check_join"))
    return markup

# --- 5. HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.chat.id)
    if not is_user_member(message.from_user.id):
        welcome_text = "👋 <b>Welcome!</b>\n\nPlease join our channels to use the bot."
        bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=get_join_keyboard())
    else:
        bot.send_message(message.chat.id, "🚀 <b>Ready!</b> Send me a TikTok link.", parse_mode='HTML')

@bot.message_handler(commands=['status'])
def status(message):
    if message.from_user.id == BOT_OWNER_ID:
        count = get_users_count()
        bot.reply_to(message, f"📊 Total Users: <code>{count}</code>", parse_mode='HTML')

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == BOT_OWNER_ID:
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Reply to a post with /broadcast")
            return
        
        reply_msg = message.reply_to_message
        if not os.path.exists('users.txt'): return
        
        with open('users.txt', 'r') as f:
            users = f.read().splitlines()
        
        bot.send_message(message.chat.id, f"📡 Broadcasting to {len(users)} users...")
        for user in users:
            try: bot.copy_message(user, message.chat.id, reply_msg.message_id)
            except: pass
        bot.send_message(message.chat.id, "✅ Broadcast Finished!")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if is_user_member(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.edit_message_text("🚀 <b>Ready!</b> Send a link.", call.message.chat.id, call.message.message_id, parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "❌ Not joined yet!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_tiktok(message):
    add_user(message.chat.id)
    if not is_user_member(message.from_user.id):
        bot.reply_to(message, "⚠️ Join our channels first!", reply_markup=get_join_keyboard())
        return

    found_urls = re.findall(URL_PATTERN, message.text)
    if not found_urls or "tiktok.com" not in found_urls[0]: return
    
    status_msg = bot.reply_to(message, "🫣", parse_mode='HTML')
    
    try:
        response = requests.post(TIKTOK_API, data={'url': found_urls[0]}, timeout=30).json()
        if response.get('code') == 0:
            data = response['data']
            caption = (
                f"💎 <b>𝐓𝐈𝐊 𝐓𝐎𝐊 📥 𝗛𝗗 ᵖˡᵘ𝓼</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <b>Video ID:</b> <code>{data.get('id')}</code>\n"
                f"📝 <b>Title:</b> {data.get('title', 'No Title')}\n\n"
                f"👤 <b>Author:</b> {data.get('author', {}).get('nickname')}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✨ <b>By:</b> {BOT_OWNER_USERNAME}"
            )
            bot.send_video(message.chat.id, data['play'], caption=caption, parse_mode='HTML')
            bot.delete_message(message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ Video not found.", message.chat.id, status_msg.message_id)
    except Exception:
        bot.edit_message_text("⚠️ System Error!", message.chat.id, status_msg.message_id)

# --- 6. START BOT ---
if __name__ == '__main__':
    print("💎 Bot is Online with Flask!")
    keep_alive() # Render እንዳይዘጋው ሰርቨሩን ያስነሳል
    try:
        bot.remove_webhook()
    except:
        pass
    bot.infinity_polling(skip_pending=True)
