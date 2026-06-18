from urllib.parse import urljoin, urlparse

from app.crawler.crawler import scan_page


def crawl_site(
    start_url,
    max_depth=2
):

    root_domain = urlparse(start_url).netloc
    visited = set()
    pages = []

    def crawl(url, depth, parent_url=None):

        if depth > max_depth:
            return

        if url in visited:
            return

        visited.add(url)

        try:

            result = scan_page(url)
            result["depth"] = depth
            result["parent_url"] = parent_url
            pages.append(result)

            for link in result["links"]:

                full_url = urljoin(
                    url,
                    link
                )

                if urlparse(full_url).netloc != root_domain:
                    continue

                crawl(
                    full_url,
                    depth + 1,
                    parent_url=url
                )

        except Exception as e:

            print(
                f"Error crawling {url}: {e}"
            )

    crawl(
        start_url,
        0,
        parent_url=None
    )

    return pages