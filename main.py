from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# 🔐 Настройки
print(os.getenv("TELEGRAM_TOKEN"))
print(os.getenv("ADMIN_IDS"))
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS = int(os.getenv("ADMIN_IDS"))

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
    keyboard = [
        [InlineKeyboardButton("💰 Купить USDT", callback_data="buy")],
        [InlineKeyboardButton("💸 Продать USDT", callback_data="sell")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🚀 Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

# 📊 Команда /rate — показывает текущие курсы
async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if update.effective_user.id not in ADMIN_IDS:
        return
    if len(context.args) != 2:
        await update.message.reply_text("Используй: /setratebuy PLN 3.25")
        return
    currency, value = context.args
    try:
        rates["buy"][currency.upper()] = float(value)
        await update.message.reply_text(f"✅ Курс покупки {currency.upper()} обновлён: {value}")
    except:
        await update.message.reply_text("❌ Ошибка формата.")

# 🔧 Команда /setratesell PLN 3.97
async def set_rate_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if len(context.args) != 2:
        await update.message.reply_text("Используй: /setratesell PLN 3.97")
        return
    currency, value = context.args
    try:
        rates["sell"][currency.upper()] = float(value)
        await update.message.reply_text(f"✅ Курс продажи {currency.upper()} обновлён: {value}")
    except:
        await update.message.reply_text("❌ Ошибка формата.")

# 🤖 Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data
    user_state[user_id] = {'action': action}

    rate_info = rates[action]
    text = f"🚀 Вы выбрали {'покупку' if action == 'buy' else 'продажу'} USDT\n\n"

    text += "📈 Курсы:\n"
    if action == "buy":
        for currency, value in rate_info.items():
            text += f"1 USDT = {value} {currency}\n"
    else:
        for currency, value in rate_info.items():
            text += f"{value} {currency} = 1 USDT\n"

    text += "\n🌍 Введите ваш город:"

    await query.edit_message_text(text)

# 🏙 Обработка ввода города
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"id: {user_id}"
    city = update.message.text.strip()

    if user_id not in user_state or 'action' not in user_state[user_id]:
        await update.message.reply_text("Сначала выберите действие через /start.")
        return

    action = user_state[user_id]['action']
    action_text = "КУПИТЬ 🟢" if action == "buy" else "ПРОДАТЬ 🔴"
    del user_state[user_id]

    await update.message.reply_text("✅ Спасибо! Мы скоро свяжемся с вами.")

    for admin_id in ADMIN_IDS:


    await context.bot.send_message(
            admin_id,
            f"🔔 <b>Новый запрос</b>\n\n"
            f"👤 Пользователь: @{username}\n"
            f"🎯 Действие: {action_text}\n"
            f"🌍 Город: {city}",
            parse_mode='HTML'
        )

# 🚀 Запуск бота
def main():
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