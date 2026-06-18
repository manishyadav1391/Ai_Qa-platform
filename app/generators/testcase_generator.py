"""
Test case generator — creates test case definitions from element metadata.

Skips hidden/non-testable elements and generates smarter test cases
based on input_type (email validation, password masking, etc.).
"""

# Input types that should NOT generate test cases
SKIP_INPUT_TYPES = {"hidden", "submit", "reset", "image"}


def generate_for_element(element):

    testcases = []

    # Skip hidden and non-testable elements
    visible = getattr(element, "visible", "true")
    input_type = getattr(element, "input_type", None) or ""

    if visible == "false":
        return []
    if input_type in SKIP_INPUT_TYPES:
        return []

    element_type = element.element_type
    name = element.name or getattr(element, "element_id", "") or element.locator or "element"

    if element_type == "input":
        # Base input tests
        testcases.extend([
            {
                "title": f"Verify valid input for {name}",
                "category": "Positive",
                "priority": "High",
                "expected": "Input accepted"
            },
            {
                "title": f"Verify empty value for {name}",
                "category": "Negative",
                "priority": "High",
                "expected": "Validation shown"
            }
        ])

        # Input-type-specific tests
        if input_type == "email":
            testcases.extend([
                {
                    "title": f"Verify email validation rejects invalid format for {name}",
                    "category": "Negative",
                    "priority": "High",
                    "expected": "Error message shown for invalid email"
                },
                {
                    "title": f"Verify email field accepts valid email for {name}",
                    "category": "Positive",
                    "priority": "High",
                    "expected": "Email accepted without error"
                }
            ])
        elif input_type == "password":
            testcases.extend([
                {
                    "title": f"Verify password masking for {name}",
                    "category": "Security",
                    "priority": "High",
                    "expected": "Password characters are masked"
                },
                {
                    "title": f"Verify password minimum length for {name}",
                    "category": "Negative",
                    "priority": "Medium",
                    "expected": "Error shown for too-short password"
                }
            ])
        elif input_type == "number":
            testcases.extend([
                {
                    "title": f"Verify only numeric input accepted for {name}",
                    "category": "Negative",
                    "priority": "Medium",
                    "expected": "Non-numeric input is rejected"
                },
                {
                    "title": f"Verify boundary values for {name}",
                    "category": "Boundary",
                    "priority": "Medium",
                    "expected": "Min/max boundaries are enforced"
                }
            ])
        elif input_type == "tel":
            testcases.append({
                "title": f"Verify phone number format validation for {name}",
                "category": "Negative",
                "priority": "Medium",
                "expected": "Invalid phone format is rejected"
            })
        elif input_type == "url":
            testcases.append({
                "title": f"Verify URL format validation for {name}",
                "category": "Negative",
                "priority": "Medium",
                "expected": "Invalid URL format is rejected"
            })

        # Required field test
        required = getattr(element, "required", "false")
        if required == "true":
            testcases.append({
                "title": f"Verify mandatory field validation for {name}",
                "category": "Negative",
                "priority": "High",
                "expected": "Error shown when required field is empty"
            })

    elif element_type == "button":
        button_text = element.text or name or "button"
        testcases.append({
            "title": f"Verify button click {button_text}",
            "category": "Functional",
            "priority": "Medium",
            "expected": "Action executed"
        })

    elif element_type == "link":
        link_text = element.text or name or "link"
        href = getattr(element, "href", "") or ""
        testcases.append({
            "title": f"Verify navigation link '{link_text}' works",
            "category": "Functional",
            "priority": "Medium",
            "expected": f"User navigates to {href or 'target page'}"
        })

    elif element_type == "checkbox":
        testcases.extend([
            {
                "title": f"Verify checking checkbox {name}",
                "category": "Functional",
                "priority": "Medium",
                "expected": "Checkbox is checked"
            },
            {
                "title": f"Verify unchecking checkbox {name}",
                "category": "Functional",
                "priority": "Medium",
                "expected": "Checkbox is unchecked"
            }
        ])

    elif element_type == "radio":
        testcases.append({
            "title": f"Verify selecting radio option {name}",
            "category": "Functional",
            "priority": "Medium",
            "expected": "Radio option is selected and others are deselected"
        })

    elif element_type == "textarea":
        testcases.extend([
            {
                "title": f"Verify valid text input in textarea {name}",
                "category": "Positive",
                "priority": "Medium",
                "expected": "Text is accepted and stored correctly"
            },
            {
                "title": f"Verify character limit validation in textarea {name}",
                "category": "Negative",
                "priority": "Low",
                "expected": "Warning shown or input truncated"
            }
        ])

    elif element_type in ("dropdown", "select", "dropdowns"):
        testcases.append({
            "title": f"Verify selecting options in dropdown {name}",
            "category": "Functional",
            "priority": "Medium",
            "expected": "Dropdown displays selected option"
        })

    elif element_type == "form":
        testcases.extend([
            {
                "title": f"Verify form submission with valid data for form {name}",
                "category": "Positive",
                "priority": "High",
                "expected": "Form submitted successfully"
            },
            {
                "title": f"Verify form validation with missing mandatory fields in form {name}",
                "category": "Negative",
                "priority": "High",
                "expected": "Error message displayed for missing fields"
            }
        ])

    elif element_type == "table":
        testcases.extend([
            {
                "title": f"Verify table loading and row rendering in table {name}",
                "category": "Functional",
                "priority": "Medium",
                "expected": "Table displays records correctly"
            }
        ])

    return testcases



def generate_page_testcases(elements):

    all_cases = []

    for element in elements:

        all_cases.extend(
            generate_for_element(element)
        )

    return all_cases


def generate_feature_testcases(features):
    testcases = []
    feature_dict = {}
    for f in features:
        try:
            val = int(f.feature_value)
        except ValueError:
            val = f.feature_value
        feature_dict[f.feature_type] = val

    if feature_dict.get("search", 0) > 0:
        testcases.extend([
            {
                "title": "Verify search functionality filters records correctly",
                "category": "Functional",
                "priority": "High",
                "expected": "Filtered results match search query"
            },
            {
                "title": "Verify empty search query displays all records",
                "category": "Functional",
                "priority": "Medium",
                "expected": "Full list of records is displayed"
            }
        ])

    if feature_dict.get("pagination", 0) > 0:
        testcases.extend([
            {
                "title": "Verify table pagination navigation (Next, Prev, page numbers)",
                "category": "Functional",
                "priority": "Medium",
                "expected": "Correct page subset of records is loaded"
            },
            {
                "title": "Verify clicking page number links navigates to correct page",
                "category": "Functional",
                "priority": "Medium",
                "expected": "Table shows correct page data"
            }
        ])

    if feature_dict.get("tables", 0) > 0:
        testcases.extend([
            {
                "title": "Verify table headers sorting (ascending/descending)",
                "category": "Functional",
                "priority": "Medium",
                "expected": "Table rows sort according to column header"
            }
        ])

    return testcases