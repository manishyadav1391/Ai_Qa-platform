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
        text, href, required, visible, locator, xpath, css_selector,
        label, parent_section, nearby_text, element_index
    """
    js_code = r"""
    () => {
        const interactiveTags = ['input', 'button', 'select', 'textarea', 'a', 'form', 'table'];
        const elements = [];
        
        const getXPath = (el) => {
            if (el.id) return `//*[@id="${el.id}"]`;
            if (el === document.body) return '/html/body';
            let ix = 0;
            const siblings = el.parentNode ? el.parentNode.childNodes : [];
            for (let i = 0; i < siblings.length; i++) {
                const sibling = siblings[i];
                if (sibling === el) {
                    return getXPath(el.parentNode) + '/' + el.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                }
                if (sibling.nodeType === 1 && sibling.tagName === el.tagName) {
                    ix++;
                }
            }
            return '';
        };

        const getCSSSelector = (el) => {
            if (el.id) return `#${el.id}`;
            let path = [];
            while (el && el.nodeType === 1) {
                let selector = el.tagName.toLowerCase();
                if (el.className) {
                    // Filter out dynamic/interactive class states
                    const classes = Array.from(el.classList)
                        .filter(c => !c.includes('active') && !c.includes('focus') && !c.includes('hover') && !c.includes('ng-'))
                        .join('.');
                    if (classes) selector += '.' + classes;
                }
                let nth = 1;
                let sibling = el.previousElementSibling;
                while (sibling) {
                    if (sibling.tagName === el.tagName) nth++;
                    sibling = sibling.previousElementSibling;
                }
                if (nth > 1) selector += `:nth-of-type(${nth})`;
                path.unshift(selector);
                el = el.parentNode;
            }
            return path.join(' > ');
        };

        const findLabel = (el) => {
            if (el.id) {
                const label = document.querySelector(`label[for="${el.id}"]`);
                if (label) return label.innerText.trim();
            }
            let parent = el.parentNode;
            while (parent) {
                if (parent.tagName === 'LABEL') return parent.innerText.trim();
                parent = parent.parentNode;
            }
            let prev = el.previousElementSibling;
            if (prev && prev.tagName === 'LABEL') return prev.innerText.trim();
            return '';
        };

        const findParentSection = (el) => {
            let parent = el.parentNode;
            while (parent && parent !== document.body) {
                const tag = parent.tagName;
                if (['FORM', 'SECTION', 'NAV', 'HEADER', 'FOOTER', 'ARTICLE', 'ASIDE'].includes(tag)) {
                    const id = parent.id ? `#${parent.id}` : '';
                    const cls = parent.className ? `.${Array.from(parent.classList).slice(0, 2).join('.')}` : '';
                    return `${tag.toLowerCase()}${id}${cls}`;
                }
                parent = parent.parentNode;
            }
            return 'body';
        };

        const getNearbyText = (el) => {
            if (!el.parentNode) return '';
            let text = el.parentNode.innerText || '';
            if (text.length > 200) {
                text = text.substring(0, 200);
            }
            return text.replace(/\s+/g, ' ').trim();
        };

        const allElements = document.querySelectorAll(interactiveTags.join(','));
        
        allElements.forEach((el, index) => {
            const style = window.getComputedStyle(el);
            const visible = style.display !== 'none' && style.visibility !== 'hidden' && el.offsetWidth > 0 && el.offsetHeight > 0;
            
            const tag = el.tagName.toLowerCase();
            const inputType = tag === 'input' ? el.getAttribute('type') || 'text' : '';
            
            let type = 'unknown';
            if (tag === 'a') type = 'link';
            else if (tag === 'button') type = 'button';
            else if (tag === 'select') type = 'dropdown';
            else if (tag === 'textarea') type = 'textarea';
            else if (tag === 'form') type = 'form';
            else if (tag === 'table') type = 'table';
            else if (tag === 'input') {
                if (inputType === 'checkbox') type = 'checkbox';
                else if (inputType === 'radio') type = 'radio';
                else if (['submit', 'reset', 'button'].includes(inputType)) type = 'button';
                else type = 'input';
            }
            
            elements.push({
                tag: tag,
                type: type,
                name: el.getAttribute('name') || '',
                element_id: el.id || '',
                input_type: inputType,
                placeholder: el.getAttribute('placeholder') || '',
                text: el.innerText ? el.innerText.trim() : (el.value || ''),
                href: el.getAttribute('href') || el.getAttribute('action') || '',
                required: el.hasAttribute('required') ? 'true' : 'false',
                visible: visible ? 'true' : 'false',
                locator: el.id ? `#${el.id}` : (el.getAttribute('name') ? `${tag}[name='${el.getAttribute('name')}']` : tag),
                xpath: getXPath(el),
                css_selector: getCSSSelector(el),
                label: findLabel(el),
                parent_section: findParentSection(el),
                nearby_text: getNearbyText(el),
                element_index: index
            });
        });
        
        return elements;
    }
    """
    return page.evaluate(js_code)

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
