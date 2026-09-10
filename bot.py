import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from scheduler import schedule_posts
from generator import generate_post, generate_image, get_post_history, should_add_image, extract_image_prompt
from config import BOT_TOKEN, CHANNEL_ID, PORT

app = Flask(__name__)

@app.route('/')
def index():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.channel_post()
async def on_channel_post(msg: types.Message):
    if msg.reply_to_message:
        text = msg.text or msg.caption or ""
        if not text: return
        orig = msg.reply_to_message.text or msg.reply_to_message.caption or ""
        try:
            from comment_replier import generate_reply
            reply = generate_reply(text, orig)
            if reply: await msg.reply(reply)
        except Exception as e:
            print(f"Ошибка ответа: {e}")

@dp.message(Command("start"))
async def start_cmd(m: Message):
    await m.answer("🤖 AI-администратор канала.\n/test_post — сгенерировать и отправить пост\n/stats — статистика\n/image <промпт> — картинка")

@dp.message(Command("test_post"))
async def test_post(m: Message):
    await m.answer("⏳ Генерирую...")
    post = generate_post()
    clean = post.replace("[IMAGE]", "").strip()
    if should_add_image(post):
        await m.answer("🎨 Генерирую картинку...")
        img = generate_image(extract_image_prompt(clean))
        if img:
            photo = BufferedInputFile(img, filename="image.jpg")
            if len(clean) <= 1024:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=clean)
            else:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=photo)
                await bot.send_message(chat_id=CHANNEL_ID, text=clean)
            await m.answer("✅ Пост с картинкой отправлен!")
            return
        await m.answer("⚠️ Картинка не сгенерировалась, отправляю текст.")
    await bot.send_message(chat_id=CHANNEL_ID, text=clean)
    await m.answer("✅ Текстовый пост отправлен.")

@dp.message(Command("image"))
async def image_cmd(m: Message):
    prompt = m.text.replace("/image", "", 1).strip()
    if not prompt:
        await m.answer("Напиши промпт после /image")
        return
    await m.answer("🎨 Генерирую...")
    img = generate_image(prompt)
    if img:
        photo = BufferedInputFile(img, filename="image.jpg")
        await m.answer_photo(photo=photo, caption="Готово!")
    else:
        await m.answer("Не удалось.")

@dp.message(Command("stats"))
async def stats_cmd(m: Message):
    h = get_post_history()
    if not h:
        await m.answer("Нет данных.")
        return
    txt = "📊 Последние 5 постов:\n\n" + "\n".join(f"{i}. {p['text'][:60]}..." for i, p in enumerate(h[-5:], 1))
    await m.answer(txt)

async def main():
    await schedule_posts(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(main())
