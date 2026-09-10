import asyncio
import json
from datetime import datetime
from aiogram.types import BufferedInputFile
from generator import (generate_post, save_post_history, should_add_image,
                       generate_image, extract_image_prompt)
from config import CHANNEL_ID, POST_TIMES, SELF_URL
import requests

async def publish_post(bot, topic=None):
    post = generate_post(topic)
    clean = post.replace("[IMAGE]", "").strip()
    try:
        if should_add_image(post):
            img = generate_image(extract_image_prompt(clean))
            if img:
                photo = BufferedInputFile(img, filename="image.jpg")
                if len(clean) <= 1024:
                    msg = await bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=clean)
                    save_post_history(clean, msg.message_id)
                    print(f"[{datetime.now()}] Пост с картинкой")
                    return
                else:
                    await bot.send_photo(chat_id=CHANNEL_ID, photo=photo)
                    txt = await bot.send_message(chat_id=CHANNEL_ID, text=clean)
                    save_post_history(clean, txt.message_id)
                    print(f"[{datetime.now()}] Фото + текст")
                    return
        msg = await bot.send_message(chat_id=CHANNEL_ID, text=clean)
        save_post_history(clean, msg.message_id)
        print(f"[{datetime.now()}] Текстовый пост")
    except Exception as e:
        print(f"Ошибка публикации: {e}")

async def run_daily_analysis():
    print("Анализ...")
    try:
        from analytics import generate_topics_from_insights
        topics = generate_topics_from_insights()
        if topics:
            try:
                with open("topics_pool.json", "r") as f: pool = json.load(f)
            except: pool = []
            for t in topics:
                if t not in pool: pool.append(t)
            with open("topics_pool.json", "w") as f: json.dump(pool[-30:], f)
        print("Анализ завершён.")
    except Exception as e:
        print(f"Ошибка анализа: {e}")

async def monitor_loop():
    while True:
        try:
            from monitor import update_topics_pool
            update_topics_pool()
        except Exception as e:
            print(f"Ошибка мониторинга: {e}")
        await asyncio.sleep(6*3600)

async def self_ping_loop():
    """Пингуем сами себя, чтобы Render не усыплял сервис"""
    while True:
        try:
            requests.get(SELF_URL, timeout=10)
            print("[PING] самопинг отправлен")
        except Exception as e:
            print(f"[PING] ошибка: {e}")
        await asyncio.sleep(240)  # каждые 4 минуты

async def schedule_posts(bot):
    times = [t.strip() for t in POST_TIMES]
    async def loop():
        await run_daily_analysis()
        asyncio.create_task(monitor_loop())
        asyncio.create_task(self_ping_loop())
        while True:
            now = datetime.now()
            for t in times:
                try: h, m = map(int, t.split(':'))
                except: continue
                if now.hour == h and now.minute == m:
                    topic = ("новости AI" if h < 12 else
                             "лайфхак по автоматизации" if h < 17 else
                             "кейс или тренд")
                    await publish_post(bot, topic)
                    await asyncio.sleep(60)
            if now.hour == 2 and now.minute == 0:
                await run_daily_analysis()
                await asyncio.sleep(60)
            await asyncio.sleep(30)
    task = asyncio.create_task(loop())
    print(f"Расписание: {', '.join(times)} МСК")
