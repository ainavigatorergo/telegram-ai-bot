import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from scheduler import schedule_posts, publish_post
from generator import (
    generate_post, generate_image, get_post_history,
    should_add_image, extract_image_prompt
)
from config import BOT_TOKEN, CHANNEL_ID, PORT

app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------- Отправка поста с картинкой ----------

async def send_post_with_image(clean_post, image_result):
    """Отправляет пост с картинкой (bytes или url). Возвращает True при успехе."""
    if not image_result:
        return False

    try:
        if image_result["type"] == "bytes":
            photo = BufferedInputFile(image_result["data"], filename="image.jpg")
            if len(clean_post) <= 1024:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=clean_post)
            else:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=photo)
                await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
            print("[BOT] ✅ Пост с картинкой (bytes) отправлен")
            return True
        else:
            url = image_result["data"]
            if len(clean_post) <= 1024:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=url, caption=clean_post)
            else:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=url)
                await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
            print("[BOT] ✅ Пост с картинкой (url) отправлен")
            return True
    except Exception as e:
        print(f"[BOT] ⚠️ Не удалось отправить фото: {e}")
        return False

# ---------- Обработка комментариев ----------

@dp.channel_post()
async def on_channel_post(message: types.Message):
    if message.reply_to_message:
        comment_text = message.text or message.caption or ""
        if not comment_text:
            return
        original_post = message.reply_to_message.text or message.reply_to_message.caption or ""
        try:
            from comment_replier import generate_reply
            reply = generate_reply(comment_text, original_post)
            if reply:
                await message.reply(reply)
                print(f"Ответ на комментарий: {reply[:50]}...")
        except Exception as e:
            print(f"Ошибка ответа на комментарий: {e}")

# ---------- Команды ----------

@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "🤖 Я AI-администратор канала @ainavigatorErgo\n\n"
        "Команды:\n"
        "/test_post – сгенерировать и отправить пост\n"
        "/post <текст> – отправить свой пост\n"
        "/image <промпт> – сгенерировать картинку\n"
        "/stats – статистика\n"
        "/analyze – анализ трендов\n"
        "/help – помощь"
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await start_cmd(message)

@dp.message(Command("test_post"))
async def test_post_cmd(message: Message):
    await message.answer("⏳ Генерирую пост...")
    post = generate_post()
    clean_post = post.replace("[IMAGE]", "").strip()

    needs_image = should_add_image(post)
    print(f"[BOT] should_add_image = {needs_image}")

    if needs_image:
        await message.answer("🎨 Генерирую картинку...")
        prompt = extract_image_prompt(clean_post)
        print(f"[BOT] Промпт для картинки: {prompt[:80]}...")
        image_result = generate_image(prompt)
        print(f"[BOT] image_result type = {image_result['type'] if image_result else None}")

        if image_result:
            sent = await send_post_with_image(clean_post, image_result)
            if sent:
                await message.answer("✅ Пост с картинкой отправлен в канал!")
                return
            else:
                await message.answer("⚠️ Картинка не ушла, отправляю только текст.")

    await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
    await message.answer("✅ Текстовый пост отправлен.")

@dp.message(Command("post"))
async def custom_post_cmd(message: Message):
    text = message.text.replace("/post", "", 1).strip()
    if not text:
        await message.answer("Напиши текст после /post")
        return
    await bot.send_message(chat_id=CHANNEL_ID, text=text)
    await message.answer("✅ Опубликовано!")

@dp.message(Command("image"))
async def image_cmd(message: Message):
    prompt = message.text.replace("/image", "", 1).strip()
    if not prompt:
        await message.answer("Напиши промпт после /image")
        return
    await message.answer("🎨 Генерирую картинку...")
    result = generate_image(prompt)
    if result and result["type"] == "bytes":
        photo = BufferedInputFile(result["data"], filename="image.jpg")
        await message.answer_photo(photo=photo, caption="Готово!")
    elif result and result["type"] == "url":
        try:
            await message.answer_photo(photo=result["data"], caption="Готово!")
        except Exception as e:
            await message.answer(f"Ссылка: {result['data']}\n(Ошибка: {e})")
    else:
        await message.answer("Не удалось сгенерировать. Проверь баланс provod.ai.")

@dp.message(Command("stats"))
async def stats_cmd(message: Message):
    history = get_post_history()
    if not history:
        await message.answer("Нет данных.")
        return
    stats_text = "📊 Последние 5 постов:\n\n"
    for i, item in enumerate(history[-5:], 1):
        stats_text += f"{i}. {item['text'][:60]}...\n"
    await message.answer(stats_text)

@dp.message(Command("analyze"))
async def analyze_cmd(message: Message):
    await message.answer("🔍 Анализирую тренды...")
    try:
        from analytics import generate_topics_from_insights
        topics = generate_topics_from_insights()
        if topics:
            await message.answer("📌 Темы:\n" + "\n".join(f"- {t}" for t in topics))
        else:
            await message.answer("Не удалось собрать данные.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def main():
    await schedule_posts(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    asyncio.run(main())
