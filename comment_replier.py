from openai import OpenAI
from config import PROVOD_API_KEY, MODEL_NAME

client = OpenAI(api_key=PROVOD_API_KEY, base_url="https://api.provod.ai/v1")

def generate_reply(comment_text, post_text=None):
    """Генерирует ответ на комментарий с учётом контекста поста"""
    system_prompt = (
        "Ты — вежливый и полезный ассистент канала «AI-навигатор». "
        "Отвечай на комментарии кратко, дружелюбно, по делу. "
        "Если вопрос требует развёрнутого ответа — дай его, но не более 2–3 предложений. "
        "Избегай кликбейта и обещаний, которые нельзя выполнить."
    )
    context = f"Пост: {post_text[:200]}..." if post_text else ""
    user_prompt = f"{context}\n\nКомментарий: {comment_text}\n\nТвой ответ:"
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка генерации ответа: {e}")
        return None
