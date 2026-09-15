# ============ HIDE TOKEN FROM LOGS ============
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

import os
import asyncio
import threading
import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN set!")

# ============ NEWS CATEGORIES ============
NEWS = {
    "local": {
        "label": "🇰🇭 ព័ត៌មានក្នុងស្រុក",
        "desc": "Local Cambodia News",
        "items": [
            "រដ្ឋាភិបាលកម្ពុជាប្រកាសផែនការអភិវឌ្ឍន៍សេដ្ឋកិច្ចថ្មី។",
            "ក្រុងភ្នំពេញបន្តពង្រីកហេដ្ឋារចនាសម្ព័ន្ធដឹកជញ្ជូន។",
            "ក្រសួងអប់រំប្រកាសកម្មវិធីសិក្សាថ្មីសម្រាប់ឆ្នាំ២០២៥។",
            "កម្ពុជាទទួលបានវិនិយោគបរទេសសរុបជាង១ពាន់លានដុល្លារ។",
            "ស្ថានភាពអាកាសធាតុកម្ពុជានឹងប្រែប្រួលក្នុងរដូវវស្សា។",
        ]
    },
    "world": {
        "label": "🌍 ព័ត៌មានអន្តរជាតិ",
        "desc": "World News",
        "items": [
            "អង្គការសហប្រជាជាតិប្រជុំពិភាក្សាអំពីការផ្លាស់ប្តូរអាកាសធាតុ។",
            "ប្រទេសអាស៊ីអាគ្នេយ៍បង្កើនកិច្ចសហប្រតិបត្តិការពាណិជ្ជកម្ម។",
            "ទីផ្សារភាគហ៊ុនពិភពលោកមានការប្រែប្រួលខ្លាំង។",
            "ការប្រជុំកំពូល G20 នឹងប្រព្រឹត្តទៅនៅចុងឆ្នាំ។",
            "បច្ចេកវិទ្យា AI កំពុងផ្លាស់ប្តូរទីផ្សារការងារទូទាំងពិភពលោក។",
        ]
    },
    "economy": {
        "label": "💰 ព័ត៌មានសេដ្ឋកិច្ច",
        "desc": "Economy News",
        "items": [
            "ប្រាក់រៀលកម្ពុជាមានស្ថិរភាពល្អប្រឆាំងនឹងដុល្លារអាមេរិក។",
            "វិស័យទេសចរណ៍កម្ពុជាបន្តងើបឡើងក្រោយជំងឺកូវីដ។",
            "ការនាំចេញទំនិញកម្ពុជាកើនឡើង១៥ភាគរយក្នុងឆ្នាំនេះ។",
            "ធនាគារជាតិកម្ពុជាប្រកាសគោលនយោបាយការប្រាក់ថ្មី។",
            "ការវិនិយោគលើហេដ្ឋារចនាសម្ព័ន្ធឌីជីថលកើនឡើងខ្លាំង។",
        ]
    },
    "sport": {
        "label": "⚽ ព័ត៌មានកីឡា",
        "desc": "Sports News",
        "items": [
            "ក្រុមបាល់ទាត់ជាតិកម្ពុជាជោគជ័យក្នុងការប្រកួតអន្តរជាតិ។",
            "ក្រុមហ៊ុន SEA Games ២០២៥ នឹងប្រព្រឹត្តទៅនៅប្រទេសថៃ។",
            "តារាកីឡាករខ្មែរជោគជ័យក្នុងការប្រកួតអាស៊ី។",
            "ព្រឹត្តិការណ៍ Marathon ភ្នំពេញទាក់ទាញអ្នកចូលរួមជាងពីរពាន់នាក់។",
            "កម្ពុជាបន្តអភិវឌ្ឍវិស័យកីឡាជាតិ។",
        ]
    },
    "tech": {
        "label": "💻 ព័ត៌មានបច្ចេកវិទ្យា",
        "desc": "Technology News",
        "items": [
            "កម្ពុជាពង្រីកប្រើប្រាស់ទូរស័ព្ទ ៥G ទូទាំងប្រទេស។",
            "ក្រុមហ៊ុន Tech ថ្មីៗក្នុងកម្ពុជាទទួលបានការវិនិយោគ។",
            "AI កំពុងត្រូវបានប្រើប្រាស់ក្នុងវិស័យធនាគារខ្មែរ។",
            "ការអប់រំអនឡាញកើនឡើងខ្លាំងក្នុងកម្ពុជា។",
            "កម្ពុជានឹងចាប់ផ្តើមប្រើប្រាស់ប្រព័ន្ធបង់ប្រាក់ឌីជីថលថ្មី។",
        ]
    }
}

# ============ FLASK ============
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "Khmer News Bot is running!", 200

# ============ HELPERS ============
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🇰🇭 ក្នុងស្រុក", callback_data="local"),
         InlineKeyboardButton("🌍 អន្តរជាតិ", callback_data="world")],
        [InlineKeyboardButton("💰 សេដ្ឋកិច្ច", callback_data="economy"),
         InlineKeyboardButton("⚽ កីឡា", callback_data="sport")],
        [InlineKeyboardButton("💻 បច្ចេកវិទ្យា", callback_data="tech")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_news_text(category):
    import random
    cat = NEWS[category]
    news_item = random.choice(cat["items"])
    today = datetime.date.today().strftime("%d/%m/%Y")
    text = (
        f"{cat['label']}\n"
        f"📅 {today}\n\n"
        f"📰 {news_item}\n\n"
        "ជ្រើសរើសប្រភេទព័ត៌មានទៀត 👇"
    )
    return text

# ============ COMMANDS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "មិត្ត"
    today = datetime.date.today().strftime("%d/%m/%Y")
    welcome = (
        f"👋 សួស្តី {user_name}!\n\n"
        f"ស្វាគមន៍មកកាន់ <b>ព័ត៌មានប្រចាំថ្ងៃ</b> 📰\n\n"
        f"📅 ថ្ងៃទី {today}\n\n"
        "ទទួលបានព័ត៌មានថ្មីៗប្រចាំថ្ងៃ!\n\n"
        "<b>ជ្រើសរើសប្រភេទព័ត៌មាន:</b>"
    )
    await update.message.reply_text(
        welcome,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 <b>ជ្រើសរើសប្រភេទព័ត៌មាន:</b>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

async def local_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        get_news_text("local"),
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

async def world_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        get_news_text("world"),
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📰 <b>ព័ត៌មានប្រចាំថ្ងៃ Bot</b>\n\n"
        "ទទួលបានព័ត៌មានថ្មីៗប្រចាំថ្ងៃ!\n\n"
        "<b>Commands:</b>\n"
        "/start - ទំព័រដើម\n"
        "/news - ជ្រើសរើសព័ត៌មាន\n"
        "/local - ព័ត៌មានក្នុងស្រុក\n"
        "/world - ព័ត៌មានអន្តរជាតិ\n"
        "/help - ជំនួយ\n\n"
        "ចុចប៊ូតុងខាងក្រោម 👇"
    )
    await update.message.reply_text(
        help_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

# ============ CALLBACK HANDLER ============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in NEWS:
        text = get_news_text(query.data)
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

# ============ BOT STARTUP ============
async def run_bot_async():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("local", local_command))
    app.add_handler(CommandHandler("world", world_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)

    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    logger.info("Khmer News Bot is polling and ready!")
    while True:
        await asyncio.sleep(1)

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot_async())

bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
