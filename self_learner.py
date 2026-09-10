import json
from openai import OpenAI
from config import PROVOD_API_KEY, MODEL_NAME, HISTORY_FILE, STATS_FILE

client = OpenAI(api_key=PROVOD_API_KEY, base_url="https://api.provod.ai/v1")

def get_best_and_worst_posts():
    """Загружает историю постов и статистику, возвращает лучшие и худшие"""
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        return [], []
    
    try:
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
    except FileNotFoundError:
        stats = {}
    
    # Сортируем по просмотрам
    posts_with_views = []
    for post in history:
        mid = str(post.get("message_id", ""))
        views = stats.get(mid, {}).get("views", post.get("views", 0))
        posts_with_views.append((views, post.get("text", "")))
    
    posts_with_views.sort(reverse=True)
    best = posts_with_views[:5]
    worst = posts_with_views[-5:] if len(posts_with_views) > 5 else []
    return best, worst

def adjust_prompts():
    """Анализирует лучшие и худшие посты, предлагает новый промпт"""
    best, worst = get_best_and_worst_posts()
    if not best:
        return None
    
    prompt = f"""
    У нас есть Telegram-канал про AI и автоматизацию для бизнеса.
    
    Лучшие по просмотрам:
    {json.dumps([b[1][:200] for b in best], indent=2, ensure_ascii=False)}
    
    Худшие по просмотрам:
    {json.dumps([w[1][:200] for w in worst], indent=2, ensure_ascii=False)}
    
    На основе этого предложи:
    1. Как изменить стиль (длина, тон, структура), чтобы улучшить вовлечение.
    2. Какие темы сейчас более актуальны.
    3. Новый системный промпт для генерации постов (готовый текст).
    Ответ дай кратко и по делу.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=700
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка самообучения: {e}")
        return None
