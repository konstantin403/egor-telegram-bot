import os
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# 🔐 Settings
TOKEN = os.getenv("TELEGRAM_TOKEN")
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(aid.strip()) for aid in admin_ids_str.split(',') if aid.strip().isdigit()]

if not TOKEN:
    print("Error: TELEGRAM_TOKEN environment variable is not set.")
    exit(1)

if not ADMIN_IDS:
    print("Warning: ADMIN_IDS environment variable is not set or invalid. Admin features will be disabled.")

# 💾 Temporary storage
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

# 📚 Translations Dictionary
translations = {
    'ru': {
        'welcome_choose_action': "🚀 Добро пожаловать! Выберите действие:",
        'buy_usdt': "💰 Купить USDT",
        'sell_usdt': "💸 Продать USDT",
        'link_to_channel': "🔗 Ссылка на наш канал",
        'current_rates_title': "💱 <b>Актуальные курсы USDT</b>:\n\n",
        'buy_section': "🟢 <b>Покупка:</b>\n",
        'sell_section': "🔴 <b>Продажа:</b>\n",
        'usage_setratebuy': "❗ Используй: /setratebuy PLN 3.25",
        'buy_rate_updated': "✅ Курс покупки {currency} обновлён: {value}",
        'format_error_number': "❌ Ошибка формата. Значение должно быть числом.",
        'unknown_currency': "❌ Неизвестная валюта: {currency}. Доступные: {available_currencies}",
        'unexpected_error': "❌ Произошла непредвиденная ошибка: {error}",
        'usage_setratesell': "❗ Используй: /setratesell PLN 3.97",
        'sell_rate_updated': "✅ Курс продажи {currency} обновлён: {value}",
        'back': "⬅️ Назад",
        'channel_link_message': "🔗 Ссылка на наш канал\n\nhttps://t.me/polusdtchannel",
        'selected_action': "🚀 Вы выбрали {action_text} USDT\n\n",
        'rates_section': "📈 Курсы:\n",
        'enter_city': "🌍 Введите ваш город:",
        'error_retrieving_rates': "❌ Произошла ошибка при получении курсов.",
        'select_action_first': "Сначала выберите действие через /start.",
        'thank_you_contact_soon': "✅ Спасибо! Мы скоро свяжемся с вами.",
        'new_request_admin': "🔔 <b>Новый запрос</b>\n\n👤 Пользователь: @{username}\n🎯 Действие: {action_text}\n🌍 Город: {city}",
        'buy_action_text': "КУПИТЬ 🟢",
        'sell_action_text': "ПРОДАТЬ 🔴",
        'choose_language': "🌐 Please choose your language:",
        'bot_started': "✅ Бот запущен.",
        'language_set': "Язык установлен на {lang_name}.",
        'admin_notification_error': "Error: No ADMIN_IDS configured to send notifications.",
        'error_sending_admin_message': "Error sending message to admin_id {admin_id}: {error}",
    },
    'en': {
        'welcome_choose_action': "🚀 Welcome! Please choose an action:",
        'buy_usdt': "💰 Buy USDT",
        'sell_usdt': "💸 Sell USDT",
        'link_to_channel': "🔗 Link to our channel",
        'current_rates_title': "💱 <b>Current USDT rates</b>:\n\n",
        'buy_section': "🟢 <b>Buy:</b>\n",
        'sell_section': "🔴 <b>Sell:</b>\n",
        'usage_setratebuy': "❗ Usage: /setratebuy PLN 3.25",
        'buy_rate_updated': "✅ Buy rate for {currency} updated: {value}",
        'format_error_number': "❌ Format error. Value must be a number.",
        'unknown_currency': "❌ Unknown currency: {currency}. Available: {available_currencies}",
        'unexpected_error': "❌ Unexpected error occurred: {error}",
        'usage_setratesell': "❗ Usage: /setratesell PLN 3.97",
        'sell_rate_updated': "✅ Sell rate for {currency} updated: {value}",
        'back': "⬅️ Back",
        'channel_link_message': "🔗 Link to our channel\n\nhttps://t.me/polusdtchannel",
        'selected_action': "🚀 You selected {action_text} USDT\n\n",
        'rates_section': "📈 Rates:\n",
        'enter_city': "🌍 Enter your city:",
        'error_retrieving_rates': "❌ An error occurred while retrieving the rates.",
        'select_action_first': "Please start by selecting an action using /start.",
        'thank_you_contact_soon': "✅ Thank you! We will contact you soon.",
        'new_request_admin': "🔔 <b>New request</b>\n\n👤 User: @{username}\n🎯 Action: {action_text}\n🌍 City: {city}",
        'buy_action_text': "BUY 🟢",
        'sell_action_text': "SELL 🔴",
        'choose_language': "🌐 Please choose your language:",
        'bot_started': "✅ Bot started.",
        'language_set': "Language set to {lang_name}.",
        'admin_notification_error': "Error: No ADMIN_IDS configured to send notifications.",
        'error_sending_admin_message': "Error sending message to admin_id {admin_id}: {error}",
    },
    'pl': {
        'welcome_choose_action': "🚀 Witaj! Wybierz akcję:",
        'buy_usdt': "💰 Kup USDT",
        'sell_usdt': "💸 Sprzedaj USDT",
        'link_to_channel': "🔗 Link do naszego kanału",
        'current_rates_title': "💱 <b>Aktualne kursy USDT</b>:\n\n",
        'buy_section': "🟢 <b>Kupno:</b>\n",
        'sell_section': "🔴 <b>Sprzedaż:</b>\n",
        'usage_setratebuy': "❗ Użyj: /setratebuy PLN 3.25",
        'buy_rate_updated': "✅ Kurs kupna {currency} zaktualizowany: {value}",
        'format_error_number': "❌ Błąd formatu. Wartość musi być liczbą.",
        'unknown_currency': "❌ Nieznana waluta: {currency}. Dostępne: {available_currencies}",
        'unexpected_error': "❌ Wystąpił nieoczekiwany błąd: {error}",
        'usage_setratesell': "❗ Użyj: /setratesell PLN 3.97",
        'sell_rate_updated': "✅ Kurs sprzedaży {currency} zaktualizowany: {value}",
        'back': "⬅️ Wróć",
        'channel_link_message': "🔗 Link do naszego kanału\n\nhttps://t.me/polusdtchannel",
        'selected_action': "🚀 Wybrałeś {action_text} USDT\n\n",
        'rates_section': "📈 Kursy:\n",
        'enter_city': "🌍 Wpisz swoje miasto:",
        'error_retrieving_rates': "❌ Wystąpił błąd podczas pobierania kursów.",
        'select_action_first': "Najpierw wybierz akcję za pomocą /start.",
        'thank_you_contact_soon': "✅ Dziękujemy! Skontaktujemy się wkrótce.",
        'new_request_admin': "🔔 <b>Nowe zapytanie</b>\n\n👤 Użytkownik: @{username}\n🎯 Akcja: {action_text}\n🌍 Miasto: {city}",
        'buy_action_text': "KUP 🟢",
        'sell_action_text': "SPRZEDAJ 🔴",
        'choose_language': "🌐 Proszę wybrać język:",
        'bot_started': "✅ Bot uruchomiony.",
        'language_set': "Język ustawiony na {lang_name}.",
        'admin_notification_error': "Błąd: Brak skonfigurowanych ADMIN_IDS do wysyłania powiadomień.",
        'error_sending_admin_message': "Błąd podczas wysyłania wiadomości do admin_id {admin_id}: {error}",
    }
}

