def generate_playwright_script(
    page_title,
    page_url,
    elements
):

    script = f"""
from playwright.sync_api import Page

def test_page(page: Page):

    page.goto("{page_url}")

"""

    for element in elements:

        if element.element_type == "input":

            script += f"""
    assert page.locator("input").count() > 0
"""

        elif element.element_type == "button":

            script += f"""
    assert page.locator("button").count() > 0
"""

    return script