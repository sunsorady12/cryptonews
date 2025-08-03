import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CallbackContext

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

def main():
    """Setup and run the bot"""
    # Verify job queue support
    try:
        from telegram.ext import JobQueue
    except ImportError:
        logger.error("CRITICAL: Install with: pip install python-telegram-bot[job-queue]")
        return

    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Job queue will now be available
    job_queue = application.job_queue
    job_queue.run_repeating(
        callback=send_news_update,
        interval=7200,
        first=10
    )
    
    logger.info("🤖 Bot started with job scheduling")
    application.run_polling()

# ... rest of your existing functions ...

if __name__ == "__main__":
    main()
