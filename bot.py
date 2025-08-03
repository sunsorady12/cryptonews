import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, ContextTypes
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_KEY = os.getenv('CRYPTO_PANIC_API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def fetch_crypto_news(limit=3):
    """Fetch top crypto news from CryptoPanic"""
    base_url = "https://cryptopanic.com/api/v1/posts/"
    params = {
        "auth_token": API_KEY,
        "public": "true",
        "kind": "news"
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])[:limit]
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return []

def format_news(news_items):
    """Format news items into a Telegram message"""
    if not news_items:
        return "No news available at the moment."
    
    message = "🔥 *Top 3 Crypto News* 🔥\n\n"
    for idx, item in enumerate(news_items, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "#")
        source = item.get("source", {}).get("title", "Unknown")
        message += f"{idx}. [{title}]({url}) - _{source}_\n\n"
    return message

async def send_news_update(context: ContextTypes.DEFAULT_TYPE):
    """Send news update to channel"""
    try:
        news = await fetch_crypto_news()
        message = format_news(news)
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info("✅ News update sent successfully")
    except Exception as e:
        logger.error(f"❌ Failed to send news: {e}")

def main():
    """Setup and run the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Create scheduler
    scheduler = AsyncIOScheduler()
    
    # Add scheduled job
    scheduler.add_job(
        send_news_update,
        'interval',
        hours=2,
        args=[application],
        next_run_time=scheduler.add_job
    )
    
    # Start scheduler
    scheduler.start()
    logger.info("⏰ Scheduled news updates every 2 hours")
    
    # Run application
    logger.info("🤖 Starting news auto-poster...")
    application.run_polling()

if __name__ == "__main__":
    main()
