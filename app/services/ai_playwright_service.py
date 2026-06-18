import os
import json
import dotenv
from ollama import Client

dotenv.load_dotenv()
client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"
    }
)


def generate_playwright_script_via_ai(
    page_title: str,
    url: str,
    elements: list,
    testcases: list
) -> str:
    prompt = f"""You are a Senior QA Automation Engineer.

Generate a single Playwright Python file.

Requirements:

1. Use sync_playwright
2. Create one function per test case
3. Reuse browser session
4. Add assertions
5. Add screenshots on failure
6. Return ONLY Python code

Page:
{page_title}

URL:
{url}

Elements:
{json.dumps(elements, indent=2)}

Test Cases:
{json.dumps(testcases, indent=2)}
"""

    response = client.chat(
        model="gpt-oss:120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response["message"]["content"]

    # Strip markdown code blocks if the model wrapped the code in ```python ... ```
    if "```python" in content:
        content = content.split("```python", 1)[1]
        content = content.split("```", 1)[0]
    elif "```" in content:
        content = content.split("```", 1)[1]
        content = content.split("```", 1)[0]

    return content.strip()
