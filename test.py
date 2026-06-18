
import dotenv

import os
from ollama import Client
dotenv.load_dotenv()
client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"
    }
)

response = client.chat(
    model="gpt-oss:120b",
    messages=[
        {
            "role": "user",
            "content": "Say Hello"
        }
    ]
)

print(response["message"]["content"])