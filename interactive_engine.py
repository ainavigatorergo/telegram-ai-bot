import random
from openai import OpenAI
from config import PROVOD_API_KEY, MODEL_NAME

client = OpenAI(api_key=PROVOD_API_KEY, base_url="https://api.provod.ai/v1")

def generate_poll(topic):
    """Генерирует опрос по теме поста"""
    prompt = f"""
    Придумай короткий опрос (вопрос и 3-4 варианта ответа) на тему: {topic}.
    Вопрос должен быть интересным и вовлекающим.
    Формат ответа:
    Вопрос: <текст>
    Варианты:
    - <вариант1>
    - <вариант2>
    - <вариант3>
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка генерации опроса: {e}")
        return None

def generate_quiz(topic):
    """Генерирует викторину по теме"""
    prompt = f"""
    Придумай короткую викторину (вопрос и правильный ответ) на тему: {topic}.
    Формат:
    Вопрос: <текст>
    Ответ: <правильный ответ>
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка генерации викторины: {e}")
        return None

def add_interactive(post_text):
    """Добавляет к посту интерактивный блок (опрос или викторина)"""
    # Извлекаем тему из поста (первая строка)
    topic = post_text.split('\n')[0][:100]
    
    # Случайно выбираем: опрос или викторина
    if random.choice([True, False]):
        interactive = generate_poll(topic)
        if interactive:
            return f"{post_text}\n\n📊 {interactive}"
    else:
        interactive = generate_quiz(topic)
        if interactive:
            return f"{post_text}\n\n🧠 {interactive}"
    
    return post_text
