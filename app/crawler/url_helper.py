from urllib.parse import urljoin, urlparse

def resolve_target_url(project_url: str, input_url: str) -> str:
    """
    Smarter URL resolver that handles subdirectory-based applications
    and index.php/ routing base URLs.
    """
    if not input_url:
        return project_url
    if input_url.startswith("http://") or input_url.startswith("https://"):
        return input_url

    parsed = urlparse(project_url)
    path = parsed.path

    # 1. Handle index.php/ and other script routing indicators
    routing_indicators = ["/index.php", "/index.html", "/index.htm"]
    for indicator in routing_indicators:
        if indicator + "/" in path:
            idx = path.find(indicator + "/")
            base_path = path[:idx + len(indicator)]
            base_url = parsed._replace(path=base_path).geturl()
            return urljoin(base_url + "/", input_url.lstrip("/"))
        elif path.endswith(indicator):
            base_url = parsed._replace(path=path).geturl()
            return urljoin(base_url + "/", input_url.lstrip("/"))

    # 2. If input starts with slash, check for subdirectories in project path
    if input_url.startswith("/"):
        if "/" in path.rstrip("/"):
            parent_dir = path.rsplit("/", 1)[0] + "/"
            base_url = parsed._replace(path=parent_dir).geturl()
            return urljoin(base_url, input_url.lstrip("/"))

    # 3. Fallback to standard urljoin
    base_url = project_url
    if not path.endswith("/") and "." not in path.split("/")[-1]:
        base_url += "/"
    return urljoin(base_url, input_url)
