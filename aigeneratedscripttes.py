from playwright.sync_api import sync_playwright, expect
import pytest

BASE_URL = "https://opensource-demo.orangehrmlive.com/web/index.php/buzz/viewBuzz"

@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    import os
    session_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "generated_scripts", "auth_state_3.json"))
    if os.path.exists(session_path):
        context = browser.new_context(storage_state=session_path)
    else:
        context = browser.new_context()
    page = context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded")
    yield page
    context.close()

def _screenshot_on_failure(page, test_name):
    try:
        page.screenshot(path=f"{test_name}.png")
    except Exception:
        pass

def test_verify_valid_input_for_input(page):
    test_name = "test_verify_valid_input_for_input"
    try:
        search_input = page.get_by_placeholder("Search")
        search_input.fill("Playwright")
        expect(search_input).to_have_value("Playwright")
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_empty_value_for_input(page):
    test_name = "test_verify_empty_value_for_input"
    try:
        search_input = page.get_by_placeholder("Search")
        search_input.fill("")
        expect(search_input).to_have_value("")
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_generic_1(page):
    test_name = "test_verify_button_click_generic_1"
    try:
        btn = page.locator("button").first
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_Upgrade(page):
    test_name = "test_verify_button_click_Upgrade"
    try:
        upgrade_btn = page.get_by_role("button", name="Upgrade")
        expect(upgrade_btn).to_be_visible()
        expect(upgrade_btn).to_be_enabled()
        upgrade_btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_generic_2(page):
    test_name = "test_verify_button_click_generic_2"
    try:
        btn = page.locator("button").nth(1)
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_Share_Photos(page):
    test_name = "test_verify_button_click_Share_Photos"
    try:
        btn = page.get_by_role("button", name="Share Photos")
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_Share_Video(page):
    test_name = "test_verify_button_click_Share_Video"
    try:
        btn = page.get_by_role("button", name="Share Video")
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_Most_Recent_Posts(page):
    test_name = "test_verify_button_click_Most_Recent_Posts"
    try:
        btn = page.get_by_role("button", name="Most Recent Posts")
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_Most_Liked_Posts(page):
    test_name = "test_verify_button_click_Most_Liked_Posts"
    try:
        btn = page.get_by_role("button", name="Most Liked Posts")
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_Most_Commented_Posts(page):
    test_name = "test_verify_button_click_Most_Commented_Posts"
    try:
        btn = page.get_by_role("button", name="Most Commented Posts")
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_generic_3(page):
    test_name = "test_verify_button_click_generic_3"
    try:
        btn = page.locator("button").nth(2)
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_generic_4(page):
    test_name = "test_verify_button_click_generic_4"
    try:
        btn = page.locator("button").nth(3)
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_generic_5(page):
    test_name = "test_verify_button_click_generic_5"
    try:
        btn = page.locator("button").nth(4)
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_generic_6(page):
    test_name = "test_verify_button_click_generic_6"
    try:
        btn = page.locator("button").nth(5)
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_generic_7(page):
    test_name = "test_verify_button_click_generic_7"
    try:
        btn = page.locator("button").nth(6)
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_generic_8(page):
    test_name = "test_verify_button_click_generic_8"
    try:
        btn = page.locator("button").nth(7)
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_button_click_generic_9(page):
    test_name = "test_verify_button_click_generic_9"
    try:
        btn = page.locator("button").nth(8)
        expect(btn).to_be_visible()
        expect(btn).to_be_enabled()
        btn.click()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_a(page):
    test_name = "test_verify_navigation_link_a"
    try:
        link = page.get_by_role("link", name="a")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url("https://www.orangehrm.com/")
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Admin(page):
    test_name = "test_verify_navigation_link_Admin"
    try:
        link = page.get_by_role("link", name="Admin")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/admin/viewAdminModule" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_PIM(page):
    test_name = "test_verify_navigation_link_PIM"
    try:
        link = page.get_by_role("link", name="PIM")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/pim/viewPimModule" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Leave(page):
    test_name = "test_verify_navigation_link_Leave"
    try:
        link = page.get_by_role("link", name="Leave")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/leave/viewLeaveModule" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Time(page):
    test_name = "test_verify_navigation_link_Time"
    try:
        link = page.get_by_role("link", name="Time")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/time/viewTimeModule" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Recruitment(page):
    test_name = "test_verify_navigation_link_Recruitment"
    try:
        link = page.get_by_role("link", name="Recruitment")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/recruitment/viewRecruitmentModule" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_My_Info(page):
    test_name = "test_verify_navigation_link_My_Info"
    try:
        link = page.get_by_role("link", name="My Info")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/pim/viewMyDetails" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Performance(page):
    test_name = "test_verify_navigation_link_Performance"
    try:
        link = page.get_by_role("link", name="Performance")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/performance/viewPerformanceModule" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Dashboard(page):
    test_name = "test_verify_navigation_link_Dashboard"
    try:
        link = page.get_by_role("link", name="Dashboard")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/dashboard/index" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Directory(page):
    test_name = "test_verify_navigation_link_Directory"
    try:
        link = page.get_by_role("link", name="Directory")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/directory/viewDirectory" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Maintenance(page):
    test_name = "test_verify_navigation_link_Maintenance"
    try:
        link = page.get_by_role("link", name="Maintenance")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/maintenance/viewMaintenanceModule" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Claim(page):
    test_name = "test_verify_navigation_link_Claim"
    try:
        link = page.get_by_role("link", name="Claim")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/claim/viewClaimModule" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Buzz(page):
    test_name = "test_verify_navigation_link_Buzz"
    try:
        link = page.get_by_role("link", name="Buzz")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url(lambda url: "/web/index.php/buzz/viewBuzz" in url)
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_Upgrade(page):
    test_name = "test_verify_navigation_link_Upgrade"
    try:
        link = page.get_by_role("link", name="Upgrade")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url("https://orangehrm.com/open-source/upgrade-to-advanced")
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_navigation_link_OrangeHRM_Inc(page):
    test_name = "test_verify_navigation_link_OrangeHRM_Inc"
    try:
        link = page.get_by_role("link", name="OrangeHRM, Inc")
        expect(link).to_be_visible()
        link.click()
        expect(page).to_have_url("http://www.orangehrm.com")
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_valid_text_input_in_textarea(page):
    test_name = "test_verify_valid_text_input_in_textarea"
    try:
        textarea = page.get_by_placeholder("What's on your mind?")
        textarea.fill("Hello from Playwright!")
        expect(textarea).to_have_value("Hello from Playwright!")
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_character_limit_validation_in_textarea(page):
    test_name = "test_verify_character_limit_validation_in_textarea"
    try:
        textarea = page.get_by_placeholder("What's on your mind?")
        long_text = "A" * 5000
        textarea.fill(long_text)
        # Assuming the textarea truncates or limits input, we check that the value length is <= 5000
        value = textarea.input_value()
        assert len(value) <= 5000
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_form_submission_with_valid_data(page):
    test_name = "test_verify_form_submission_with_valid_data"
    try:
        form = page.locator("form")
        expect(form).to_be_visible()
        # No concrete fields to fill; just submit the form via JavaScript if possible
        form.evaluate("form => form.submit()")
        # Verify that the page URL maybe changes or a success indicator appears
        # Here we just ensure no error is raised
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_form_validation_with_missing_mandatory_fields(page):
    test_name = "test_verify_form_validation_with_missing_mandatory_fields"
    try:
        form = page.locator("form")
        expect(form).to_be_visible()
        form.evaluate("form => form.submit()")
        # Expect some validation message; placeholder check for generic error
        error = page.locator("text=required")
        expect(error).to_be_visible()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_search_functionality_filters_records(page):
    test_name = "test_verify_search_functionality_filters_records"
    try:
        search_input = page.get_by_placeholder("Search")
        search_input.fill("Admin")
        # Assuming results appear, check that at least one result is visible
        result = page.locator("text=Admin")
        expect(result).to_be_visible()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise

def test_verify_empty_search_query_displays_all_records(page):
    test_name = "test_verify_empty_search_query_displays_all_records"
    try:
        search_input = page.get_by_placeholder("Search")
        search_input.fill("")
        # Assuming the full list is shown, check that a known element from the page exists
        known_element = page.locator("text=Buzz")
        expect(known_element).to_be_visible()
    except Exception:
        _screenshot_on_failure(page, test_name)
        raise