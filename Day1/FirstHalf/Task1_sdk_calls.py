from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in .env file")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)
MODEL = "openrouter/free"

def ask_openrouter(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )
    answer = response.choices[0].message.content
    print("Model Name:", response.model)
    print("Answer:")
    print(answer)
    print("Token Usage:")
    print("Prompt Tokens:", response.usage.prompt_tokens)
    print("Completion Tokens:", response.usage.completion_tokens)
    print("Total Tokens:", response.usage.total_tokens)
    return answer
questions = [
    "What is machine learning?",
    "Explain Python programming in simple words.",
    "What is generative AI and how does it work?"
]
for i, question in enumerate(questions, start=1):
    print(f"QUESTION {i}")
    print("Question:", question)
    ask_openrouter(question)
