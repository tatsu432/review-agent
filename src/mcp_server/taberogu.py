import logging
import re
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP
from schema import TaberoguOutput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

taberogu_mcp = FastMCP("taberogu_mcp")


def extract_restaurant_name_from_google_maps_url(url: str) -> str | None:
    """Extract restaurant name from Google Maps URL."""
    if not url:
        return None

    try:
        # Try to extract from URL parameters
        parsed = urlparse(url)
        if "place" in parsed.path:
            # Extract from path like /maps/place/Restaurant+Name/@lat,lng,zoom
            path_parts = parsed.path.split("/")
            for part in path_parts:
                if part and "+" in part:
                    return part.replace("+", " ")

        # Try to extract from query parameters
        if parsed.query:
            query_params = parsed.query.split("&")
            for param in query_params:
                if "q=" in param:
                    name = param.split("q=")[1]
                    return name.replace("+", " ")

        return None
    except Exception as e:
        logger.warning(f"Failed to extract restaurant name from URL: {e}")
        return None


def search_taberogu_restaurant(
    restaurant_name: str, location: str | None = None
) -> list[TaberoguOutput]:
    """Search for restaurant on Taberogu and return restaurant information."""
    try:
        # Construct search URL
        search_query = restaurant_name
        if location:
            search_query = f"{restaurant_name} {location}"

        # URL encode the search query
        encoded_query = quote(search_query)
        search_url = f"https://tabelog.com/tokyo/rstLst/?vs=1&sa=&sk={encoded_query}"

        logger.info(f"Searching Taberogu for: {search_query}")

        # Set headers to mimic a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        results = []

        # Find restaurant listings
        restaurant_listings = soup.find_all("div", class_="list-rst")

        for listing in restaurant_listings[:5]:  # Limit to first 5 results
            try:
                # Extract restaurant name - use the correct selector
                name_elem = listing.find("a", class_="list-rst__rst-name-target")
                if not name_elem:
                    continue

                name = name_elem.get_text(strip=True)
                restaurant_url = name_elem.get("href", "")

                # Extract rating - use the correct selector
                rating_elem = listing.find("span", class_="c-rating__val")
                rating = None
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    try:
                        rating = float(rating_text)
                    except ValueError:
                        pass

                # Extract number of reviews - look for the review count element
                reviews_elem = listing.find("em", class_="list-rst__rvw-count-num")
                reviews_count = None
                if reviews_elem:
                    reviews_text = reviews_elem.get_text(strip=True)
                    # Extract number from text like "123"
                    match = re.search(r"(\d+)", reviews_text)
                    if match:
                        reviews_count = int(match.group(1))

                # Extract address - look for area-genre info
                address_elem = listing.find("div", class_="list-rst__area-genre")
                address = address_elem.get_text(strip=True) if address_elem else None

                # Extract phone - not available in search results
                phone = None

                # Extract business hours - not available in search results
                business_hours = None

                # Construct full Taberogu URL
                if restaurant_url and not restaurant_url.startswith("http"):
                    restaurant_url = f"https://tabelog.com{restaurant_url}"

                result = TaberoguOutput(
                    name=name,
                    rating=rating,
                    reviews_count=reviews_count,
                    taberogu_url=restaurant_url,
                    address=address,
                    phone=phone,
                    business_hours=business_hours,
                )

                results.append(result)

            except Exception as e:
                logger.warning(f"Failed to parse restaurant listing: {e}")
                continue

        return results

    except requests.RequestException as e:
        logger.error(f"Failed to search Taberogu: {e}")
        raise Exception(f"Failed to search Taberogu: {e}")
    except Exception as e:
        logger.error(f"Unexpected error searching Taberogu: {e}")
        raise Exception(f"Unexpected error searching Taberogu: {e}")


@taberogu_mcp.tool(
    name="taberogu_search",
    description="""Search for restaurants on Taberogu and return structured data including ratings and reviews.
    Return the results in the following format:
    - name: The name of the restaurant
    - rating: The rating of the restaurant on Taberogu
    - reviews_count: The number of reviews of the restaurant on Taberogu
    - taberogu_url: The Taberogu URL of the restaurant
    - address: The address of the restaurant
    - phone: The phone number of the restaurant
    - business_hours: The business hours of the restaurant
    """,
)
def taberogu_search(
    restaurant_name: str,
    location: str | None = None,
) -> list[TaberoguOutput]:
    """
    Search for restaurants on Taberogu and return restaurant information.

    Args:
        restaurant_name: The name of the restaurant to search for
        location: Optional location to narrow down the search

    Returns:
        List of restaurant information including ratings and reviews
    """
    if not restaurant_name:
        raise ValueError("restaurant_name is required")

    logger.info(f"Searching Taberogu for restaurant: {restaurant_name}")
    if location:
        logger.info(f"Location filter: {location}")

    try:
        results = search_taberogu_restaurant(restaurant_name, location)
        logger.info(f"Found {len(results)} restaurants on Taberogu")
        return results
    except Exception as e:
        logger.error(f"Failed to search Taberogu: {e}")
        raise Exception(f"Failed to search Taberogu: {e}")


@taberogu_mcp.tool(
    name="taberogu_from_google_maps",
    description="""Search for restaurants on Taberogu using a Google Maps URL.
    Extracts the restaurant name from the Google Maps URL and searches Taberogu.
    """,
)
def taberogu_from_google_maps(
    google_maps_url: str,
    location: str | None = None,
) -> list[TaberoguOutput]:
    """
    Search for restaurants on Taberogu using a Google Maps URL.

    Args:
        google_maps_url: The Google Maps URL of the restaurant
        location: Optional location to narrow down the search

    Returns:
        List of restaurant information including ratings and reviews
    """
    if not google_maps_url:
        raise ValueError("google_maps_url is required")

    logger.info(f"Extracting restaurant name from Google Maps URL: {google_maps_url}")

    # Extract restaurant name from Google Maps URL
    restaurant_name = extract_restaurant_name_from_google_maps_url(google_maps_url)

    if not restaurant_name:
        raise ValueError("Could not extract restaurant name from Google Maps URL")

    logger.info(f"Extracted restaurant name: {restaurant_name}")

    try:
        results = search_taberogu_restaurant(restaurant_name, location)
        logger.info(f"Found {len(results)} restaurants on Taberogu")
        return results
    except Exception as e:
        logger.error(f"Failed to search Taberogu from Google Maps URL: {e}")
        raise Exception(f"Failed to search Taberogu from Google Maps URL: {e}")
