import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=".env")

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def score_answers_with_gpt(question, answers):
    prompt = f"Question: {question}\n\n"
    prompt += "Answers:\n"
    for i, a in enumerate(answers, 1):
        prompt += f"{i}. {a}\n"
    prompt += "\nRate each answer from 1 to 10 based on how well it answers the question. Also, choose the best one."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    return response.choices[0].message.content

question="How does JWT (JSON Web Token) authentication work in web applications?"
answers=['JWT is a token-based authentication method where a user logs in once and gets a signed token. This token is then sent with every request and validated on the server without checking the database every time.','It’s a way to avoid cookies. You encode user data into a JWT and pass it back and forth between client and server. But it can be unsafe unless you encrypt it.','JWT stands for JSON Web Token. When a user logs in, the server creates a token containing the user’s ID and signs it with a secret. The client stores it (usually in localStorage) and sends it with every request in the Authorization header. The server validates the token and grants access based on the claims inside. JWTs are useful because they’re stateless and reduce DB lookups.','I used JWTs once, but they’re confusing. You have to be careful with expiry and revocation. Otherwise, they’re okay.','You should use HTTPS with JWT or attackers can sniff your token. Also, you shouldn’t store it in localStorage — use HttpOnly cookies instead. JWTs don’t support revocation by default.','The typical flow is: user logs in → backend generates a JWT → frontend stores it → JWT is attached to requests → backend checks signature → access granted if valid. It’s good for SPAs and mobile apps because it’s stateless.']

ratings = score_answers_with_gpt(question, answers)
print(ratings)