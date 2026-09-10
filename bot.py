import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from scheduler import schedule_posts, publish_post
from generator import generate_post, generate_image, get_post_history, should_add_image, extract_image_prompt
from config import BOT_TOKEN, CHANNEL_ID, PORT

app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---- Обработка комментариев ----
@dp.channel_post()
async def on_channel_post(message: types.Message):
    """Срабатывает на каждое новое сообщение в канале (включая комментарии)"""
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

# ---- Команды бота ----
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "🤖 Я AI-администратор канала @ainavigatorErgo\n\n"
        "Доступные команды:\n"
        "/test_post – сгенерировать и отправить пост\n"
        "/post <текст> – отправить свой пост\n"
        "/image <промпт> – сгенерировать картинку\n"
        "/stats – статистика последних постов\n"
        "/analyze – анализ конкурентов\n"
        "/help – это сообщение"
    )

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await start_cmd(message)

@dp.message(Command("test_post"))
async def test_post_cmd(message: Message):
    await message.answer("⏳ Генерирую пост...")
    post = generate_post()
    clean_post = post.replace("[IMAGE]", "").strip()

    if should_add_image(post):
        await message.answer("🎨 Генерирую картинку...")
        prompt = extract_image_prompt(clean_post)
        image_url = generate_image(prompt)
        if image_url:
            # Лимит Telegram: 1024 символа для caption
            if len(clean_post) <= 1024:
                try:
                    await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=clean_post)
                    await message.answer("✅ Пост с картинкой отправлен в канал!")
                    return
                except Exception as e:
                    print(f"Ошибка send_photo (caption): {e}")
                    await message.answer(f"⚠️ Фото с подписью не ушло: {e}")
            # Если текст длиннее 1024 — отправляем фото и текст отдельно
            try:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url)
                await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
                await message.answer("✅ Фото и текст отправлены отдельными сообщениями!")
                return
            except Exception as e:
                print(f"Ошибка send_photo (отдельно): {e}")
                await message.answer(f"⚠️ Фото не ушло: {e}")

    await bot.send_message(chat_id=CHANNEL_ID, text=clean_post)
    await message.answer("✅ Текстовый пост отправлен в канал!")

@dp.message(Command("post"))
async def custom_post_cmd(message: Message):
    text = message.text.replace("/post", "", 1).strip()
    if not text:
        await message.answer("Напиши текст после /post")
        return
    await bot.send_message(chat_id=CHANNEL_ID, text=text)
    await message.answer("✅ Ваш пост опубликован!")

@dp.message(Command("image"))
async def image_cmd(message: Message):
    prompt = message.text.replace("/image", "", 1).strip()
    if not prompt:
        await message.answer("Напиши промпт после /image")
        return
    await message.answer("🎨 Генерирую картинку...")
    url = generate_image(prompt)
    if url:
        try:
            await message.answer_photo(photo=url, caption="Готово!")
        except Exception as e:
            await message.answer(f"Ссылка на картинку: {url}\n(Не удалось отобразить: {e})")
    else:
        await message.answer("Не удалось сгенерировать картинку. Проверь баланс provod.ai.")

@dp.message(Command("stats"))
async def stats_cmd(message: Message):
    history = get_post_history()
    if not history:
        await message.answer("Нет данных по постам.")
        return
    stats_text = "📊 Статистика последних 5 постов:\n\n"
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
            await message.answer("📌 Темы для постов:\n" + "\n".join(f"- {t}" for t in topics))
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
