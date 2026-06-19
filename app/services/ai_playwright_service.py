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
    testcases: list,
    project_id: int = None
) -> str:
    session_file_name = f"auth_state_{project_id}.json" if project_id else "auth_state_none.json"
    prompt = f"""You are a Senior QA Automation Engineer specializing in Playwright Python.

Generate a single, self-contained Playwright Python test file that runs with pytest.

STRICT STRUCTURAL RULES:

1. Import: `from playwright.sync_api import sync_playwright, expect`
2. Define a BASE_URL variable at the top: `BASE_URL = "{url}"`
3. Create a pytest fixture that launches a browser with `headless=False` and navigates to BASE_URL:
   ```
   import pytest
   import os
   from playwright.sync_api import sync_playwright, expect

   BASE_URL = "{url}"

   @pytest.fixture(scope="module")
   def browser():
       with sync_playwright() as p:
           browser = p.chromium.launch(headless=False)
           yield browser
           browser.close()

   @pytest.fixture
   def page(browser):
       # Load auth session if exists
       session_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "{session_file_name}"))
       if os.path.exists(session_path):
           context = browser.new_context(storage_state=session_path)
       else:
           context = browser.new_context()
       page = context.new_page()
       page.goto(BASE_URL, wait_until="domcontentloaded")
       yield page
       context.close()
   ```
4. Each test function MUST accept `page` as a parameter (from the fixture)
5. Each test function MUST start with `test_`
6. Wrap each test body in try/except for screenshot-on-failure
7. Return ONLY valid Python code — no markdown, no explanations, no ```python blocks

CRITICAL LOCATOR RULES — follow this EXACT priority order:

1. If element has a non-empty "id" field, use:  page.locator("#<id>")
2. If element has a non-empty "name" field, use:  page.locator("[name='<name>']")
3. If element has a non-empty "placeholder" field, use:  page.get_by_placeholder("<placeholder>")
4. For links (tag="a") with non-empty "text", use:  page.get_by_role("link", name="<text>")
5. For buttons (tag="button") with non-empty "text", use:  page.get_by_role("button", name="<text>")
6. NEVER invent selectors. ONLY use attributes that exist in the elements list below.
7. If multiple links/buttons have the same text, use .first or .nth(index)

ELEMENT TYPE RULES:

- tag="a" → LINK. Use get_by_role("link", ...) or locator("#id")
- tag="button" → BUTTON. Use get_by_role("button", ...) or locator("#id")
- tag="input" with input_type="email" → Use .fill() with a valid email
- tag="input" with input_type="password" → Use .fill() with a password string
- tag="input" with input_type="text" → Use .fill() with text
- tag="select" → DROPDOWN. Use page.select_option()
- tag="textarea" → MULTILINE input. Use .fill()
- Elements with visible="false" → SKIP entirely
- Elements with input_type="hidden" → SKIP entirely

ASSERTION RULES:

- For input fills: assert the .input_value() matches what you typed
- For link clicks: use expect(page).to_have_url() or assert page.url contains the target
- For button clicks: assert .is_visible() and .is_enabled() before clicking
- For form submissions: fill required fields first, then submit
- For checkboxes: use .check() and assert .is_checked()
- Use try/except with page.screenshot(path="test_name.png") on failure

Page Title:
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
