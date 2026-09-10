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

# ---------- Flask для Render ----------

app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# ---------- Инициализация бота и диспетчера ----------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------- Обработка комментариев в канале ----------

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
        await message.answer("🎨 Генерирую картинку (до 60 секунд)...")
        prompt = extract_image_prompt(clean_post)
        img_bytes = generate_image(prompt)

        if img_bytes:
            photo = BufferedInputFile(img_bytes, filename="image.jpg")
            try:
                if len(clean_post) <= 1024:
                    await bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=clean_post)
                else:
                    await bot.send_photo(chat_id=CHANNEL_ID, photo=photo)
                    await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
                await message.answer("✅ Пост с картинкой отправлен!")
                return
            except Exception as e:
                print(f"[BOT] Ошибка отправки фото: {e}")

        await message.answer("⚠️ Картинка не сгенерировалась, отправляю текст.")

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
    img_bytes = generate_image(prompt)
    if img_bytes:
        photo = BufferedInputFile(img_bytes, filename="image.jpg")
        await message.answer_photo(photo=photo, caption="Готово!")
    else:
        await message.answer("Не удалось сгенерировать.")

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

# ---------- Запуск ----------

async def main():
    await schedule_posts(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    asyncio.run(main())
