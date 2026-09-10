import json
from openai import OpenAI
from config import PROVOD_API_KEY, MODEL_NAME

client = OpenAI(api_key=PROVOD_API_KEY, base_url="https://api.provod.ai/v1")

COMPETITOR_CHANNELS = ["@delohub", "@neirosetibisness", "@evgeniydubskiy"]

def analyze_competitors():
    """Анализ конкурентов через открытые данные (упрощённая версия)"""
    # Здесь можно расширить: реальный парсинг через Telethon
    # Пока анализируем на основе общих трендов
    prompt = """
    Проанализируй текущие тренды в нише AI и автоматизации для бизнеса.
    Выдели:
    1. Ключевые темы, которые сейчас популярны.
    2. Общую структуру успешных постов.
    3. Рекомендации для нашего канала (3–5 пунктов).
    Ответ дай в виде короткого списка.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка анализа: {e}")
        return ""

def generate_topics_from_insights():
    """Генерирует новые темы на основе анализа"""
    insights = analyze_competitors()
    if not insights:
        return []
    
    prompt = f"""
    На основе анализа трендов:
    {insights}
    
    Сгенерируй 5 конкретных тем для наших постов про AI и автоматизацию.
    Каждая тема должна быть уникальной, с углом "как это помогает бизнесу".
    Ответ — список тем через запятую.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=300
        )
        topics = response.choices[0].message.content.split(',')
        return [t.strip() for t in topics if t.strip()]
    except Exception as e:
        print(f"Ошибка генерации тем: {e}")
        return []
