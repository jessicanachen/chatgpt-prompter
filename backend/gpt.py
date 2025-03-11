import requests
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def format_prompt_with_gpt(raw_prompt):
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "Reformat this prompt clearly and concisely."},
                {"role": "user", "content": raw_prompt}
            ]
        }
    )
    return response.json()['choices'][0]['message']['content']

def send_prompt_to_gpt(messages):
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": "gpt-4",
            "messages": messages
        }
    )
    return response.json()['choices'][0]['message']['content']
