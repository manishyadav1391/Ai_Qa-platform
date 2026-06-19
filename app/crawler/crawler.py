"""
Single page scanner — reuses an existing browser when provided,
falls back to launching its own if not.
"""
from playwright.sync_api import sync_playwright, Browser
from app.crawler.page_scanner import extract_elements, extract_features, extract_links


def scan_page(url: str, browser: Browser = None, storage_state: dict = None, timeout: int = 30000, context = None):
    """
    Scan a single page and return its metadata.

    Args:
        url: The URL to scan.
        browser: An existing Playwright browser instance to reuse.
                 If None, a new browser is launched and closed after.
        storage_state: Optional Playwright storage state dict (cookies + localStorage).
                       When provided, the browser context is created with this state,
                       enabling authenticated page access.
        timeout: Page navigation timeout in milliseconds (default 30s).
        context: An existing Playwright BrowserContext to reuse. If provided,
                 browser and storage_state are ignored and context is reused.
    """
    owns_browser = browser is None and context is None
    owns_context = context is None

    if owns_browser:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)

    try:
        if owns_context:
            # Create context with or without auth session
            if storage_state:
                context = browser.new_context(storage_state=storage_state)
            else:
                context = browser.new_context()

        page = context.new_page()
        page.set_default_timeout(timeout)
        page.set_default_navigation_timeout(timeout)

        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=timeout
        )

        # Wait a short time for JS to render, but don't wait for networkidle
        # which can hang on pages with persistent connections
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass  # Acceptable — page loaded enough

        title = page.title()
        current_url = page.url
        elements = extract_elements(page)
        features = extract_features(page)
        links = extract_links(page)

        page.close()
        if owns_context:
            context.close()

        return {
            "title": title,
            "url": current_url,
            "status_code": response.status if response else None,
            "elements": elements,
            "features": features,
            "links": links
        }

    finally:
        if owns_browser:
            browser.close()
            pw.stop()