import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POST_TIMES = os.getenv("POST_TIMES", "10:00,19:00").split(',')
PORT = int(os.getenv("PORT", 8080))
SELF_URL = os.getenv("SELF_URL", "https://ainavbot.onrender.com")  # URL на Render

TOPICS_FILE = "used_topics.json"
HISTORY_FILE = "post_history.json"
STATS_FILE = "post_stats.json"
POOL_FILE = "topics_pool.json"
