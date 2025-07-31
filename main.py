import os
from dotenv import load_dotenv # Import load_dotenv for local development

# Load environment variables from .env file (for local development)
# On Railway, these variables are injected directly and this line is not strictly needed,
# but it's good practice for local testing.
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
# No explicit 'TelegramError' import in the original, but it's good to keep it if used elsewhere.
# from telegram.error import TelegramError

# 🔐 Настройки
# It's good practice to check if these variables are loaded correctly,
# especially for ADMIN_IDS which needs parsing.
TOKEN = os.getenv("TELEGRAM_TOKEN")
# ADMIN_IDS will be a string like "id1,id2,id3". We need to parse it into a list of integers.
# Provide a default empty string to prevent NoneType error if ADMIN_IDS is not set.
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(aid.strip()) for aid in admin_ids_str.split(',') if aid.strip().isdigit()]

# Basic check for essential variables
if not TOKEN:
    print("Error: TELEGRAM_TOKEN environment variable is not set.")
    exit(1) # Exit if essential token is missing

if not ADMIN_IDS:
    print("Warning: ADMIN_IDS environment variable is not set or invalid. Admin features will be disabled.")

# 💾 Временное хранилище
user_state = {}
rates = {
    "buy": {
        "PLN🇵🇱": 3.14,
        "USD🇺🇸": 0.84,
        "EUR🇪🇺": 0.74
    },
    "sell": {
        "PLN🇵🇱": 3.97,
        "USD🇺🇸": 1.06,
        "EUR🇪🇺": 0.93
    }
}

# 📱 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command, sending a welcome message and action buttons."""
    keyboard = [
        [InlineKeyboardButton("💰 Купить USDT", callback_data="buy")],
        [InlineKeyboardButton("💸 Продать USDT", callback_data="sell")],
        [InlineKeyboardButton("💸 Сылка на канал", callback_data="channel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🚀 Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

# 📊 Команда /rate — показывает текущие курсы
async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /rate command, displaying current buy and sell rates."""
    text = "💱 <b>Актуальные курсы USDT</b>:\n\n"

    text += "🟢 <b>Покупка:</b>\n"
    for currency, value in rates["buy"].items():
        text += f"1 USDT = {value} {currency}\n"

    text += "\n🔴 <b>Продажа:</b>\n"
    for currency, value in rates["sell"].items():
        text += f"{value} {currency} = 1 USDT\n"

    await update.message.reply_text(text, parse_mode='HTML')

# 🔧 Команда /setratebuy PLN 3.25
async def set_rate_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /setratebuy command to set buy rates (admin only).
    Usage: /setratebuy <CURRENCY> <VALUE>
    """
    if update.effective_user.id not in ADMIN_IDS:
        # Silently ignore if not admin, or send a private message to admin user
        # print(f"Unauthorized attempt to set_rate_buy by user ID: {update.effective_user.id}")
        return

    if len(context.args) != 2:
        await update.message.reply_text("❗ Используй: /setratebuy PLN 3.25")
        return

    currency, value_str = context.args # Renamed value to value_str to avoid conflict with float conversion
    try:
        value = float(value_str)
        rates["buy"][currency.upper()] = value
        await update.message.reply_text(f"✅ Курс покупки {currency.upper()} обновлён: {value}")
    except ValueError: # Catch specific ValueError for float conversion
        await update.message.reply_text("❌ Ошибка формата. Значение должно быть числом.")
    except KeyError: # Catch KeyError if currency is not in rates["buy"]
        await update.message.reply_text(f"❌ Неизвестная валюта: {currency.upper()}. Доступные: {', '.join(rates['buy'].keys())}")
    except Exception as e: # Catch any other unexpected errors
        await update.message.reply_text(f"❌ Произошла непредвиденная ошибка: {e}")

# 🔧 Команда /setratesell PLN 3.97
async def set_rate_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /setratesell command to set sell rates (admin only).
    Usage: /setratesell <CURRENCY> <VALUE>
    """
    if update.effective_user.id not in ADMIN_IDS:
        # Silently ignore if not admin
        return

    if len(context.args) != 2:
        await update.message.reply_text("❗ Используй: /setratesell PLN 3.97")
        return

    currency, value_str = context.args # Renamed value to value_str
    try:
        value = float(value_str)
        rates["sell"][currency.upper()] = value
        await update.message.reply_text(f"✅ Курс продажи {currency.upper()} обновлён: {value}")
    except ValueError:
        await update.message.reply_text("❌ Ошибка формата. Значение должно быть числом.")
    except KeyError:
        await update.message.reply_text(f"❌ Неизвестная валюта: {currency.upper()}. Доступные: {', '.join(rates['sell'].keys())}")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла непредвиденная ошибка: {e}")

# 🤖 Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles callback queries from inline keyboard buttons."""
    query = update.callback_query
    await query.answer() # Always answer the callback query
    user_id = query.from_user.id
    action = query.data # 'buy' or 'sell'
    user_state[user_id] = {'action': action}

    rate_info = rates.get(action) # Use .get() for safer access
    if not rate_info:
        await query.edit_message_text("❌ Произошла ошибка при получении курсов.")
        return

    if action == "channel"
        channel = f"Ссылка на наш канал\n\n" + "https://t.me/polusdtchannel"

        await query.edit_message_text(channel)
        return

    text = f"🚀 Вы выбрали {'покупку' if action == 'buy' else 'продажу'} USDT\n\n"

    text += "📈 Курсы:\n"
    if action == "buy":
        for currency, value in rate_info.items():
            text += f"1 USDT = {value} {currency}\n"
    else: # action == "sell"
        for currency, value in rate_info.items():
            text += f"{value} {currency} = 1 USDT\n"

    text += "\n🌍 Введите ваш город:"

    await query.edit_message_text(text)

# 🏙 Обработка ввода города
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user input for city after selecting buy/sell action."""
    user_id = update.message.from_user.id
    # Use full name if username is not available for better identification
    username = update.message.from_user.username or update.message.from_user.full_name or f"id: {user_id}"
    city = update.message.text.strip()

    if user_id not in user_state or 'action' not in user_state[user_id]:
        await update.message.reply_text("Сначала выберите действие через /start.")
        return

    action = user_state[user_id]['action']
    action_text = "КУПИТЬ 🟢" if action == "buy" else "ПРОДАТЬ 🔴"
    del user_state[user_id] # Clear state after processing

    await update.message.reply_text("✅ Спасибо! Мы скоро свяжемся с вами.")

    # Ensure ADMIN_IDS is a list of integers for iteration
    if not ADMIN_IDS:
        print("Error: No ADMIN_IDS configured to send notifications.")
        return # Cannot send message if no admin IDs are set

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🔔 <b>Новый запрос</b>\n\n"
                    f"👤 Пользователь: @{username}\n"
                    f"🎯 Действие: {action_text}\n"
                    f"🌍 Город: {city}",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Error sending message to admin_id {admin_id}: {e}")

# 🚀 Запуск бота
def main():
    """Main function to set up and run the Telegram bot."""
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rate", rate))
    app.add_handler(CommandHandler("setratebuy", set_rate_buy))
    app.add_handler(CommandHandler("setratesell", set_rate_sell))
    app.add_handler(CallbackQueryHandler(button_handler))
    # filters.TEXT & ~filters.COMMAND ensures it only processes plain text, not commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))

    print("✅ Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()