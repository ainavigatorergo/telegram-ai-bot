import json
import time
import requests
import urllib.parse
from openai import OpenAI
from config import OPENROUTER_API_KEY, TOPICS_FILE, HISTORY_FILE

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# ---------- Темы ----------

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

# ---------- История ----------

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

# ---------- Текст через OpenRouter с перебором моделей ----------

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

    # Резервные модели — если одна не работает, пробуем следующую
    models_to_try = [
        "google/gemini-2.0-flash-exp:free",
        "google/gemini-flash-1.5:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free"
    ]

    for model_name in models_to_try:
        for attempt in range(retries):
            try:
                print(f"[TEXT] Пробую модель: {model_name} (попытка {attempt + 1})")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8,
                    max_tokens=2500,
                    timeout=60
                )
                post = response.choices[0].message.content
                print(f"[TEXT] ✅ Модель {model_name} сработала")
                save_used_topic(topic)
                return post
            except Exception as e:
                error_str = str(e)
                print(f"[TEXT] Ошибка ({model_name}, попытка {attempt + 1}): {error_str}")

                # Если модель не найдена или заблокирована по региону — сразу следующая
                if "not found" in error_str.lower() or "404" in error_str or "region" in error_str.lower():
                    break

                time.sleep(2 ** attempt)

    return "⚠️ Не удалось сгенерировать пост. Попробуйте позже."

# ---------- Картинка через Pollinations.ai ----------

def generate_image(prompt, retries=2):
    clean_prompt = prompt.replace('\n', ' ').replace('*', '').replace('#', '')[:200]
    encoded_prompt = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux"

    for attempt in range(retries):
        try:
            print(f"[IMAGE] Pollinations запрос (попытка {attempt + 1})...")
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 1000:
                print(f"[IMAGE] ✅ Готово, размер: {len(resp.content)} байт")
                return resp.content
            else:
                print(f"[IMAGE] ⚠️ Статус: {resp.status_code}, размер: {len(resp.content)}")
                time.sleep(3)
        except Exception as e:
            print(f"[IMAGE] Ошибка (попытка {attempt + 1}): {e}")
            time.sleep(3)

    print("[IMAGE] ❌ Не удалось получить картинку")
    return None

# ---------- Логика определения картинки ----------

def should_add_image(post_text):
    if "[IMAGE]" in post_text:
        return True
    keywords = ["сравнение", "инфографика", "график", "диаграмма", "пример", "кейс"]
    for kw in keywords:
        if kw in post_text.lower():
            return True
    return False

def extract_image_prompt(post_text):
    first_line = post_text.split('\n')[0][:150]
    return f"{first_line}, digital illustration, modern tech style"
