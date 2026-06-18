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
    prompt = f"""You are a Senior QA Automation Engineer specializing in Playwright Python.

Generate a single Playwright Python test file.

Requirements:

1. Use sync_playwright
2. Create one function per test case
3. Reuse browser session
4. Add assertions for each test
5. Add screenshots on failure (use try/except)
6. Return ONLY valid Python code — no markdown, no explanations

CRITICAL LOCATOR RULES — follow this priority order:

1. If element has "id", use:  page.locator("#element_id")
2. If element has "name", use:  page.locator("[name='element_name']")
3. If element has "placeholder", use:  page.get_by_placeholder("placeholder text")
4. For links (tag="a"), use:  page.get_by_role("link", name="link text")
5. For buttons (tag="button"), use:  page.get_by_role("button", name="button text")
6. NEVER guess locators. Only use attributes provided in the elements list below.

ELEMENT TYPE RULES:

- tag="a" means it's a LINK, not a button. Use get_by_role("link", ...)
- tag="button" means it's a BUTTON. Use get_by_role("button", ...)
- tag="input" with input_type="email" means email field
- tag="input" with input_type="password" means password field
- tag="select" means dropdown. Use page.select_option()
- tag="textarea" means multiline text input
- Elements with visible="false" should be IGNORED completely
- Elements with input_type="hidden" should be IGNORED completely

Page:
{page_title}

URL:
{url}

Elements on the page (with full metadata):
{json.dumps(elements, indent=2)}

Test Cases to implement:
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
