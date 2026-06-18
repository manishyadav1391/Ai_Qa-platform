"""
Template-based Playwright script generator.

Generates specific locators based on element metadata instead of
generic page.locator("input").count() assertions.
"""


# Input types that should be skipped in template generation
SKIP_INPUT_TYPES = {"hidden", "submit", "reset", "image"}


def _best_locator(element) -> str:
    """
    Build the best Playwright locator expression for an element.
    Priority: #id > [name] > get_by_placeholder > get_by_role/text
    """
    tag = getattr(element, "tag_name", None) or element.element_type
    eid = getattr(element, "element_id", None) or ""
    name = element.name or ""
    placeholder = getattr(element, "placeholder", None) or ""
    text = element.text or ""

    if eid:
        return f'page.locator("#{eid}")'

    if name:
        return f'page.locator("[name=\'{name}\']")'

    if placeholder:
        return f'page.get_by_placeholder("{placeholder}")'

    if tag == "a" and text:
        return f'page.get_by_role("link", name="{text}")'

    if tag == "button" and text:
        return f'page.get_by_role("button", name="{text}")'

    if text:
        return f'page.get_by_text("{text}")'

    return f'page.locator("{tag}")'


def _generate_input_test(element, locator: str) -> str:
    """Generate test code for an input element."""
    input_type = getattr(element, "input_type", None) or "text"
    name = element.name or getattr(element, "element_id", "") or "field"

    if input_type == "email":
        return f"""
    # Test email input: {name}
    {locator}.fill("test@example.com")
    assert {locator}.input_value() == "test@example.com"
"""
    elif input_type == "password":
        return f"""
    # Test password input: {name}
    {locator}.fill("SecurePass123!")
    assert {locator}.input_value() == "SecurePass123!"
"""
    elif input_type == "number":
        return f"""
    # Test number input: {name}
    {locator}.fill("42")
    assert {locator}.input_value() == "42"
"""
    else:
        return f"""
    # Test text input: {name}
    {locator}.fill("test value")
    assert {locator}.input_value() == "test value"
"""


def _generate_button_test(element, locator: str) -> str:
    """Generate test code for a button."""
    text = element.text or element.name or "button"
    return f"""
    # Test button: {text}
    assert {locator}.is_visible()
    assert {locator}.is_enabled()
"""


def _generate_link_test(element, locator: str) -> str:
    """Generate test code for a link."""
    text = element.text or element.name or "link"
    href = getattr(element, "href", "") or ""
    code = f"""
    # Test link: {text}
    assert {locator}.is_visible()
"""
    if href and not href.startswith("#") and not href.startswith("javascript:"):
        code += f'    assert {locator}.get_attribute("href") is not None\n'
    return code


def _generate_dropdown_test(element, locator: str) -> str:
    """Generate test code for a dropdown/select."""
    name = element.name or getattr(element, "element_id", "") or "dropdown"
    return f"""
    # Test dropdown: {name}
    assert {locator}.is_visible()
    options = {locator}.locator("option").all()
    assert len(options) > 0, "Dropdown should have at least one option"
"""


def _generate_textarea_test(element, locator: str) -> str:
    """Generate test code for a textarea."""
    name = element.name or getattr(element, "element_id", "") or "textarea"
    return f"""
    # Test textarea: {name}
    {locator}.fill("Test textarea content")
    assert {locator}.input_value() == "Test textarea content"
"""


def _generate_form_test(element, locator: str) -> str:
    """Generate test code for a form."""
    name = element.name or getattr(element, "element_id", "") or "form"
    return f"""
    # Test form presence: {name}
    assert {locator}.is_visible()
"""


def _generate_table_test(element, locator: str) -> str:
    """Generate test code for a table."""
    name = element.name or getattr(element, "element_id", "") or "table"
    return f"""
    # Test table: {name}
    assert {locator}.is_visible()
    rows = {locator}.locator("tr").all()
    assert len(rows) > 0, "Table should have at least one row"
"""


def generate_playwright_script(
    page_title,
    page_url,
    elements
):
    """
    Generate a Playwright Python test script with specific locators
    based on element metadata.
    """

    script = f'''from playwright.sync_api import sync_playwright


def test_{_safe_name(page_title)}():
    """Auto-generated test for: {page_title}"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto("{page_url}", wait_until="networkidle")
            assert page.title() != "", "Page should have a title"
'''

    test_count = 0

    for element in elements:
        # Skip hidden and non-testable elements
        visible = getattr(element, "visible", "true")
        input_type = getattr(element, "input_type", None) or ""

        if visible == "false":
            continue
        if input_type in SKIP_INPUT_TYPES:
            continue

        locator = _best_locator(element)
        elem_type = element.element_type

        if elem_type == "input":
            script += _generate_input_test(element, locator)
            test_count += 1

        elif elem_type == "button":
            script += _generate_button_test(element, locator)
            test_count += 1

        elif elem_type == "link":
            script += _generate_link_test(element, locator)
            test_count += 1

        elif elem_type == "checkbox":
            name = element.name or "checkbox"
            script += f"""
    # Test checkbox: {name}
    assert {locator}.is_visible()
"""
            test_count += 1

        elif elem_type == "radio":
            name = element.name or "radio"
            script += f"""
    # Test radio: {name}
    assert {locator}.is_visible()
"""
            test_count += 1

        elif elem_type == "dropdown":
            script += _generate_dropdown_test(element, locator)
            test_count += 1

        elif elem_type == "textarea":
            script += _generate_textarea_test(element, locator)
            test_count += 1

        elif elem_type == "form":
            script += _generate_form_test(element, locator)
            test_count += 1

        elif elem_type == "table":
            script += _generate_table_test(element, locator)
            test_count += 1

    if test_count == 0:
        script += """
    # No testable elements found on this page
    print("Page loaded successfully, no interactive elements to test")
"""

    script += f"""
            print("All {test_count} element tests passed for: {page_title}")

        except Exception as e:
            page.screenshot(path="screenshots/failure_{_safe_name(page_title)}.png")
            raise e

        finally:
            browser.close()


if __name__ == "__main__":
    test_{_safe_name(page_title)}()
"""

    return script


def _safe_name(title: str) -> str:
    """Convert a page title to a valid Python function name."""
    safe = title.lower().replace(" ", "_").replace("-", "_")
    # Remove any non-alphanumeric characters except underscores
    safe = "".join(c for c in safe if c.isalnum() or c == "_")
    # Ensure it starts with a letter
    if safe and not safe[0].isalpha():
        safe = "page_" + safe
    return safe or "page_test"