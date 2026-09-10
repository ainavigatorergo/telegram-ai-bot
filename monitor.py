import json
import feedparser
import asyncio
from openai import OpenAI
from config import PROVOD_API_KEY, MODEL_NAME, POOL_FILE

client = OpenAI(api_key=PROVOD_API_KEY, base_url="https://api.provod.ai/v1")

RSS_FEEDS = [
    "https://habr.com/ru/rss/hub/ai/",
    "https://vc.ru/rss/ai",
    "https://roem.ru/feed/"
]

def fetch_rss_news():
    news = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                news.append({
                    "title": entry.title,
                    "summary": entry.get("summary", "")[:200]
                })
        except Exception as e:
            print(f"Ошибка RSS {url}: {e}")
    return news

def get_trending_topics():
    rss_news = fetch_rss_news()
    if not rss_news:
        return []
    
    prompt = f"""
    Вот свежие новости из AI-сферы:
    {json.dumps(rss_news, indent=2, ensure_ascii=False)}
    
    Выдели 3–5 ключевых трендов. Для каждого предложи конкретную тему для поста 
    (с углом «как это помогает бизнесу»).
    Ответ дай списком, каждую тему с новой строки.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        topics = response.choices[0].message.content.split('\n')
        return [t.strip("- •").strip() for t in topics if t.strip()]
    except Exception as e:
        print(f"Ошибка генерации трендов: {e}")
        return []

def update_topics_pool():
    new_topics = get_trending_topics()
    if not new_topics:
        return
    try:
        with open(POOL_FILE, "r") as f:
            pool = json.load(f)
    except FileNotFoundError:
        pool = []
    for t in new_topics:
        if t and t not in pool:
            pool.append(t)
    with open(POOL_FILE, "w") as f:
        json.dump(pool[-30:], f)
    print(f"Пул тем обновлён: {len(new_topics)} новых тем")
