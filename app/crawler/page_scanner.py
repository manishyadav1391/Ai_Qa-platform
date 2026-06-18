from playwright.sync_api import Page


def extract_elements(page: Page):

    elements = []

    # Inputs (text-like, checkbox, radio)
    inputs = page.locator("input").all()

    for item in inputs:
        input_type = item.get_attribute("type")
        if input_type == "checkbox":
            elem_type = "checkbox"
        elif input_type == "radio":
            elem_type = "radio"
        else:
            elem_type = "input"

        elements.append({
            "type": elem_type,
            "name": item.get_attribute("name") or "",
            "locator": item.get_attribute("id") or "",
            "text": "",
            "placeholder": item.get_attribute("placeholder") or "",
            "required": "true" if item.get_attribute("required") is not None else "false"
        })

    # Buttons
    buttons = page.locator("button").all()

    for item in buttons:

        elements.append({
            "type": "button",
            "name": item.get_attribute("name") or "",
            "locator": item.get_attribute("id") or "",
            "text": item.inner_text() or "",
            "placeholder": "",
            "required": "false"
        })

    # Dropdowns (select elements)
    selects = page.locator("select").all()

    for item in selects:

        elements.append({
            "type": "dropdown",
            "name": item.get_attribute("name") or "",
            "locator": item.get_attribute("id") or "",
            "text": "",
            "placeholder": "",
            "required": "true" if item.get_attribute("required") is not None else "false"
        })

    # Forms
    forms = page.locator("form").all()

    for item in forms:

        elements.append({
            "type": "form",
            "name": item.get_attribute("name") or "",
            "locator": item.get_attribute("id") or "",
            "text": "",
            "placeholder": "",
            "required": "false"
        })

    # Tables
    tables = page.locator("table").all()

    for item in tables:

        elements.append({
            "type": "table",
            "name": item.get_attribute("id") or "",
            "locator": item.get_attribute("id") or "",
            "text": "",
            "placeholder": "",
            "required": "false"
        })

    # Textareas
    textareas = page.locator("textarea").all()

    for item in textareas:

        elements.append({
            "type": "textarea",
            "name": item.get_attribute("name") or "",
            "locator": item.get_attribute("id") or "",
            "text": "",
            "placeholder": item.get_attribute("placeholder") or "",
            "required": "true" if item.get_attribute("required") is not None else "false"
        })

    return elements


def extract_features(page: Page):
    forms = page.locator("form").count()
    tables = page.locator("table").count()
    dropdowns = page.locator("select").count()
    textareas = page.locator("textarea").count()
    checkboxes = page.locator("input[type='checkbox']").count()
    radios = page.locator("input[type='radio']").count()

    # Search inputs: type="search", or name/id/placeholder contains "search"
    search = page.locator("input[type='search'], input[name*='search' i], input[id*='search' i], input[placeholder*='search' i]").count()

    # Pagination: element with class/id containing "pagination" or nav with aria-label containing "pagination"
    pagination = page.locator(".pagination, [class*='pagination' i], [id*='pagination' i], nav[aria-label*='pagination' i]").count()

    return {
        "forms": forms,
        "tables": tables,
        "dropdowns": dropdowns,
        "textareas": textareas,
        "checkboxes": checkboxes,
        "radios": radios,
        "search": search,
        "pagination": pagination
    }


def extract_links(page):

    links = []

    anchors = page.locator("a").all()

    for anchor in anchors:

        href = anchor.get_attribute("href")

        if href:

            links.append(href)

    return list(set(links))
