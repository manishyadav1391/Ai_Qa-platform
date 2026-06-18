"""
Recursive site crawler with safeguards against infinite crawling.

Features:
- URL normalization (fragments, trailing slashes, query params)
- Max pages limit (default 50)
- Per-page timeout (default 30s)
- URL blocklist (logout, downloads, mailto, etc.)
- Stop signal support (threading.Event)
- Browser reuse (single instance for all pages)
- Progress callback for live status updates
"""

import threading
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode

from playwright.sync_api import sync_playwright

from app.crawler.crawler import scan_page


# ── URL Blocklist ────────────────────────────────────────────────

# Path patterns that should never be crawled
BLOCKED_PATH_PATTERNS = [
    "logout",
    "signout",
    "sign-out",
    "log-out",
    "delete",
    "remove",
    "unsubscribe",
    "admin",
    "wp-admin",
    "wp-login",
]

# File extensions that are not HTML pages
BLOCKED_EXTENSIONS = {
    ".pdf", ".zip", ".rar", ".gz", ".tar",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".mp3", ".mp4", ".avi", ".mov", ".wmv",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".css", ".js", ".json", ".xml", ".csv",
    ".exe", ".dmg", ".apk",
}

# URL schemes that are not web pages
BLOCKED_SCHEMES = {"mailto", "tel", "javascript", "data", "ftp"}

# Query parameters to strip for normalization (tracking params)
STRIP_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid", "mc_cid", "mc_eid",
}


def normalize_url(url: str) -> str:
    """
    Normalize a URL to prevent duplicate crawling.

    - Strips fragments (#section)
    - Strips trailing slashes
    - Removes tracking query parameters
    - Lowercases scheme and host
    - Sorts remaining query parameters
    """
    parsed = urlparse(url)

    # Lowercase scheme and host
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip trailing slash from path (but keep "/" for root)
    path = parsed.path.rstrip("/") or "/"

    # Remove tracking params, sort remaining
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        filtered = {
            k: v for k, v in params.items()
            if k.lower() not in STRIP_PARAMS
        }
        query = urlencode(filtered, doseq=True) if filtered else ""
    else:
        query = ""

    # Rebuild without fragment
    return urlunparse((scheme, netloc, path, "", query, ""))


def is_blocked_url(url: str) -> bool:
    """Check if a URL should be skipped."""
    parsed = urlparse(url)

    # Check scheme
    if parsed.scheme.lower() in BLOCKED_SCHEMES:
        return True

    # Check file extension
    path_lower = parsed.path.lower()
    for ext in BLOCKED_EXTENSIONS:
        if path_lower.endswith(ext):
            return True

    # Check blocked path patterns
    for pattern in BLOCKED_PATH_PATTERNS:
        if pattern in path_lower:
            return True

    return False


def crawl_site(
    start_url: str,
    max_depth: int = 2,
    max_pages: int = 50,
    page_timeout: int = 30000,
    stop_event: threading.Event = None,
    on_progress=None,
):
    """
    Crawl a website recursively with safeguards.

    Args:
        start_url: The starting URL to crawl.
        max_depth: Maximum link depth to follow (default 2).
        max_pages: Maximum number of pages to crawl (default 50).
        page_timeout: Per-page timeout in ms (default 30000).
        stop_event: A threading.Event — if set, crawler stops gracefully.
        on_progress: Callback function(pages_crawled, current_url) for live updates.

    Returns:
        List of page result dicts.
    """
    root_domain = urlparse(start_url).netloc.lower()
    visited = set()
    pages = []

    # Launch a single browser for all pages
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)

    try:
        def crawl(url, depth, parent_url=None):
            # ── Guard: stop signal ──
            if stop_event and stop_event.is_set():
                return

            # ── Guard: max pages ──
            if len(pages) >= max_pages:
                return

            # ── Guard: max depth ──
            if depth > max_depth:
                return

            # ── Normalize and deduplicate ──
            normalized = normalize_url(url)
            if normalized in visited:
                return
            visited.add(normalized)

            # ── Guard: blocked URLs ──
            if is_blocked_url(url):
                return

            # ── Report progress ──
            if on_progress:
                on_progress(len(pages), url)

            try:
                result = scan_page(
                    url,
                    browser=browser,
                    timeout=page_timeout
                )
                result["depth"] = depth
                result["parent_url"] = parent_url
                pages.append(result)

                # Report progress after successful scan
                if on_progress:
                    on_progress(len(pages), url)

                # Follow links from this page
                for link in result["links"]:
                    # Check stop signal before each child page
                    if stop_event and stop_event.is_set():
                        return
                    if len(pages) >= max_pages:
                        return

                    full_url = urljoin(url, link)

                    # Only follow same-domain links
                    if urlparse(full_url).netloc.lower() != root_domain:
                        continue

                    crawl(
                        full_url,
                        depth + 1,
                        parent_url=url
                    )

            except Exception as e:
                print(f"Error crawling {url}: {e}")

        crawl(start_url, 0, parent_url=None)

    finally:
        browser.close()
        pw.stop()

    return pages