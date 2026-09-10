@dp.message(Command("test_post"))
async def test_post_cmd(message: Message):
    await message.answer("⏳ Генерирую пост...")
    post = generate_post()
    clean_post = post.replace("[IMAGE]", "").strip()

    needs_image = should_add_image(post)
    print(f"[BOT] should_add_image = {needs_image}")

    if needs_image:
        await message.answer("🎨 Генерирую картинку (это может занять до 30 секунд)...")
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
