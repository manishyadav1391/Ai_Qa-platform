import os
import sys
import traceback
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Directory for failure screenshots
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def capture_screenshot(page, test_name):
    """Save a screenshot for the given test."""
    path = os.path.join(SCREENSHOT_DIR, f"{test_name}.png")
    page.screenshot(path=path)
    print(f"[INFO] Screenshot saved: {path}")


def test_select_dropdown_status(page):
    """
    Verify selecting options in dropdown status
    Expected: Dropdown displays selected option
    """
    try:
        # Assuming the dropdown is a <select> element with name="status"
        dropdown = page.locator('select[name="status"]')
        dropdown.wait_for(state="visible", timeout=5000)

        # Grab all options, pick the first non‑placeholder option
        options = dropdown.locator('option')
        count = options.count()
        assert count > 1, "Dropdown should contain at least one selectable option"

        # Select the second option (index 1) – adjust if a placeholder exists
        option_value = options.nth(1).get_attribute("value")
        dropdown.select_option(value=option_value)

        # Assertion: the selected value should match what we chose
        selected = dropdown.input_value()
        assert selected == option_value, f"Expected selected value '{option_value}', got '{selected}'"
        print("[PASS] test_select_dropdown_status")
    except Exception as e:
        capture_screenshot(page, "test_select_dropdown_status")
        print("[FAIL] test_select_dropdown_status")
        raise e


def test_form_submission_valid(page):
    """
    Verify form submission with valid data for form order-form
    Expected: Form submitted successfully
    """
    try:
        form = page.locator('#order-form')
        form.wait_for(state="visible", timeout=5000)

        # Fill typical fields – adjust selectors as per actual form fields
        form.locator('input[name="customer"]').fill("John Doe")
        form.locator('textarea[name="description"]').fill("Test order description.")
        # Assume there is a submit button inside the form
        form.locator('button[type="submit"], input[type="submit"]').click()

        # Success message – adapt selector to actual implementation
        success_msg = page.locator('.toast-success, .alert-success')
        success_msg.wait_for(state="visible", timeout=5000)
        assert success_msg.is_visible(), "Success message should be visible after form submission"
        print("[PASS] test_form_submission_valid")
    except Exception as e:
        capture_screenshot(page, "test_form_submission_valid")
        print("[FAIL] test_form_submission_valid")
        raise e


def test_form_validation_missing_fields(page):
    """
    Verify form validation with missing mandatory fields in form order-form
    Expected: Error message displayed for missing fields
    """
    try:
        form = page.locator('#order-form')
        form.wait_for(state="visible", timeout=5000)

        # Clear any pre‑filled data (ensure required fields are empty)
        form.locator('input[name="customer"]').fill("")
        form.locator('textarea[name="description"]').fill("")
        form.locator('button[type="submit"], input[type="submit"]').click()

        # Look for validation error – generic selector, may need tuning
        error_msg = page.locator('.error, .validation-error, .alert-danger')
        error_msg.wait_for(state="visible", timeout=5000)
        assert error_msg.is_visible(), "Error message should appear when required fields are missing"
        print("[PASS] test_form_validation_missing_fields")
    except Exception as e:
        capture_screenshot(page, "test_form_validation_missing_fields")
        print("[FAIL] test_form_validation_missing_fields")
        raise e


def test_table_loading_rows(page):
    """
    Verify table loading and row rendering in table element
    Expected: Table displays records correctly
    """
    try:
        # Assuming the table has a <tbody> with rows
        table_body = page.locator('table tbody')
        table_body.wait_for(state="visible", timeout=5000)

        rows = table_body.locator('tr')
        row_count = rows.count()
        assert row_count > 0, "Table should contain at least one data row"

        # Optional: validate that each row has expected number of cells
        first_row_cells = rows.nth(0).locator('td')
        cell_count = first_row_cells.count()
        assert cell_count > 0, "Rows should contain cells"
        print(f"[PASS] test_table_loading_rows – {row_count} rows found")
    except Exception as e:
        capture_screenshot(page, "test_table_loading_rows")
        print("[FAIL] test_table_loading_rows")
        raise e


