from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs, urlencode
from jsonapi.document import JSONAPI_CONTENT_TYPE


def validate_content_type(content_type: str) -> bool:
    """Validate that the content type is JSON:API compliant."""
    if not content_type:
        return False
    if content_type == JSONAPI_CONTENT_TYPE:
        return True
    # Check for content type with parameters (e.g., charset)
    if content_type.startswith(JSONAPI_CONTENT_TYPE + ";"):
        return True

    return False


def generate_pagination_links(
    base_url: str,
    current_page: int,
    total_pages: int,
    page_size: int,
    total_count: Optional[int] = None,
    **extra_params,
) -> Dict[str, str]:
    """
    Generate pagination links according to JSON:API specification.

    Args:
        base_url: The base URL for the resource
        current_page: Current page number (1-based)
        total_pages: Total number of pages
        page_size: Number of items per page
        total_count: Total number of items (optional)
        **extra_params: Additional query parameters to include

    Returns:
        Dictionary with pagination links (first, last, prev, next)
    """
    links = {}

    # Parse base URL to add query parameters
    parsed_url = urlparse(base_url)
    query_params = parse_qs(parsed_url.query)

    # Add extra parameters
    for key, value in extra_params.items():
        if isinstance(value, list):
            query_params[key] = value
        else:
            query_params[key] = [str(value)]

    # Generate first link
    first_params = query_params.copy()
    first_params["page[number]"] = ["1"]
    first_params["page[size]"] = [str(page_size)]
    links[
        "first"
    ] = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(first_params, doseq=True)}"

    # Generate last link
    if total_pages > 1:
        last_params = query_params.copy()
        last_params["page[number]"] = [str(total_pages)]
        last_params["page[size]"] = [str(page_size)]
        links[
            "last"
        ] = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(last_params, doseq=True)}"

    # Generate prev link
    if current_page > 1:
        prev_params = query_params.copy()
        prev_params["page[number]"] = [str(current_page - 1)]
        prev_params["page[size]"] = [str(page_size)]
        links[
            "prev"
        ] = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(prev_params, doseq=True)}"

    # Generate next link
    if current_page < total_pages:
        next_params = query_params.copy()
        next_params["page[number]"] = [str(current_page + 1)]
        next_params["page[size]"] = [str(page_size)]
        links[
            "next"
        ] = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(next_params, doseq=True)}"

    return links


def generate_cursor_pagination_links(
    base_url: str,
    current_cursor: Optional[str],
    next_cursor: Optional[str],
    prev_cursor: Optional[str],
    **extra_params,
) -> Dict[str, str]:
    """
    Generate cursor-based pagination links.

    Args:
        base_url: The base URL for the resource
        current_cursor: Current cursor value
        next_cursor: Next cursor value
        prev_cursor: Previous cursor value
        **extra_params: Additional query parameters to include

    Returns:
        Dictionary with pagination links (first, prev, next)
    """
    links = {}

    # Parse base URL to add query parameters
    parsed_url = urlparse(base_url)
    query_params = parse_qs(parsed_url.query)

    # Add extra parameters
    for key, value in extra_params.items():
        if isinstance(value, list):
            query_params[key] = value
        else:
            query_params[key] = [str(value)]

    # Generate first link (without cursor)
    first_params = query_params.copy()
    if "page[cursor]" in first_params:
        del first_params["page[cursor]"]
    links[
        "first"
    ] = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(first_params, doseq=True)}"

    # Generate prev link
    if prev_cursor:
        prev_params = query_params.copy()
        prev_params["page[cursor]"] = [prev_cursor]
        links[
            "prev"
        ] = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(prev_params, doseq=True)}"

    # Generate next link
    if next_cursor:
        next_params = query_params.copy()
        next_params["page[cursor]"] = [next_cursor]
        links[
            "next"
        ] = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(next_params, doseq=True)}"

    return links
