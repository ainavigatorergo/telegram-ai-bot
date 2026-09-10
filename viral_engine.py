import asyncio
from openai import OpenAI
from config import PROVOD_API_KEY, MODEL_NAME, CHANNEL_ID
from generator import save_post_history

client = OpenAI(api_key=PROVOD_API_KEY, base_url="https://api.provod.ai/v1")

def generate_headlines(topic):
    """Генерирует 2 варианта заголовков для A/B-теста"""
    prompt = f"""
    Придумай 2 разных заголовка для поста на тему: {topic}.
    Первый — интригующий (вопрос или неожиданный факт).
    Второй — практический (обещание пользы).
    Ответ дай в формате:
    1. <заголовок>
    2. <заголовок>
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=150
        )
        lines = response.choices[0].message.content.strip().split('\n')
        headlines = []
        for line in lines:
            if line.strip() and line[0].isdigit():
                headlines.append(line.split('.', 1)[-1].strip())
        return headlines[:2]
    except Exception as e:
        print(f"Ошибка генерации заголовков: {e}")
        return []

async def ab_test_post(bot, channel_id, base_post):
    """Публикует 2 варианта поста с разными заголовками и выбирает лучший"""
    # Извлекаем тему из первого предложения (упрощённо)
    topic = base_post.split('\n')[0][:100]
    headlines = generate_headlines(topic)
    
    if len(headlines) < 2:
        # Если не удалось сгенерировать — публикуем как есть
        msg = await bot.send_message(chat_id=channel_id, text=base_post)
        save_post_history(base_post, msg.message_id)
        return
    
    # Вариант A
    post_a = f"{headlines[0]}\n\n{base_post}"
    msg_a = await bot.send_message(chat_id=channel_id, text=post_a)
    save_post_history(post_a, msg_a.message_id)
    
    # Ждём 30 минут (для теста можно уменьшить, но в продакшене 30 мин)
    await asyncio.sleep(30 * 60)
    
    # Вариант B (удаляем А, чтобы не дублировать, или оставляем — решай сам)
    # Для чистоты эксперимента лучше удалить А и опубликовать B
    try:
        await bot.delete_message(chat_id=channel_id, message_id=msg_a.message_id)
    except:
        pass
    
    post_b = f"{headlines[1]}\n\n{base_post}"
    msg_b = await bot.send_message(chat_id=channel_id, text=post_b)
    save_post_history(post_b, msg_b.message_id)
    
    # В реальной версии здесь нужно собрать статистику и оставить лучший вариант
    # Пока просто оставляем оба (или можно оставить только B)
