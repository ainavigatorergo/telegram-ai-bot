import asyncio
import json
from datetime import datetime
from aiogram.types import BufferedInputFile
from generator import (
    generate_post, save_post_history,
    should_add_image, generate_image, extract_image_prompt
)
from config import CHANNEL_ID, POST_TIMES

scheduled_tasks = []

async def publish_post(bot, topic=None):
    post = generate_post(topic)
    clean_post = post.replace("[IMAGE]", "").strip()

    try:
        if should_add_image(post):
            img_bytes = generate_image(extract_image_prompt(clean_post))
            if img_bytes:
                photo = BufferedInputFile(img_bytes, filename="image.jpg")
                try:
                    if len(clean_post) <= 1024:
                        msg = await bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=clean_post)
                        save_post_history(clean_post, msg.message_id)
                        print(f"[{datetime.now()}] Пост с картинкой опубликован")
                        return
                    else:
                        await bot.send_photo(chat_id=CHANNEL_ID, photo=photo)
                        text_msg = await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
                        save_post_history(clean_post, text_msg.message_id)
                        print(f"[{datetime.now()}] Фото + текст опубликованы")
                        return
                except Exception as e:
                    print(f"[SCHED] Ошибка отправки фото: {e}")

        msg = await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
        save_post_history(clean_post, msg.message_id)
        print(f"[{datetime.now()}] Текстовый пост опубликован")
    except Exception as e:
        print(f"Ошибка публикации: {e}")

async def run_daily_analysis():
    print("Запускаю ежедневный анализ...")
    try:
        from analytics import generate_topics_from_insights
        topics = generate_topics_from_insights()
        if topics:
            try:
                with open("topics_pool.json", "r") as f:
                    pool = json.load(f)
            except FileNotFoundError:
                pool = []
            for t in topics:
                if t not in pool:
                    pool.append(t)
            with open("topics_pool.json", "w") as f:
                json.dump(pool[-30:], f)
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
        await asyncio.sleep(6 * 3600)

async def schedule_posts(bot):
    times = [t.strip() for t in POST_TIMES]

    async def scheduler_loop():
        await run_daily_analysis()
        asyncio.create_task(monitor_loop())

        while True:
            now = datetime.now()
            for time_str in times:
                try:
                    h, m = map(int, time_str.split(':'))
                except:
                    continue
                if now.hour == h and now.minute == m:
                    if h < 12:
                        topic = "новости AI и обзор инструментов"
                    elif h < 17:
                        topic = "лайфхак по автоматизации"
                    else:
                        topic = "кейс или разбор тренда"
                    await publish_post(bot, topic)
                    await asyncio.sleep(60)

            if now.hour == 2 and now.minute == 0:
                await run_daily_analysis()
                await asyncio.sleep(60)

            await asyncio.sleep(30)

    task = asyncio.create_task(scheduler_loop())
    scheduled_tasks.append(task)
    print(f"Расписание установлено: {', '.join(times)} МСК")
