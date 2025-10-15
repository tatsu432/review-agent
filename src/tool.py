import os
import urllib.request
from html.parser import HTMLParser
from typing import Dict, List
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from ddgs import DDGS
from langchain_core.tools import tool

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@tool
def web_search(query: str, max_results: int = 10) -> list:
    """Search the web and return a list of results with title, href, and snippet.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (default 10).

    Returns:
        A list of dicts: {"title": str, "href": str, "snippet": str}
    """
    results: list = []
    seen_keys: set = set()
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=max_results):
            title = item.get("title")
            href = item.get("href") or item.get("url")
            body = item.get("body") or item.get("snippet")
            if not href:
                continue
            norm = _normalize_url_internal(href)
            # Deduplicate by normalized scheme+netloc+path
            key = norm or href
            if key in seen_keys:
                continue
            seen_keys.add(key)
            results.append({"title": title or "", "href": href, "snippet": body or ""})
    return results


# Back-compat alias for previous tool name observed in notebook logs
@tool("mcp_web_search")
def mcp_web_search(query: str, max_results: int = 10) -> list:
    """Back-compatible alias for web_search."""
    return web_search(query=query, max_results=max_results)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self._chunks.append(text)

    def get_text(self) -> str:
        return " ".join(self._chunks)


@tool
def fetch_page_text(url: str, timeout_seconds: int = 10) -> str:
    """Fetch a web page and return plain text content for ranking/summarization.

    Args:
        url: The URL to fetch.
        timeout_seconds: Timeout for the HTTP request.

    Returns:
        Extracted visible text content as a single string.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        content_type = resp.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type:
            return ""
        html_bytes = resp.read()
        try:
            html = html_bytes.decode("utf-8", errors="ignore")
        except Exception:
            html = html_bytes.decode(errors="ignore")
    parser = _TextExtractor()
    parser.feed(html)
    return parser.get_text()


def _normalize_url_internal(url: str) -> str:
    try:
        parsed = urlparse(url.strip())
        scheme = "https" if parsed.scheme in ("http", "https") else parsed.scheme
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        # Strip common tracking params and anchors
        allowed_params = []
        query_pairs = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=False)
            if k in allowed_params
        ]
        query = urlencode(query_pairs)
        # Remove trailing slashes and default index
        path = (parsed.path or "/").replace("/index.html", "/").rstrip("/") or "/"
        normalized = urlunparse((scheme, netloc, path, "", query, ""))
        return normalized
    except Exception:
        return url


@tool
def normalize_url(url: str) -> str:
    """Normalize a URL (lowercase host, strip www, tracking params, trailing slash)."""
    return _normalize_url_internal(url)


_LOW_AUTHORITY_DOMAINS = {
    "yelp.com",
    "tripadvisor.com",
    "google.com",
    "maps.google.com",
    "facebook.com",
    "instagram.com",
}

_AUTHORITATIVE_GUIDES = {
    "michelin.com",
    "timeout.com",
    "eater.com",
    "nytimes.com",
    "washingtonpost.com",
    "tabelog.com",
}


def _score_domain_for_official(domain: str) -> int:
    # Higher is better for being the restaurant's own site
    if domain in _LOW_AUTHORITY_DOMAINS:
        return 0
    if domain in _AUTHORITATIVE_GUIDES:
        return 2
    # Unknown domains get mid score; potential official site
    return 3


@tool
def select_best_link(restaurant_name: str, candidates_json: str) -> str:
    """Choose the best URL for a restaurant from candidate links.

    Provide candidates_json as a JSON array of {"title": str, "href": str}.
    Preference order: official site > authoritative guide (Michelin/TimeOut/Eater/Tabelog) > others.
    Returns the selected href (original, not normalized).
    """
    import json as _json

    try:
        candidates = _json.loads(candidates_json)
    except Exception:
        return ""

    def candidate_key(c):
        href = c.get("href", "")
        norm = _normalize_url_internal(href)
        domain = urlparse(norm).netloc
        title = (c.get("title") or "").lower()
        name = (restaurant_name or "").lower()
        is_name_in_title = 1 if (name and name in title) else 0
        domain_score = _score_domain_for_official(domain)
        # Prefer candidates whose title includes the restaurant name and with higher domain score
        return (is_name_in_title, domain_score)

    best = None
    best_key = (-1, -1)
    for c in candidates:
        k = candidate_key(c)
        if k > best_key:
            best, best_key = c, k
    return (best or {}).get("href", "")


@tool
def google_maps_places(
    query: str,
    location: str | None = None,
    radius_meters: int | None = 2000,
) -> list:
    """Search restaurants via Google Maps Places API and return structured data.

    Inputs:
    - query: search text (e.g., "sushi", "ramen", or restaurant name)
    - location: optional "lat,lng" center; if omitted, text search relies on query context
    - radius_meters: optional radius for nearby search when location provided

    Output: list of dicts with keys:
      name, rating, price_level, types, photo_url, place_url

    Requires environment variable GOOGLE_MAPS_API_KEY.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY is not set")
        raise Exception("GOOGLE_MAPS_API_KEY is not set")
    logger.info("GOOGLE_MAPS_API_KEY is set")

    session = requests.Session()

    logger.info("session is set")

    def _build_photo_url(photo_ref: str) -> str:
        if not photo_ref:
            logger.warning("photo_ref is not set")
            return ""
        logger.info("photo_ref is set")
        return (
            "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference="
            + photo_ref
            + "&key="
            + api_key
        )

    results: List[Dict] = []

    try:
        # Prefer Places Text Search for flexible query, optionally biased by location.
        params = {"query": query, "key": api_key}
        if location:
            params["location"] = location
            if radius_meters:
                params["radius"] = radius_meters

        resp = session.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params,
            timeout=15,
        )
        data = resp.json()
        for item in data.get("results", []):
            place_id = item.get("place_id", "")
            name = item.get("name", "")
            rating = item.get("rating")
            price_level = item.get("price_level")
            types = item.get("types") or []
            photos = item.get("photos") or []
            photo_ref = photos[0].get("photo_reference") if photos else ""
            photo_url = _build_photo_url(photo_ref)
            place_url = (
                f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                if place_id
                else ""
            )

            # Only include likely restaurants
            if "restaurant" in types or "food" in types:
                results.append(
                    {
                        "name": name,
                        "rating": rating,
                        "price_level": price_level,
                        "types": types,
                        "photo_url": photo_url,
                        "place_url": place_url,
                    }
                )
    except Exception:
        logger.error("Failed to search for restaurants via Google Maps Places API")
        raise Exception("Failed to search for restaurants via Google Maps Places API")

    logger.info("Results are set")
    return results
