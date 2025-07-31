import os
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

from translations import translations

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

# Helper function to get translated text
def get_text(user_id: int, key: str, **kwargs) -> str:
    """Retrieves translated text for a given key and user's language."""
    user_lang = user_state.get(user_id, {}).get('lang', 'en') # Default to English if not set
    text = translations.get(user_lang, {}).get(key, translations['en'].get(key, f"Missing translation for {key}"))
    return text.format(**kwargs)

# Language names map for admin notifications
lang_name_map = {'en': 'English', 'ru': 'Русский', 'pl': 'Polski'}

async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the language selection menu."""
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
        [InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton("Polski 🇵🇱", callback_data="lang_pl")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Check if we're coming from a callback or a command
    if update.callback_query:
        await update.callback_query.edit_message_text(get_text(user_id, 'choose_language'), reply_markup=reply_markup)
    else:
        await update.message.reply_text(get_text(user_id, 'choose_language'), reply_markup=reply_markup)


# 📱 Initial /start Command or Language Selection
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command.
    If no language is set, prompts for language selection.
    Otherwise, displays the main action menu in the user's selected language.
    """
    user_id = update.effective_user.id
    if user_id not in user_state or 'lang' not in user_state[user_id]:
        await show_language_menu(update, context)
    else:
        await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the main action menu to the user."""
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'buy_usdt'), callback_data="buy")],
        [InlineKeyboardButton(get_text(user_id, 'sell_usdt'), callback_data="sell")],
        [InlineKeyboardButton(get_text(user_id, 'link_to_channel'), callback_data="channel")],
        [InlineKeyboardButton(get_text(user_id, 'switch_language_button'), callback_data="switch_language")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
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
        await query.edit_message_text(get_text(user_id, 'language_set', lang_name=lang_name_map.get(lang_code, lang_code)))
        await show_main_menu(update, context)
        return

    # --- NEW: Handle "Switch Language" button ---
    if action == "switch_language":
        await show_language_menu(update, context)
        return

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
    user_state[user_id] = {'action': action, 'message_id': query.message.message_id, 'lang': user_state.get(user_id, {}).get('lang', 'en')}
    
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
    else:
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

    user_data = user_state.get(user_id, {})
    user_lang_code = user_data.get('lang', 'en')
    user_lang_name = lang_name_map.get(user_lang_code, user_lang_code)

    if 'action' not in user_data:
        if 'lang' not in user_data:
            await start(update, context)
        else:
            main_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, 'buy_usdt'), callback_data="buy")],
                [InlineKeyboardButton(get_text(user_id, 'sell_usdt'), callback_data="sell")],
                [InlineKeyboardButton(get_text(user_id, 'link_to_channel'), callback_data="channel")],
                [InlineKeyboardButton(get_text(user_id, 'switch_language_button'), callback_data="switch_language")]
            ])
            await update.message.reply_text(get_text(user_id, 'select_action_first'), reply_markup=main_keyboard)
        return

    message_to_delete_id = user_data.get('message_id')
    if message_to_delete_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=message_to_delete_id)
        except Exception as e:
            print(f"Failed to delete message {message_to_delete_id} for user {user_id}: {e}")

    action = user_data['action']
    action_text_translated = get_text(user_id, 'buy_action_text') if action == 'buy' else get_text(user_id, 'sell_action_text')
    del user_state[user_id]

    await update.message.reply_text(get_text(user_id, 'thank_you_contact_soon'))

    if not ADMIN_IDS:
        print(get_text(user_id, 'admin_notification_error'))
        return

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=get_text(user_id, 'new_request_admin', username=username, action_text=action_text_translated, city=city, user_lang_name=user_lang_name),
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

    print(get_text(0, 'bot_started'))

    app.run_polling()

if __name__ == "__main__":
    main()