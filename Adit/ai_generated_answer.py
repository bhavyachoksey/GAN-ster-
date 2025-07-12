import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=".env")

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def remove_html_and_emojis(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    return text.strip()

def generate_chatgpt_answer(question: str, max_sentences: int = 15, model: str = "gpt-3.5-turbo") -> str:
    prompt = f"Answer the following question clearly. No HTML tags or emojis. Limit to {max_sentences} sentences.\n\nQuestion: {question}"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        raw_text = response.choices[0].message.content
        cleaned = remove_html_and_emojis(raw_text)
        sentences = re.split(r'(?<=[.!?])\s+', cleaned)
        answer=' '.join(sentences[:max_sentences])
        return answer
    except Exception as e:
        return f"Error: {str(e)}"