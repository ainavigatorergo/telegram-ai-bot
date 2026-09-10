import json
import time
from openai import OpenAI
from config import PROVOD_API_KEY, MODEL_NAME, TOPICS_FILE, HISTORY_FILE

client = OpenAI(api_key=PROVOD_API_KEY, base_url="https://api.provod.ai/v1")

# ---------- Работа с темами ----------

def load_used_topics():
    try:
        with open(TOPICS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_used_topic(topic):
    used = load_used_topics()
    used.append(topic)
    with open(TOPICS_FILE, "w") as f:
        json.dump(used, f)

def reset_topics():
    with open(TOPICS_FILE, "w") as f:
        json.dump([], f)

# ---------- История постов ----------

def save_post_history(post_text, message_id):
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []
    history.append({"text": post_text, "message_id": message_id, "views": 0})
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-50:], f)

def get_post_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# ---------- Генерация текста поста ----------

def generate_post(topic=None, retries=3):
    used_topics = load_used_topics()
    topics_pool = [
        "обзор новой нейросети для бизнеса",
        "лайфхак по автоматизации рутины в Telegram",
        "готовый промпт для ChatGPT для маркетологов",
        "как нейросети экономят 10+ часов в неделю",
        "обзор бесплатных AI-инструментов для работы с текстом",
        "автоматизация ответов на отзывы с помощью ботов",
        "сравнение Kandinsky и Midjourney для бизнеса",
        "как составить идеальное коммерческое предложение с ИИ"
    ]
    if not topic:
        for t in topics_pool:
            if t not in used_topics:
                topic = t
                break
        else:
            reset_topics()
            topic = topics_pool[0]

    system_prompt = (
        "Ты — автор Telegram-канала «AI-навигатор». "
        "Твой стиль: экспертный, но дружелюбный. Ты даёшь готовые решения, "
        "без воды, с конкретными примерами. Используй эмодзи. "
        "Если пост содержит сравнение, инфографику или кейс — в конце добавь метку [IMAGE]."
    )
    user_prompt = (
        f"Напиши пост на тему: {topic}. "
        "Структура: заголовок, основная часть, вывод, призыв подписаться. "
        "Длина: 900–1200 знаков. Добавь хештег #обзор или #лайфхак. "
        "ВАЖНО: текст должен быть завершённым, не обрывайся на полуслове."
    )

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=2500,
                timeout=30
            )
            post = response.choices[0].message.content
            save_used_topic(topic)
            return post
        except Exception as e:
            print(f"Ошибка генерации текста (попытка {attempt + 1}/{retries}): {e}")
            time.sleep(2 ** attempt)
    return "⚠️ Не удалось сгенерировать пост. Попробуйте позже."

# ---------- Генерация картинки ----------

def generate_image(prompt, retries=3):
    """
    Генерирует изображение с автоматическим перебором моделей.
    При ошибке 503 (временная недоступность модели) — короткая пауза и повтор.
    При других ошибках — сразу переход к следующей модели.
    """
    models_to_try = [
        "google/gemini-3.1-flash-image",   # Основная: стабильная и быстрая
        "google/nano-banana-pro",           # Резервная: качественная
        "openai/gpt-image-2"                # Дополнительная: альтернатива
    ]

    for model_name in models_to_try:
        for attempt in range(retries):
            try:
                response = client.images.generate(
                    model=model_name,
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                if response.data and len(response.data) > 0:
                    print(f"✅ Картинка сгенерирована через {model_name}")
                    return response.data[0].url
            except Exception as e:
                error_str = str(e)
                print(f"Ошибка генерации ({model_name}, попытка {attempt + 1}/{retries}): {error_str}")

                # Ошибка 503 / временная недоступность — пауза и повтор
                if "503" in error_str or "MODEL_CAPABILITY_METADATA_UNAVAILABLE" in error_str:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    # Другие ошибки — не тратим попытки, сразу пробуем следующую модель
                    break

    print("❌ Не удалось сгенерировать картинку ни через одну модель")
    return None

# ---------- Логика для картинок ----------

def should_add_image(post_text):
    if "[IMAGE]" in post_text:
        return True
    keywords = ["сравнение", "инфографика", "график", "диаграмма", "пример", "кейс"]
    for kw in keywords:
        if kw in post_text.lower():
            return True
    return False

def extract_image_prompt(post_text):
    return post_text[:100] + " — визуализация для Telegram-канала"
