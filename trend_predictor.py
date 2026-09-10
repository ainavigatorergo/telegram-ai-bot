from openai import OpenAI
from config import PROVOD_API_KEY, MODEL_NAME

client = OpenAI(api_key=PROVOD_API_KEY, base_url="https://api.provod.ai/v1")

def predict_trends():
    """Прогнозирует, какие темы будут актуальны в ближайшие 2–3 дня"""
    prompt = """
    Ты — аналитик трендов в сфере AI и автоматизации для бизнеса.
    На основе текущих новостей и общей динамики предложи 3 темы, 
    которые станут популярными в ближайшие 2–3 дня.
    Для каждой темы укажи, почему она будет актуальна.
    Ответ дай списком.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка прогноза трендов: {e}")
        return None

def get_trending_topics():
    """Возвращает список тем для публикации на основе прогноза"""
    trends = predict_trends()
    if not trends:
        return []
    # Разбиваем на строки и убираем пустые
    lines = [l.strip("- •1234567890. ") for l in trends.split('\n') if l.strip()]
    return [l for l in lines if len(l) > 10][:3]
