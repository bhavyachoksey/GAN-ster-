import os
import re
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

# Optional OpenAI dependency
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.startswith("sk-"):
        # Initialize OpenAI client with minimal configuration
        client = OpenAI(
            api_key=api_key,
            timeout=30.0,
            max_retries=2
        )
        AI_AVAILABLE = True
    else:
        print("OpenAI API key not found or invalid")
        AI_AVAILABLE = False
        client = None
except ImportError as e:
    print(f"OpenAI dependency not available: {e}")
    print("Using fallback answer generation...")
    AI_AVAILABLE = False
    client = None
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Using fallback answer generation...")
    AI_AVAILABLE = False
    client = None

def remove_html_and_emojis(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    return text.strip()

def generate_chatgpt_answer(question: str, max_sentences: int = 15, model: str = "gpt-3.5-turbo") -> str:
    if not AI_AVAILABLE:
        return "AI answer generation is not available. Please provide your own answer."
    
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