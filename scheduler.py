import asyncio
import json
from datetime import datetime
from aiogram.types import BufferedInputFile
from generator import (
    generate_post, save_post_history,
    should_add_image, generate_image, extract_image_prompt
)
from config import CHANNEL_ID, POST_TIMES, STATS_FILE

try:
    from viral_engine import ab_test_post
    from interactive_engine import add_interactive
    from audience_analyzer import get_audience_style
    MODULES_LOADED = True
except ImportError:
    MODULES_LOADED = False
    print("Внимание: некоторые модули не загружены. Работаем в базовом режиме.")

scheduled_tasks = []

async def publish_post(bot, topic=None):
    """Публикует пост с картинкой (если нужна)"""
    post = generate_post(topic)
    clean_post = post.replace("[IMAGE]", "").strip()

    try:
        if should_add_image(post):
            image_result = generate_image(extract_image_prompt(clean_post))
            if image_result:
                try:
                    if image_result["type"] == "bytes":
                        photo = BufferedInputFile(image_result["data"], filename="image.jpg")
                        if len(clean_post) <= 1024:
                            msg = await bot.send_photo(
                                chat_id=CHANNEL_ID, photo=photo, caption=clean_post
                            )
                            save_post_history(clean_post, msg.message_id)
                            print(f"[{datetime.now()}] Пост с картинкой (bytes) опубликован")
                            return
                        else:
                            await bot.send_photo(chat_id=CHANNEL_ID, photo=photo)
                            text_msg = await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
                            save_post_history(clean_post, text_msg.message_id)
                            print(f"[{datetime.now()}] Фото + текст (bytes) опубликованы")
                            return
                    else:
                        url = image_result["data"]
                        if len(clean_post) <= 1024:
                            msg = await bot.send_photo(
                                chat_id=CHANNEL_ID, photo=url, caption=clean_post
                            )
                            save_post_history(clean_post, msg.message_id)
                            print(f"[{datetime.now()}] Пост с картинкой (url) опубликован")
                            return
                        else:
                            await bot.send_photo(chat_id=CHANNEL_ID, photo=url)
                            text_msg = await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
                            save_post_history(clean_post, text_msg.message_id)
                            print(f"[{datetime.now()}] Фото + текст (url) опубликованы")
                            return
                except Exception as e:
                    print(f"⚠️ Не удалось отправить фото: {e}")

        # Текстовый пост
        msg = await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
        save_post_history(clean_post, msg.message_id)
        print(f"[{datetime.now()}] Текстовый пост опубликован (ID: {msg.message_id})")

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
