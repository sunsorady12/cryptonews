import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (
    Application,
    CommandHandler,
    InlineQueryHandler,
    ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
import json
from uuid import uuid4

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_KEY = os.getenv('CRYPTO_PANIC_API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')
SECRET = os.getenv('SECRET_KEY')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🚀 Welcome to Crypto News Digest Bot! Use /news to get latest updates or try inline mode with @YourBotName news btc')

async def fetch_crypto_news(filter_currency=None, limit=5):
    base_url = "https://cryptopanic.com/api/v1/posts/"
    params = {
        "auth_token": API_KEY,
        "public": "true",
        "kind": "news"
    }
    if filter_currency:
        params["currencies"] = filter_currency.upper()
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])[:limit]
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return []

def format_news(news_items):
    if not news_items:
        return "No news available at the moment."
    
    message = "🔥 *Top Crypto News* 🔥\n\n"
    for idx, item in enumerate(news_items, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "#")
        source = item.get("source", {}).get("title", "Unknown")
        message += f"{idx}. [{title}]({url}) - _{source}_\n\n"
    return message

async def send_news_update(context: ContextTypes.DEFAULT_TYPE):
    try:
        news = await fetch_crypto_news()
        message = format_news(news)
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"Error sending news: {e}")

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    currency = context.args[0] if context.args else None
    news = await fetch_crypto_news(currency)
    message = format_news(news)
    await update.message.reply_text(
        text=message,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def inline_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    currency = query.split()[1] if len(query.split()) > 1 else None
    news = await fetch_crypto_news(currency, limit=3)
    
    results = []
    for item in news:
        title = item.get("title", "Untitled")
        url = item.get("url", "#")
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=title,
                input_message_content=InputTextMessageContent(
                    message_text=f"[{title}]({url})",
                    parse_mode="Markdown"
                ),
                url=url,
                description=item.get("source", {}).get("title", "")
            )
        )
    
    await update.inline_query.answer(results)

def main():
    # Create application WITH job queue enabled
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .arbitrary_callback_data(True)
        .build()
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(InlineQueryHandler(inline_news))
    
    # Initialize scheduler
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        send_news_update,
        "interval",
        hours=6,
        args=[application],
    )
    
    # Start scheduler when bot runs
    async def post_init(application: Application):
        scheduler.start()
    
    application.post_init = post_init
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
