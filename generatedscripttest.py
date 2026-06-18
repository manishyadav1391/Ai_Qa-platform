import os
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Playwright, Browser, Page, expect, Error

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
BASE_URL = "file:///C:/qa-platform/test_pages/dashboard.html"
SCREENSHOT_DIR = Path("./screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def capture_screenshot(page: Page, test_name: str):
    """Save a screenshot with the test name and timestamp."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    path = SCREENSHOT_DIR / f"{test_name}_{timestamp}.png"
    page.screenshot(path=str(path))
    print(f"[INFO] Screenshot saved to {path}")

def run_test(test_func, page: Page):
    """Execute a test function, capture screenshot on failure."""
    test_name = test_func.__name__
    try:
        print(f"\n=== RUN {test_name} ===")
        test_func(page)
        print(f"[PASS] {test_name}")
    except AssertionError as ae:
        print(f"[FAIL] {test_name}: {ae}")
        capture_screenshot(page, test_name)
        raise
    except Error as e:
        # Playwright specific error handling
        print(f"[ERROR] {test_name}: {e}")
        capture_screenshot(page, test_name)
        raise

# ----------------------------------------------------------------------
# Test Cases
# ----------------------------------------------------------------------
def test_unauthenticated_access_redirects(page: Page):
    """
    Unauthenticated access redirects to login page.
    """
    page.goto(BASE_URL)
    # Expect the URL to contain 'login' after redirect
    expect(page).to_have_url(lambda url: "login" in url.lower())
    # Verify that login form is visible and dashboard content is not
    expect(page.locator("form#login")).to_be_visible()
    expect(page.locator("#dashboard-root")).to_have_count(0)


def test_session_timeout_forces_reauthentication(page: Page):
    """
    Session timeout forces re‑authentication.
    """
    # Assume a prior login step has already stored a session cookie
    page.goto(BASE_URL)
    # Simulate session expiration by clearing cookies
    page.context.clear_cookies()
    # Interact with a widget (placeholder selector)
    widget = page.locator("[data-test-id='widget-1']")
    widget.click()
    # Expect redirect to login with timeout message
    expect(page).to_have_url(lambda url: "login" in url.lower())
    expect(page.locator("text=Session timed out")).to_be_visible()


def test_role_based_view_hides_restricted_widgets(page: Page):
    """
    Role‑based view hides restricted widgets.
    """
    page.goto(BASE_URL)
    # Assume the user role is 'viewer' (set via localStorage for demo)
    page.evaluate("window.localStorage.setItem('userRole', 'viewer')")
    page.reload()
    # Widget that requires admin permission should not be present
    admin_widget = page.locator("[data-test-id='admin-widget']")
    expect(admin_widget).to_have_count(0)
    # Attempt direct navigation to admin widget URL should show 403 or message
    page.goto("file:///C:/qa-platform/test_pages/admin_widget.html")
    expect(page.locator("text=403")).to_be_visible()


def test_full_keyboard_navigation_across_all_dashboard_controls(page: Page):
    """
    Full keyboard navigation across all dashboard controls.
    """
    page.goto(BASE_URL)
    # Focus the body to start tabbing
    page.keyboard.press("Tab")
    # Collect focusable elements that should receive focus
    focusable = page.locator("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])")
    count = focusable.count()
    assert count > 0, "No focusable elements found on the dashboard"

    for i in range(count):
        # Ensure the element has a visible focus indicator (simplified check)
        element = focusable.nth(i)
        element.focus()
        outline = element.evaluate("el => getComputedStyle(el).outline")
        assert outline != "none" and outline != "", f"Element {i} lacks visible focus outline"

        # Activate with Enter or Space where applicable
        tag_name = element.evaluate("el => el.tagName.toLowerCase()")
        if tag_name in ["button", "a"]:
            page.keyboard.press("Enter")
        elif tag_name in ["input", "select", "textarea"]:
            # For inputs just type a character to ensure no error
            page.keyboard.type("a")
        # Give UI time to react
        page.wait_for_timeout(200)


def test_color_contrast_meets_wcag_aa(page: Page):
    """
    Color contrast meets WCAG AA for text and UI elements.
    """
    page.goto(BASE_URL)

    # Helper to compute contrast using the browser's API (simplified)
    def get_contrast(fg: str, bg: str) -> float:
        script = """
        (fg, bg) => {
            const rgb = c => c.match(/^rgb\\((\\d+), (\\d+), (\\d+)\\)$/).slice(1).map(Number);
            const [r1,g1,b1] = rgb(fg);
            const [r2,g2,b2] = rgb(bg);
            const lum = c => {
                const s = c/255;
                return s <= 0.03928 ? s/12.92 : Math.pow((s+0.055)/1.055, 2.4);
            };
            const L1 = 0.2126*lum(r1) + 0.7152*lum(g1) + 0.0722*lum(b1);
            const L2 = 0.2126*lum(r2) + 0.7152*lum(g2) + 0.0722*lum(b2);
            return (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
        }
        """
        return page.evaluate(script, fg, bg)

    # Iterate over elements that have visible text
    text_elements = page.locator("body *")
    for i in range(text_elements.count()):
        el = text_elements.nth(i)
        if not el.is_visible():
            continue
        text = el.inner_text().strip()
        if not text:
            continue
        fg = el.evaluate("el => getComputedStyle(el).color")
        bg = el.evaluate("el => getComputedStyle(el).backgroundColor")
        contrast = get_contrast(fg, bg)
        # Simple rule: assume normal text size
        assert contrast >= 4.5, f"Contrast {contrast:.2f} for '{text}' is below 4.5:1"


def test_screen_reader_announces_chart_titles_and_data_summaries(page: Page):
    """
    Screen reader announces chart titles and data summaries.
    """
    page.goto(BASE_URL)
    # Locate chart container (example selector)
    chart = page.locator("[data-test-id='sales-chart']")
    expect(chart).to_be_visible()

    # Verify ARIA attributes are present
    aria_label = chart.get_attribute("aria-label")
    assert aria_label, "Chart missing aria-label for screen readers"

    aria_desc = chart.get_attribute("aria-describedby")
    if aria_desc:
        description = page.locator(f"#{aria_desc}").inner_text()
        assert description, "ARIA description element exists but is empty"
    else:
        # Fallback: ensure role="img" and alt text
        role = chart.get_attribute("role")
        assert role == "img", "Chart should have role='img' for screen readers"
        alt = chart.get_attribute("alt")
        assert alt, "Chart missing alt text"


def test_dashboard_loads_with_maximum_allowed_widgets(page: Page):
    """
    Dashboard loads with maximum allowed widgets.
    """
    page.goto(BASE_URL)
    # Assume there is an “Add widget” button
    add_btn = page.locator("button#add-widget")
    for _ in range(12):  # maximum allowed
        add_btn.click()
        page.wait_for_timeout(200)  # wait for widget to render

    widgets = page.locator("[data-test-id^='widget-']")
    assert widgets.count() == 12, "Dashboard did not render 12 widgets"

    # Simple performance check: measure load time from start to last widget visible
    start = time.time()
    page.wait_for_selector("[data-test-id='widget-12']", timeout=3000)
    load_time = time.time() - start
    assert load_time < 3, f"Dashboard load time {load_time:.2f}s exceeds 3 s threshold"


def test_adding_widget_beyond_limit_shows_appropriate_error(page: Page):
    """
    Adding widget beyond limit shows appropriate error.
    """
    page.goto(BASE_URL)
    add_btn = page.locator("button#add-widget")
    # Fill up to limit first
    for _ in range(12):
        add_btn.click()
        page.wait_for_timeout(100)

    # Attempt to add the 13th widget
    add_btn.click()
    # Expect error toast/message
    error_msg = page.locator("text=Maximum number of widgets reached")
    expect(error_msg).to_be_visible()


def test_graceful_handling_of_api_500_error_on_widget_load(page: Page):
    """
    Graceful handling of API 500 error on widget load.
    """
    page.goto(BASE_URL)

    # Intercept the API call for a specific widget and force a 500 response
    def route_handler(route, request):
        if "widget-data" in request.url:
            route.fulfill(status=500, body='{"error":"Internal Server Error"}')
        else:
            route.continue_()

    page.route("**/api/widget-data**", route_handler)

    # Add a widget that triggers the intercepted API
    page.locator("button#add-widget").click()
    widget_error = page.locator("[data-test-id='widget-error']").filter(has_text="retry")
    expect(widget_error).to_be_visible()
    # Verify other existing widgets remain functional
    other_widgets = page.locator("[data-test-id='widget-1']")
    expect(other_widgets).to_be_visible()


def test_dashboard_state_persistence_after_browser_refresh(page: Page):
    """
    Dashboard state persistence after browser refresh.
    """
    page.goto(BASE_URL)
    # Rearrange a widget (drag‑and‑drop placeholder)
    widget = page.locator("[data-test-id='widget-1']")
    target = page.locator("[data-test-id='widget-2']")
    widget.drag_to(target)

    # Add a new widget
    page.locator("button#add-widget").click()
    new_widget = page.locator("[data-test-id='widget-13']")  # assuming next index

    # Refresh the page
    page.reload()
    # Verify that the layout order persisted (widget-1 should now be after widget-2)
    order = page.evaluate("""
        () => Array.from(document.querySelectorAll('[data-test-id^="widget-"]'))
               .map(el => el.getAttribute('data-test-id'))
    """)
    assert order.index("widget-1") > order.index("widget-2"), "Widget order did not persist after refresh"
    # Verify the newly added widget still exists
    expect(page.locator("[data-test-id='widget-13']")).to_be_visible()


# ----------------------------------------------------------------------
# Test Runner
# ----------------------------------------------------------------------
def main():
    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page: Page = context.new_page()

        # List of test functions to execute
        tests = [
            test_unauthenticated_access_redirects,
            test_session_timeout_forces_reauthentication,
            test_role_based_view_hides_restricted_widgets,
            test_full_keyboard_navigation_across_all_dashboard_controls,
            test_color_contrast_meets_wcag_aa,
            test_screen_reader_announces_chart_titles_and_data_summaries,
            test_dashboard_loads_with_maximum_allowed_widgets,
            test_adding_widget_beyond_limit_shows_appropriate_error,
            test_graceful_handling_of_api_500_error_on_widget_load,
            test_dashboard_state_persistence_after_browser_refresh,
        ]

        # Run each test while re‑using the same page (session)
        for test in tests:
            run_test(test, page)

        # Clean up
        context.close()
        browser.close()


if __name__ == "__main__":
    main()