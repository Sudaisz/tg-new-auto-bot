import json
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile

API_TOKEN = '8138646021:AAEV8mZ-MFtpVgEN-_pFrRUAS4Qxt4fcCsQ'
ADMIN_ID =  6619154186 # Change to your Telegram ID
REQUIRED_CHANNELS = ['@beyondtech_v2', '@suxedo_ban', '@kelvintechnologies', '@beyondnew']
USERS_FILE = 'users.json'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

async def check_and_register_user(user_id):
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": None,
            "password": None,
            "stars": 0,
            "referrals": [],
            "premium_until": None,
            "referral_timestamps": [],
        }
        save_users(users)

def is_premium(user_id):
    users = load_users()
    user = users.get(str(user_id))
    if user and user['premium_until']:
        return datetime.strptime(user['premium_until'], "%Y-%m-%d") >= datetime.now()
    return False

def activate_premium(user_id):
    users = load_users()
    until = datetime.now() + timedelta(days=15)
    users[str(user_id)]["premium_until"] = until.strftime("%Y-%m-%d")
    save_users(users)

def deduct_stars(user_id, amount):
    users = load_users()
    if users[str(user_id)]['stars'] >= amount:
        users[str(user_id)]['stars'] -= amount
        save_users(users)
        return True
    return False

def star_payment_keyboard(action, amount):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(f"Pay {amount} ⭐", callback_data=f"pay:{action}:{amount}"))
    return kb

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    anime_photo = InputFile('anime.jpg')  # File must exist
    await bot.send_photo(message.chat.id, anime_photo,
        caption=("👋 Welcome to the Ultimate Multi-Bot!\n"
                 "🔗 Join all 4 channels first, then use /register to continue."))

@dp.message_handler(commands=['register'])
async def register(message: types.Message):
    user_id = message.from_user.id
    await check_and_register_user(user_id)
    users = load_users()

    if users[str(user_id)]['username']:
        return await message.reply("✅ You're already registered.")

    await message.reply("Please send your desired username:")

    @dp.message_handler()
    async def receive_username(msg: types.Message):
        if msg.from_user.id != user_id:
            return
        users[str(user_id)]['username'] = msg.text
        save_users(users)
        await msg.reply("Now send your password:")

        @dp.message_handler()
        async def receive_password(pw_msg: types.Message):
            if pw_msg.from_user.id != user_id:
                return
            users[str(user_id)]['password'] = pw_msg.text
            save_users(users)
            await pw_msg.reply("✅ Registered successfully!")

        dp.register_message_handler(receive_password, content_types=types.ContentType.TEXT, state=None)

    dp.register_message_handler(receive_username, content_types=types.ContentType.TEXT, state=None)

@dp.message_handler(commands=['buy_premium'])
async def buy_premium(message: types.Message):
    user_id = str(message.from_user.id)
    if int(user_id) == ADMIN_ID:
        activate_premium(user_id)
        return await message.reply("👑 Premium activated (Admin bypass).")
    users = load_users()
    if users.get(user_id, {}).get("stars", 0) >= 1:
        await message.reply("Tap below to confirm premium purchase:",
                            reply_markup=star_payment_keyboard("premium", 1))
    else:
        await message.reply("❌ Not enough stars. Earn or buy stars.")

@dp.message_handler(commands=['get_report'])
async def get_report(message: types.Message):
    user_id = str(message.from_user.id)
    if int(user_id) == ADMIN_ID:
        return await message.reply("👑 Report generated (Admin bypass).")

    args = message.get_args()
    if not args:
        return await message.reply("Usage: /get_report <type>")

    users = load_users()
    if users[user_id]["stars"] >= 3:
        await message.reply("Tap below to pay for report:",
                            reply_markup=star_payment_keyboard("report", 3))
    elif len(users[user_id]["referrals"]) >= 5:
        users[user_id]["referrals"] = []
        save_users(users)
        await message.reply(f"📄 Report for '{args}' generated using referrals!")
    else:
        await message.reply("❌ Need 3⭐ or 5 referrals to get report.")

@dp.callback_query_handler(lambda c: c.data.startswith("pay:"))
async def handle_star_payment(callback: types.CallbackQuery):
    _, action, amount = callback.data.split(":")
    user_id = str(callback.from_user.id)
    amount = int(amount)

    if deduct_stars(user_id, amount):
        if action == "premium":
            activate_premium(user_id)
            await callback.message.edit_text("🎉 Premium activated for 15 days!")
        elif action == "report":
            await callback.message.edit_text("📄 Report sent!")
    else:
        await callback.message.edit_text("❌ Not enough stars.")

@dp.message_handler(commands=['play'])
async def play_menu(message: types.Message):
    await message.reply("🎮 Available games:\n• X and O\n• Snake\n• Rock Paper Scissors\n• 2048\n• /random battle")

@dp.message_handler(commands=['random'])
async def random_game(message: types.Message):
    user_id = str(message.from_user.id)
    users = load_users()

    opponent = None
    # Matchmaking simulation (extend this logic as needed)
    for uid in users:
        if uid != user_id and users[uid].get("waiting_random"):
            opponent = uid
            break

    if opponent:
        users[user_id]["waiting_random"] = False
        users[opponent]["waiting_random"] = False
        # Simulate random win
        winner = user_id if bool(datetime.now().second % 2) else opponent
        loser = opponent if winner == user_id else user_id

        users[winner]["stars"] += users[loser]["stars"]
        users[loser]["stars"] = 0
        users[winner]["referrals"].extend(users[loser]["referrals"])
        users[loser]["referrals"] = []

        save_users(users)
        await message.reply(f"🏆 {winner} won and stole all the stars/referrals from {loser}!")
    else:
        users[user_id]["waiting_random"] = True
        save_users(users)
        msg = await message.reply("⚠️ You’re about to stake ALL your coins/referrals.\nTap 'Cancel' below within 4s if unsure.",
                                  reply_markup=InlineKeyboardMarkup().add(
                                      InlineKeyboardButton("❌ Cancel", callback_data="cancel_random")
                                  ))
        await asyncio.sleep(4)
        if users[user_id].get("waiting_random"):
            await bot.send_message(message.chat.id, "🔍 Searching for an opponent...")
        else:
            await bot.send_message(message.chat.id, "❌ Game cancelled.")

@dp.callback_query_handler(lambda c: c.data == "cancel_random")
async def cancel_random(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    users = load_users()
    users[user_id]["waiting_random"] = False
    save_users(users)
    await callback.message.edit_text("❌ Random game cancelled.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