# Helper function to get translated text
def get_text(user_id: int, key: str, **kwargs) -> str:
    """Retrieves translated text for a given key and user's language."""
    user_lang = user_state.get(user_id, {}).get('lang', 'en') # Default to English if not set
    # Fallback to English if translation for specific key is missing in chosen language
    text = translations.get(user_lang, {}).get(key, translations['en'].get(key, f"Missing translation for {key}"))
    return text.format(**kwargs)

# 📱 Initial /start Command or Language Selection
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command.
    If no language is set, prompts for language selection.
    Otherwise, displays the main action menu in the user's selected language.
    """
    user_id = update.effective_user.id
    if user_id not in user_state or 'lang' not in user_state[user_id]:
        # Prompt for language selection
        keyboard = [
            [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
            [InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton("Polski 🇵🇱", callback_data="lang_pl")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(get_text(user_id, 'choose_language'), reply_markup=reply_markup)
    else:
        # User already has a language, show main menu
        await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the main action menu to the user."""
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'buy_usdt'), callback_data="buy")],
        [InlineKeyboardButton(get_text(user_id, 'sell_usdt'), callback_data="sell")],
        [InlineKeyboardButton(get_text(user_id, 'link_to_channel'), callback_data="channel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Use reply_text for initial menu, edit_message_text if coming from a callback
    if update.callback_query:
        await update.callback_query.edit_message_text(get_text(user_id, 'welcome_choose_action'), reply_markup=reply_markup)
    else:
        await update.message.reply_text(get_text(user_id, 'welcome_choose_action'), reply_markup=reply_markup)


# 📊 Command /rate — shows current rates
async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /rate command, displaying current buy and sell rates."""
    user_id = update.effective_user.id
    text = get_text(user_id, 'current_rates_title')

    text += get_text(user_id, 'buy_section')
    for currency, value in rates["buy"].items():
        text += f"1 USDT = {value} {currency}\n"

    text += "\n" + get_text(user_id, 'sell_section')
    for currency, value in rates["sell"].items():
        text += f"{value} {currency} = 1 USDT\n"

    await update.message.reply_text(text, parse_mode='HTML')

# 🔧 Command /setratebuy PLN 3.25
async def set_rate_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /setratebuy command to set buy rates (admin only).
    Usage: /setratebuy <CURRENCY> <VALUE>
    """
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if len(context.args) != 2:
        await update.message.reply_text(get_text(user_id, 'usage_setratebuy'))
        return

    currency, value_str = context.args
    try:
        value = float(value_str)
        rates["buy"][currency.upper()] = value
        await update.message.reply_text(get_text(user_id, 'buy_rate_updated', currency=currency.upper(), value=value))
    except ValueError:
        await update.message.reply_text(get_text(user_id, 'format_error_number'))
    except KeyError:
        await update.message.reply_text(get_text(user_id, 'unknown_currency', currency=currency.upper(), available_currencies=', '.join(rates['buy'].keys())))
    except Exception as e:
        await update.message.reply_text(get_text(user_id, 'unexpected_error', error=e))

# 🔧 Command /setratesell PLN 3.97
async def set_rate_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /setratesell command to set sell rates (admin only).
    Usage: /setratesell <CURRENCY> <VALUE>
    """
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if len(context.args) != 2:
        await update.message.reply_text(get_text(user_id, 'usage_setratesell'))
        return

    currency, value_str = context.args
    try:
        value = float(value_str)
        rates["sell"][currency.upper()] = value
        await update.message.reply_text(get_text(user_id, 'sell_rate_updated', currency=currency.upper(), value=value))
    except ValueError:
        await update.message.reply_text(get_text(user_id, 'format_error_number'))
    except KeyError:
        await update.message.reply_text(get_text(user_id, 'unknown_currency', currency=currency.upper(), available_currencies=', '.join(rates['sell'].keys())))
    except Exception as e:
        await update.message.reply_text(get_text(user_id, 'unexpected_error', error=e))

# 🤖 Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles callback queries from inline keyboard buttons."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data

    # --- Language Selection Handling ---
    if action.startswith('lang_'):
        lang_code = action.split('_')[1]
        user_state[user_id] = {'lang': lang_code}
        lang_name_map = {'en': 'English', 'ru': 'Русский', 'pl': 'Polski'} # For confirmation message
        await query.edit_message_text(get_text(user_id, 'language_set', lang_name=lang_name_map.get(lang_code, lang_code)))
        await show_main_menu(update, context) # Show main menu after language selection
        return

    # Define a reusable 'back' keyboard
    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(get_text(user_id, 'back'), callback_data="back_to_start")]])
    
    # --- LOGIC FOR "back_to_start" BUTTON ---
    if action == "back_to_start":
        await show_main_menu(update, context)
        return

    # --- LOGIC FOR "channel" BUTTON ---
    if action == "channel":
        await query.edit_message_text(
            get_text(user_id, 'channel_link_message'),
            reply_markup=back_keyboard
        )
        return

    # --- LOGIC FOR "buy" AND "sell" BUTTONS ---
    user_state[user_id] = {'action': action, 'message_id': query.message.message_id, 'lang': user_state.get(user_id, {}).get('lang', 'en')} # Preserve language
    
    rate_info = rates.get(action)
    if not rate_info:
        await query.edit_message_text(get_text(user_id, 'error_retrieving_rates'), reply_markup=back_keyboard)
        return

    action_text_translated = get_text(user_id, 'buy_action_text') if action == 'buy' else get_text(user_id, 'sell_action_text')
    text = get_text(user_id, 'selected_action', action_text=action_text_translated)
    text += get_text(user_id, 'rates_section')
    if action == "buy":
        for currency, value in rate_info.items():
            text += f"1 USDT = {value} {currency}\n"
    else: # action == "sell"
        for currency, value in rate_info.items():
            text += f"{value} {currency} = 1 USDT\n"

    text += "\n" + get_text(user_id, 'enter_city')
    await query.edit_message_text(text, reply_markup=back_keyboard)

# 🏙 City input handler
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user input for city after selecting buy/sell action."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.full_name or f"id: {user_id}"
    city = update.message.text.strip()

    # Retrieve user's language for messages
    user_lang = user_state.get(user_id, {}).get('lang', 'en')

    if user_id not in user_state or 'action' not in user_state[user_id]:
        # If user starts with text without selecting action, send them back to start
        # and prompt for language if not set
        if 'lang' not in user_state.get(user_id, {}):
            await start(update, context) # This will prompt for language
        else:
            main_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, 'buy_usdt'), callback_data="buy")],
                [InlineKeyboardButton(get_text(user_id, 'sell_usdt'), callback_data="sell")],
                [InlineKeyboardButton(get_text(user_id, 'link_to_channel'), callback_data="channel")]
            ])
            await update.message.reply_text(get_text(user_id, 'select_action_first'), reply_markup=main_keyboard)
        return

    # Delete the previous message with the keyboard
    message_to_delete_id = user_state[user_id].get('message_id')
    if message_to_delete_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=message_to_delete_id)
        except Exception as e:
            print(f"Failed to delete message {message_to_delete_id} for user {user_id}: {e}")

    action = user_state[user_id]['action']
    action_text_translated = get_text(user_id, 'buy_action_text') if action == 'buy' else get_text(user_id, 'sell_action_text')
    del user_state[user_id] # Clear state after processing

    await update.message.reply_text(get_text(user_id, 'thank_you_contact_soon'))

    if not ADMIN_IDS:
        print(get_text(user_id, 'admin_notification_error'))
        return

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=get_text(user_id, 'new_request_admin', username=username, action_text=action_text_translated, city=city),
                parse_mode='HTML'
            )
        except Exception as e:
            print(get_text(user_id, 'error_sending_admin_message', admin_id=admin_id, error=e))

# 🚀 Bot launch
def main():
    """Main function to set up and run the Telegram bot."""
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rate", rate))
    app.add_handler(CommandHandler("setratebuy", set_rate_buy))
    app.add_handler(CommandHandler("setratesell", set_rate_sell))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))

    print(get_text(0, 'bot_started')) # Use a dummy user_id 0 for global messages like bot start

    app.run_polling()

if __name__ == "__main__":
    main()