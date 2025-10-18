import logging
import os
import re
from difflib import SequenceMatcher

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from schema import YelpBusinessOutput

load_dotenv()  # This loads the .env file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

yelp_mcp = FastMCP("yelp_mcp")


def normalize_restaurant_name(name: str) -> str:
    """Normalize restaurant name for better matching."""
    if not name:
        return ""

    # Convert to lowercase
    normalized = name.lower()

    # Remove common suffixes and prefixes
    suffixes_to_remove = [
        "restaurant",
        "cafe",
        "coffee",
        "bar",
        "kitchen",
        "dining",
        "food",
        "レストラン",
        "カフェ",
        "バー",
        "キッチン",
        "ダイニング",
        "フード",
    ]

    for suffix in suffixes_to_remove:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)].strip()

    # Remove special characters and extra spaces
    normalized = re.sub(r"[^\w\s]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two restaurant names."""
    if not name1 or not name2:
        return 0.0

    # Normalize both names
    norm1 = normalize_restaurant_name(name1)
    norm2 = normalize_restaurant_name(name2)

    # Calculate similarity using SequenceMatcher
    similarity = SequenceMatcher(None, norm1, norm2).ratio()

    return similarity


def is_reliable_yelp_match(
    google_name: str, yelp_name: str, min_similarity: float = 0.7
) -> bool:
    """Check if Yelp result is likely to be the same restaurant as Google Maps result."""
    similarity = calculate_name_similarity(google_name, yelp_name)

    logger.info(
        f"Name similarity check: '{google_name}' vs '{yelp_name}' = {similarity:.2f}"
    )

    return similarity >= min_similarity


@yelp_mcp.tool(
    name="yelp_business_search",
    description="""Search for a restaurant on Yelp and get business information.
    Returns:
    - name: The name of the restaurant
    - yelp_rating: The Yelp rating of the restaurant (only if name matches reliably)
    - yelp_review_count: The number of Yelp reviews (only if name matches reliably)
    - yelp_url: The Yelp URL of the restaurant (only if name matches reliably)
    Note: Individual review text and reviewer information are not available through the Yelp API.
    The tool validates that the Yelp result matches the requested restaurant name to prevent incorrect information.
    """,
)
def yelp_business_search(
    restaurant_name: str,
    location: str | None = None,
) -> YelpBusinessOutput:
    """
    Search for a restaurant on Yelp and return detailed information including reviews.
    """
    return _search_yelp_business_internal(restaurant_name, location)


def _search_yelp_business_internal(
    restaurant_name: str,
    location: str | None = None,
) -> YelpBusinessOutput:
    """
    Internal function to search for a restaurant on Yelp.
    This is the core logic extracted from yelp_business_search.
    """
    api_key = os.getenv("YELP_API_KEY")
    if not api_key:
        raise Exception("YELP_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        # First, search for the business
        search_params = {
            "term": restaurant_name,
            "categories": "restaurants",
            "limit": 1,
        }

        if location:
            search_params["location"] = location

        search_response = requests.get(
            "https://api.yelp.com/v3/businesses/search",
            headers=headers,
            params=search_params,
            timeout=15,
        )

        if search_response.status_code != 200:
            logger.error(
                f"Yelp search failed with status {search_response.status_code}"
            )
            raise Exception(f"Yelp search failed: {search_response.text}")

        search_data = search_response.json()
        businesses = search_data.get("businesses", [])

        if not businesses:
            logger.warning(f"No businesses found for '{restaurant_name}'")
            return YelpBusinessOutput(
                name=restaurant_name,
                yelp_rating=None,
                yelp_review_count=None,
                yelp_url=None,
                reviews=[],
            )

        business = businesses[0]
        business_name = business.get("name", restaurant_name)
        yelp_rating = business.get("rating")
        yelp_review_count = business.get("review_count")
        yelp_url = business.get("url")

        # Validate that the Yelp result matches the requested restaurant
        is_reliable = is_reliable_yelp_match(restaurant_name, business_name)

        if not is_reliable:
            logger.warning(
                f"Yelp result may not match requested restaurant: '{restaurant_name}' vs '{business_name}'"
            )
            # Return a result indicating unreliable match
            return YelpBusinessOutput(
                name=restaurant_name,  # Use original name
                yelp_rating=None,  # Don't report unreliable rating
                yelp_review_count=None,  # Don't report unreliable count
                yelp_url=None,  # Don't report unreliable URL
                reviews=[],
            )

        logger.info(f"Yelp business information validated: {business_name}")
        logger.info(f"Yelp business information: {business}")

        return YelpBusinessOutput(
            name=business_name,
            yelp_rating=yelp_rating,
            yelp_review_count=yelp_review_count,
            yelp_url=yelp_url,
            reviews=[],  # Empty list since we can't access individual reviews
        )

    except Exception as e:
        logger.error(f"Failed to search for restaurant on Yelp: {e}")
        raise Exception(f"Failed to search for restaurant on Yelp: {e}")


@yelp_mcp.tool(
    name="yelp_enhance_google_maps_results",
    description="""Enhance Google Maps search results with Yelp business information.
    Takes a list of restaurant names and returns enhanced data with Yelp ratings and business info.
    Only includes Yelp data when the restaurant name matches reliably to prevent incorrect information.
    Note: Individual review text is not available through the Yelp API.
    """,
)
def yelp_enhance_google_maps_results(
    restaurant_names: list[str],
    location: str | None = None,
) -> list[YelpBusinessOutput]:
    """
    Enhance Google Maps search results with Yelp review information.
    """
    enhanced_results = []

    for restaurant_name in restaurant_names:
        try:
            result = _search_yelp_business_internal(restaurant_name, location)
            enhanced_results.append(result)
        except Exception as e:
            logger.warning(f"Failed to enhance {restaurant_name} with Yelp data: {e}")
            # Add a basic result even if Yelp fails
            enhanced_results.append(
                YelpBusinessOutput(
                    name=restaurant_name,
                    yelp_rating=None,
                    yelp_review_count=None,
                    yelp_url=None,
                    reviews=[],
                )
            )
        logger.info(f"Found Yelp business information for {restaurant_name}")

    return enhanced_results
