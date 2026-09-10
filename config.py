import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROVOD_API_KEY = os.getenv("PROVOD_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemini-3.5-flash")
POST_TIMES = os.getenv("POST_TIMES", "10:00,19:00").split(',')
PORT = int(os.getenv("PORT", 8080))

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

TOPICS_FILE = "used_topics.json"
HISTORY_FILE = "post_history.json"
STATS_FILE = "post_stats.json"
POOL_FILE = "topics_pool.json"
