import os
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# 🔐 Настройки
TOKEN = os.getenv("TELEGRAM_TOKEN")
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(aid.strip()) for aid in admin_ids_str.split(',') if aid.strip().isdigit()]

if not TOKEN:
    print("Error: TELEGRAM_TOKEN environment variable is not set.")
    exit(1)

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
        [InlineKeyboardButton("🔗 Ссылка на наш канал", callback_data="channel")]
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
        return
    if len(context.args) != 2:
        await update.message.reply_text("❗ Используй: /setratebuy PLN 3.25")
        return
    currency, value_str = context.args
    try:
        value = float(value_str)
        rates["buy"][currency.upper()] = value
        await update.message.reply_text(f"✅ Курс покупки {currency.upper()} обновлён: {value}")
    except ValueError:
        await update.message.reply_text("❌ Ошибка формата. Значение должно быть числом.")
    except KeyError:
        await update.message.reply_text(f"❌ Неизвестная валюта: {currency.upper()}. Доступные: {', '.join(rates['buy'].keys())}")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла непредвиденная ошибка: {e}")

# 🔧 Команда /setratesell PLN 3.97
async def set_rate_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /setratesell command to set sell rates (admin only).
    Usage: /setratesell <CURRENCY> <VALUE>
    """
    if update.effective_user.id not in ADMIN_IDS:
        return
    if len(context.args) != 2:
        await update.message.reply_text("❗ Используй: /setratesell PLN 3.97")
        return
    currency, value_str = context.args
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
    await query.answer()
    user_id = query.from_user.id
    action = query.data

    # Define a reusable 'back' keyboard
    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]])
    
    # --- LOGIC FOR "back_to_start" BUTTON ---
    if action == "back_to_start":
        main_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Купить USDT", callback_data="buy")],
            [InlineKeyboardButton("💸 Продать USDT", callback_data="sell")],
            [InlineKeyboardButton("🔗 Ссылка на наш канал", callback_data="channel")]
        ])
        await query.edit_message_text("🚀 Добро пожаловать! Выберите действие:", reply_markup=main_keyboard)
        return

    # --- LOGIC FOR "channel" BUTTON ---
    if action == "channel":
        await query.edit_message_text(
            "🔗 Ссылка на наш канал\n\nhttps://t.me/polusdtchannel",
            reply_markup=back_keyboard
        )
        return

    # --- LOGIC FOR "buy" AND "sell" BUTTONS ---
    # We now store the message_id to be able to delete it later
    user_state[user_id] = {'action': action, 'message_id': query.message.message_id}

    rate_info = rates.get(action)
    if not rate_info:
        await query.edit_message_text("❌ Произошла ошибка при получении курсов.", reply_markup=back_keyboard)
        return

    text = f"🚀 Вы выбрали {'покупку' if action == 'buy' else 'продажу'} USDT\n\n"
    text += "📈 Курсы:\n"
    if action == "buy":
        for currency, value in rate_info.items():
            text += f"1 USDT = {value} {currency}\n"
    else:
        for currency, value in rate_info.items():
            text += f"{value} {currency} = 1 USDT\n"

    text += "\n🌍 Введите ваш город:"
    await query.edit_message_text(text, reply_markup=back_keyboard)

# 🏙 Обработка ввода города
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user input for city after selecting buy/sell action."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name or f"id: {user_id}"
    city = update.message.text.strip()

    if user_id not in user_state or 'action' not in user_state[user_id]:
        # If user starts with text, send them back to start
        main_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Купить USDT", callback_data="buy")],
            [InlineKeyboardButton("💸 Продать USDT", callback_data="sell")],
            [InlineKeyboardButton("🔗 Ссылка на наш канал", callback_data="channel")]
        ])
        await update.message.reply_text("Сначала выберите действие через /start.", reply_markup=main_keyboard)
        return

    # --- NEW: Delete the previous message with the keyboard ---
    message_to_delete_id = user_state[user_id].get('message_id')
    if message_to_delete_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=message_to_delete_id)
        except Exception as e:
            # Handle cases where the message is already deleted or not found
            print(f"Failed to delete message {message_to_delete_id} for user {user_id}: {e}")

    action = user_state[user_id]['action']
    action_text = "КУПИТЬ 🟢" if action == "buy" else "ПРОДАТЬ 🔴"
    del user_state[user_id]

    await update.message.reply_text("✅ Спасибо! Мы скоро свяжемся с вами.")

    if not ADMIN_IDS:
        print("Error: No ADMIN_IDS configured to send notifications.")
        return

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))

    print("✅ Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()