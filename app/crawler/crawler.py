from playwright.sync_api import sync_playwright
from app.crawler.page_scanner import extract_elements, extract_features, extract_links


def scan_page(url: str):

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        response = page.goto(
            url,
            wait_until="networkidle"
        )

        title = page.title()

        current_url = page.url
        elements = extract_elements(page)
        features = extract_features(page)
        links = extract_links(page)

        browser.close()

        return {
            "title": title,
            "url": current_url,
            "status_code": response.status if response else None,
            "elements": elements,
            "features": features,
            "links": links
        }