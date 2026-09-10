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

# Список моделей: если одна не работает, пробуем следующую
MODELS_TO_TRY = [
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "google/gemini-flash-1.5:free"
]

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

def generate_post(topic=None, retries=2):
    used = load_used_topics()
    pool = [
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
        for t in pool:
            if t not in used:
                topic = t
                break
        else:
            reset_topics()
            topic = pool[0]

    system = (
        "Ты — автор Telegram-канала «AI-навигатор». "
        "Стиль: экспертный, дружелюбный, без воды, с примерами. Используй эмодзи. "
        "Если пост содержит сравнение, инфографику или кейс — добавь метку [IMAGE]."
    )
    user = (
        f"Напиши пост на тему: {topic}. "
        "Структура: заголовок, основная часть, вывод, призыв подписаться. "
        "Длина: 900–1200 знаков. Хештег #обзор или #лайфхак. "
        "ВАЖНО: текст завершённый, без обрывов."
    )

    for model in MODELS_TO_TRY:
        for attempt in range(retries):
            try:
                print(f"[TEXT] Модель: {model} (попытка {attempt+1})")
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}],
                    temperature=0.8,
                    max_tokens=2500,
                    timeout=60
                )
                post = resp.choices[0].message.content
                print(f"[TEXT] ✅ Модель {model} сработала")
                save_used_topic(topic)
                return post
            except Exception as e:
                err = str(e)
                print(f"[TEXT] Ошибка ({model}): {err}")
                # Если модель не найдена или регион запрещён — сразу к следующей
                if "not found" in err.lower() or "404" in err or "region" in err.lower():
                    break
                time.sleep(2 ** attempt)
    return "⚠️ Не удалось сгенерировать пост."

def generate_image(prompt, retries=2):
    clean = prompt.replace('\n', ' ').replace('*', '').replace('#', '')[:200]
    encoded = urllib.parse.quote(clean)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux"
    for attempt in range(retries):
        try:
            print(f"[IMAGE] Pollinations (попытка {attempt+1})")
            r = requests.get(url, timeout=60)
            if r.status_code == 200 and len(r.content) > 1000:
                print(f"[IMAGE] ✅ Размер: {len(r.content)} байт")
                return r.content
            time.sleep(3)
        except Exception as e:
            print(f"[IMAGE] Ошибка: {e}")
            time.sleep(3)
    return None

def should_add_image(text):
    return "[IMAGE]" in text or any(k in text.lower() for k in ["сравнение", "инфографика", "график", "диаграмма", "пример", "кейс"])

def extract_image_prompt(text):
    first = text.split('\n')[0][:150]
    return f"{first}, digital illustration, modern tech style"