def test_textarea_valid_input(page):
    """
    Verify valid text input in textarea description
    Expected: Text is accepted and stored correctly
    """
    try:
        textarea = page.locator('textarea[name="description"]')
        textarea.wait_for(state="visible", timeout=5000)

        sample_text = "This is a valid description for the order."
        textarea.fill(sample_text)

        # Blur to trigger possible internal storage
        textarea.press("Tab")

        # Verify the value remains unchanged
        current_value = textarea.input_value()
        assert current_value == sample_text, "Textarea should retain the entered valid text"
        print("[PASS] test_textarea_valid_input")
    except Exception as e:
        capture_screenshot(page, "test_textarea_valid_input")
        print("[FAIL] test_textarea_valid_input")
        raise e


def test_textarea_character_limit(page):
    """
    Verify character limit validation in textarea description
    Expected: Warning shown or input truncated
    """
    try:
        textarea = page.locator('textarea[name="description"]')
        textarea.wait_for(state="visible", timeout=5000)

        # Determine the maxlength attribute if present
        maxlength_attr = textarea.get_attribute("maxlength")
        if maxlength_attr:
            max_len = int(maxlength_attr)
        else:
            # Fallback guess if maxlength not defined – use 200 as typical limit
            max_len = 200

        long_text = "A" * (max_len + 50)  # exceed limit by 50 chars
        textarea.fill(long_text)

        # Some implementations truncate automatically; others show a warning.
        current_value = textarea.input_value()
        if len(current_value) > max_len:
            # Expect a warning element to appear
            warning = page.locator('.char-limit-warning, .validation-warning')
            warning.wait_for(state="visible", timeout=5000)
            assert warning.is_visible(), "Warning should be displayed when text exceeds limit"
        else:
            # Verify truncation
            assert len(current_value) == max_len, "Textarea should truncate input to maxlength"
        print("[PASS] test_textarea_character_limit")
    except Exception as e:
        capture_screenshot(page, "test_textarea_character_limit")
        print("[FAIL] test_textarea_character_limit")
        raise e


def test_table_sorting(page):
    """
    Verify table headers sorting (ascending/descending)
    Expected: Table rows sort according to column header
    """
    try:
        # Assume the first column header is sortable
        header = page.locator('table thead th').first
        header.wait_for(state="visible", timeout=5000)

        # Capture first column values before sorting
        def get_first_column_values():
            rows = page.locator('table tbody tr')
            values = []
            for i in range(rows.count()):
                cell = rows.nth(i).locator('td').first
                values.append(cell.inner_text().strip())
            return values

        before = get_first_column_values()
        assert before, "Table must have rows to test sorting"

        # Click to sort ascending
        header.click()
        page.wait_for_timeout(500)  # small wait for UI to update
        after_asc = get_first_column_values()
        assert after_asc != before, "Sorting should change row order"

        # Verify ascending order (simple numeric or alphabetic check)
        assert after_asc == sorted(after_asc), "Rows should be sorted in ascending order after first click"

        # Click again to sort descending
        header.click()
        page.wait_for_timeout(500)
        after_desc = get_first_column_values()
        assert after_desc == sorted(after_desc, reverse=True), "Rows should be sorted in descending order after second click"
        print("[PASS] test_table_sorting")
    except Exception as e:
        capture_screenshot(page, "test_table_sorting")
        print("[FAIL] test_table_sorting")
        raise e


def main():
    url = "file:///C:/qa-platform/test_pages/orders.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)   # set headless=True for CI
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)

        # List of test callables preserving order
        tests = [
            test_select_dropdown_status,
            test_form_submission_valid,
            test_form_validation_missing_fields,
            test_table_loading_rows,
            test_textarea_valid_input,
            test_textarea_character_limit,
            test_table_sorting,
        ]

        # Execute each test, continue on failure to collect all screenshots
        for test in tests:
            try:
                test(page)
            except Exception:
                # Log traceback but keep running subsequent tests
                traceback.print_exc()
                continue

        # Cleanup
        context.close()
        browser.close()


if __name__ == "__main__":
    main()