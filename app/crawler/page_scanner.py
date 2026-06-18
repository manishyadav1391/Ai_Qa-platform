from playwright.sync_api import Page


# Element types to SKIP when generating test cases / scripts
SKIP_INPUT_TYPES = {"hidden", "submit", "reset", "image"}

# Tags we actively extract as interactive elements
INTERACTIVE_TAGS = {"input", "button", "select", "textarea", "a", "form", "table"}


def _is_visible(locator) -> bool:
    """Safely check if an element is visible."""
    try:
        return locator.is_visible()
    except Exception:
        return True  # Default to visible if check fails


def _classify_element(tag: str, input_type: str | None, href: str | None) -> str:
    """
    Map an HTML tag + attributes to a semantic element type.
    This is what downstream generators use to decide test strategies.
    """
    if tag == "a":
        return "link"

    if tag == "button":
        return "button"

    if tag == "input":
        if input_type == "checkbox":
            return "checkbox"
        if input_type == "radio":
            return "radio"
        if input_type in ("submit", "reset", "button"):
            return "button"
        # text, email, password, number, search, tel, url, date, etc.
        return "input"

    if tag == "select":
        return "dropdown"

    if tag == "textarea":
        return "textarea"

    if tag == "form":
        return "form"

    if tag == "table":
        return "table"

    return "unknown"


def _build_locator(element_id: str | None, name: str | None, tag: str) -> str:
    """Build the best CSS locator from available attributes."""
    if element_id:
        return f"#{element_id}"
    if name:
        return f"{tag}[name='{name}']"
    return tag


def extract_elements(page: Page):
    """
    Extract all interactive elements from the page with rich metadata.

    Returns a list of dicts with:
        tag, type, name, element_id, input_type, placeholder,
        text, href, required, visible, locator
    """
    elements = []

    # ─── Inputs ──────────────────────────────────────────────────────
    inputs = page.locator("input").all()

    for item in inputs:
        input_type = item.get_attribute("type") or "text"
        element_id = item.get_attribute("id") or ""
        name = item.get_attribute("name") or ""
        placeholder = item.get_attribute("placeholder") or ""
        visible = _is_visible(item)
        required = item.get_attribute("required") is not None

        # Hidden inputs are still stored but flagged
        if input_type == "hidden":
            visible = False

        elem_type = _classify_element("input", input_type, None)

        elements.append({
            "tag": "input",
            "type": elem_type,
            "name": name,
            "element_id": element_id,
            "input_type": input_type,
            "placeholder": placeholder,
            "text": "",
            "href": "",
            "required": "true" if required else "false",
            "visible": "true" if visible else "false",
            "locator": _build_locator(element_id, name, "input"),
        })

    # ─── Buttons ─────────────────────────────────────────────────────
    buttons = page.locator("button").all()

    for item in buttons:
        element_id = item.get_attribute("id") or ""
        name = item.get_attribute("name") or ""
        btn_type = item.get_attribute("type") or "button"
        text = ""
        try:
            text = item.inner_text().strip()
        except Exception:
            pass

        elements.append({
            "tag": "button",
            "type": "button",
            "name": name,
            "element_id": element_id,
            "input_type": btn_type,
            "placeholder": "",
            "text": text,
            "href": "",
            "required": "false",
            "visible": "true" if _is_visible(item) else "false",
            "locator": _build_locator(element_id, name, "button"),
        })

    # ─── Links (<a>) ─────────────────────────────────────────────────
    anchors = page.locator("a").all()

    for item in anchors:
        href = item.get_attribute("href") or ""
        element_id = item.get_attribute("id") or ""
        name = item.get_attribute("name") or ""
        text = ""
        try:
            text = item.inner_text().strip()
        except Exception:
            pass

        # Skip empty anchors (anchors with no text and no href)
        if not text and not href:
            continue

        elements.append({
            "tag": "a",
            "type": "link",
            "name": name,
            "element_id": element_id,
            "input_type": "",
            "placeholder": "",
            "text": text,
            "href": href,
            "required": "false",
            "visible": "true" if _is_visible(item) else "false",
            "locator": _build_locator(element_id, name, "a"),
        })

    # ─── Selects (dropdowns) ─────────────────────────────────────────
    selects = page.locator("select").all()

    for item in selects:
        element_id = item.get_attribute("id") or ""
        name = item.get_attribute("name") or ""
        required = item.get_attribute("required") is not None

        elements.append({
            "tag": "select",
            "type": "dropdown",
            "name": name,
            "element_id": element_id,
            "input_type": "",
            "placeholder": "",
            "text": "",
            "href": "",
            "required": "true" if required else "false",
            "visible": "true" if _is_visible(item) else "false",
            "locator": _build_locator(element_id, name, "select"),
        })

    # ─── Textareas ───────────────────────────────────────────────────
    textareas = page.locator("textarea").all()

    for item in textareas:
        element_id = item.get_attribute("id") or ""
        name = item.get_attribute("name") or ""
        placeholder = item.get_attribute("placeholder") or ""
        required = item.get_attribute("required") is not None

        elements.append({
            "tag": "textarea",
            "type": "textarea",
            "name": name,
            "element_id": element_id,
            "input_type": "",
            "placeholder": placeholder,
            "text": "",
            "href": "",
            "required": "true" if required else "false",
            "visible": "true" if _is_visible(item) else "false",
            "locator": _build_locator(element_id, name, "textarea"),
        })

    # ─── Forms ───────────────────────────────────────────────────────
    forms = page.locator("form").all()

    for item in forms:
        element_id = item.get_attribute("id") or ""
        name = item.get_attribute("name") or ""
        action = item.get_attribute("action") or ""

        elements.append({
            "tag": "form",
            "type": "form",
            "name": name,
            "element_id": element_id,
            "input_type": "",
            "placeholder": "",
            "text": "",
            "href": action,  # Store form action in href field
            "required": "false",
            "visible": "true" if _is_visible(item) else "false",
            "locator": _build_locator(element_id, name, "form"),
        })

    # ─── Tables ──────────────────────────────────────────────────────
    tables = page.locator("table").all()

    for item in tables:
        element_id = item.get_attribute("id") or ""

        elements.append({
            "tag": "table",
            "type": "table",
            "name": element_id,
            "element_id": element_id,
            "input_type": "",
            "placeholder": "",
            "text": "",
            "href": "",
            "required": "false",
            "visible": "true" if _is_visible(item) else "false",
            "locator": _build_locator(element_id, None, "table"),
        })

    return elements


def extract_features(page: Page):
    forms = page.locator("form").count()
    tables = page.locator("table").count()
    dropdowns = page.locator("select").count()
    textareas = page.locator("textarea").count()
    checkboxes = page.locator("input[type='checkbox']").count()
    radios = page.locator("input[type='radio']").count()
    links = page.locator("a[href]").count()

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
        "links": links,
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
