import os
import dotenv

import json

from ollama import Client
dotenv.load_dotenv()
client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"
    }
)


def generate_ai_testcases(
    page_name: str,
    elements: list,
    existing_testcases: list
):

    prompt = f"""
You are a Senior QA Automation Architect.

Page Name:
{page_name}

Elements (with full metadata — use "tag", "input_type", "placeholder" to generate smarter tests):
{json.dumps(elements, indent=2)}

Existing Test Cases:
{json.dumps(existing_testcases, indent=2)}

Generate ONLY additional test cases.

Rules:
1. Do not duplicate existing tests.
2. Use element metadata intelligently:
   - For input_type="email": generate email format validation tests
   - For input_type="password": generate password masking and strength tests
   - For input_type="number": generate numeric boundary tests
   - For tag="a" (links): generate navigation and URL tests
   - For tag="select" (dropdowns): generate option selection tests
   - For required="true": generate mandatory field validation tests
3. Focus on:
   - Security
   - Accessibility
   - Boundary Testing
   - Edge Cases
   - Workflow Validation
4. Return JSON ONLY.
5. Maximum 10 test cases.

Format:

[
  {{
    "title": "...",
    "category": "...",
    "priority": "...",
    "expected_result": "..."
  }}
]
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

    try:
        return json.loads(content)
    except Exception:
        print(content)
        return []