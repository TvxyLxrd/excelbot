import os
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, ConversationHandler, Filters


# Api бота
TOKEN = ''

# Подключение к Google Sheets
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS = ServiceAccountCredentials.from_json_keyfile_name('path/to/your/credentials.json', SCOPE)
SHEET_NAME = 'Лист1'
SPREADSHEET_ID = 'your_spreadsheet_id'

CREATE_SALE, GET_CHANNEL, GET_DATE, GET_TIME, GET_BUYER, GET_FORMAT, GET_PRICE, GET_MANAGER = range(8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("Создать продажу"), KeyboardButton("Календарь продаж")],
                [KeyboardButton("Общий доход"), KeyboardButton("Каналы")]]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Главное меню", reply_markup=reply_markup)

async def create_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Создание продажи")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название канала")
    return GET_CHANNEL

async def get_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите дату публикации")
    return GET_DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now()
    calendar = [[InlineKeyboardButton(f"{today + timedelta(days=i):%d.%m.%Y}", callback_data=f"{today + timedelta(days=i):%Y-%m-%d}") for i in range(-7, 8, 1)]]
    reply_markup = InlineKeyboardMarkup(calendar)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите дату", reply_markup=reply_markup)
    return GET_TIME

async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.callback_query.data
    await update.callback_query.answer()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Введите время публикации (ЧЧ:ММ)")
    return GET_BUYER

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Введите username или имя покупателя")
    return GET_BUYER

async def get_buyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['buyer'] = update.message.text
    keyboard = [[KeyboardButton("Пост"), KeyboardButton("Сторис"), KeyboardButton("Таргет")]]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите формат публикации", reply_markup=reply_markup)
    return GET_FORMAT

async def get_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['format'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Напишите цену рекламного места")
    return GET_PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Напишите % менеджеру")
    return GET_MANAGER

async def get_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['manager'] = update.message.text
    report = f"Канал: {context.user_data['channel']}\n" \
             f"Дата: {context.user_data['date']}\n" \
             f"Время: {context.user_data['time']}\n" \
             f"Покупатель: {context.user_data['buyer']}\n" \
             f"Формат: {context.user_data['format']}\n" \
             f"Цена: {context.user_data['price']}\n" \
             f"% менеджеру: {context.user_data['manager']}"

    client = gspread.authorize(CREDS)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    sheet.append_row([context.user_data['channel'], context.user_data['date'], context.user_data['time'], context.user_data['buyer'], context.user_data['format'], context.user_data['price'], context.user_data['manager']])

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Данные успешно сохранены в Google Sheets. Ссылка: {url}")
    await start(update, context)
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("create_sale", create_sale)],
        states={
            CREATE_SALE: [MessageHandler(Filters.text & ~Filters.command, get_channel)],
            GET_CHANNEL: [MessageHandler(Filters.text & ~Filters.command, get_date)],
            GET_DATE: [CallbackQueryHandler(handle_date)],
            GET_TIME: [MessageHandler(Filters.text & ~Filters.command, get_buyer)],
            GET_BUYER: [MessageHandler(Filters.text & ~Filters.command, get_format)],
            GET_FORMAT: [MessageHandler(Filters.text & ~Filters.command, get_price)],
            GET_PRICE: [MessageHandler(Filters.text & ~Filters.command, get_manager)],
            GET_MANAGER: [MessageHandler(Filters.text & ~Filters.command, get_manager)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    updater.add_handler(conv_handler)
    updater.run_polling()

if __name__ == '__main__':
    main()
