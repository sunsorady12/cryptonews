import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext
)
import requests

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

def fetch_crypto_news(limit=3):
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

async def send_news_update(context: CallbackContext):
    """Send news update to channel"""
    try:
        news = fetch_crypto_news(limit=3)
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

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check endpoint for Render"""
    await update.message.reply_text("Bot is running and healthy!")

def main():
    """Setup and run the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add health check handler
    application.add_handler(CommandHandler("health", health_check))
    
    # Schedule news updates every 2 hours
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(
            send_news_update,
            interval=7200,  # 2 hours in seconds
            first=10        # Start after 10 seconds
        )
        logger.info("⏰ Scheduled news updates every 2 hours")
    else:
        logger.error("Job queue not available! Scheduled updates disabled")
    
    # Run the bot
    if 'RENDER' in os.environ:
        # Webhook configuration for production
        PORT = int(os.environ.get('PORT', 8080))
        WEBHOOK_URL = f"https://{os.environ.get('RENDER_SERVICE_NAME')}.onrender.com/{TELEGRAM_TOKEN}"
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=WEBHOOK_URL
        )
        logger.info("🌐 Running in webhook mode")
    else:
        # Polling for local development
        application.run_polling()
        logger.info("🔄 Running in polling mode")

if __name__ == "__main__":
    main()
