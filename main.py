import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.error import TelegramError
print(os.getenv("TELEGRAM_TOKEN"))
print(os.getenv("ADMIN_ID"))
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# 💾 Временное хранилище
user_state = {}
current_rate = { "usdt": None }  # Ручной курс

# 📱 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Купить USDT", callback_data="buy")],
        [InlineKeyboardButton("💸 Продать USDT", callback_data="sell")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# 📊 Команда /rate — показывает текущий вручную установленный курс
async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate = current_rate["usdt"]
    if rate:
        await update.message.reply_text(f"💱 Текущий курс USDT: {rate} ₽")
    else:
        await update.message.reply_text("Курс USDT ещё не установлен.")

# 🔧 Команда /setrate — устанавливает курс (только админ)
async def set_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return  # игнорируем команду, чтобы пользователи не видели

    if not context.args:
        await update.message.reply_text("❗ Используйте: /setrate 93.5")
        return

    try:
        rate = float(context.args[0])
        current_rate["usdt"] = rate
        # Удаляем команду пользователя, чтобы скрыть
        await update.message.delete()
        # Отправляем админу подтверждение
        await context.bot.send_message(ADMIN_ID, f"✅ Курс USDT установлен: {rate} ₽")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Пример: /setrate 93.5")

# 🤖 Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data
    user_state[user_id] = {'action': action}

    rate = current_rate["usdt"]
    rate_text = f"\n💱 Текущий курс: {rate} ₽" if rate else "\n⚠️ Курс пока не установлен."

    await query.edit_message_text(
        f"Вы выбрали {'покупку' if action == 'buy' else 'продажу'} USDT.{rate_text}\n\nВведите ваш город:"
    )

# 🏙 Обработка ввода города
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"id: {user_id}"
    city = update.message.text.strip()

    user = update.effective_user

    print('user', user)

    if user_id not in user_state or 'action' not in user_state[user_id]:
        await update.message.reply_text("Сначала выберите действие через /start.")
        return

    action = user_state[user_id]['action']
    action_text = "КУПИТЬ" if action == "buy" else "ПРОДАТЬ"
    del user_state[user_id]

    await update.message.reply_text("Спасибо! Мы свяжемся с вами.")

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 Новый запрос:\n\n"
            f"👤 Пользователь: @{username}\n"
            f"🎯 Действие: {action_text}\n"
            f"🌍 Город: {city}"
    )

async def error_handler(update, context):
    print(f"Exception while handling update: {update}")
    import traceback
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)

# 🚀 Запуск бота
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rate", rate))
    app.add_handler(CommandHandler("setrate", set_rate))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))
    app.add_error_handler(error_handler)

    print("Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()