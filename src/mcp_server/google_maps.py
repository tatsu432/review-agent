import logging
import os
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from schema import GoogleMapsPlacesOutput

load_dotenv()  # This loads the .env file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

google_maps_places_mcp = FastMCP("google_maps_places_mcp")


def is_valid_google_maps_url(url: str) -> bool:
    """Validate if a URL is a proper Google Maps URL."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.netloc in ["www.google.com", "maps.google.com", "maps.app.goo.gl"]
    except Exception:
        return False


@google_maps_places_mcp.tool(
    name="google_maps_places",
    description="""Search restaurants via Google Maps Places API and return structured data.
    Return the results in the following format:
    - name: The name of the restaurant
    - rating: The rating of the restaurant
    - reviews_count: The number of reviews of the restaurant
    - price_level: The price level of the restaurant
    - types: The types of the restaurant
    - place_url: The place url of the restaurant
    """,
)
def google_maps_places(
    query: str,
    location: str | None = None,
    radius_meters: int | None = 2000,
) -> list[GoogleMapsPlacesOutput]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise Exception("GOOGLE_MAPS_API_KEY is not set")

    # We'll keep internal mapping to place_id for optional enrichment
    results_with_ids: list[GoogleMapsPlacesOutput] = []

    try:
        # Prefer Places Text Search for flexible query, optionally biased by location.
        params = {"query": query, "key": api_key}
        if location:
            params["location"] = location
            if radius_meters:
                params["radius"] = radius_meters

        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params,
            timeout=15,
        )
        data = resp.json()
        for item in data.get("results", []):
            place_id = item.get("place_id", "")
            name = item.get("name", "")
            rating = item.get("rating")
            reviews_count = item.get("user_ratings_total")
            price_level = item.get("price_level")
            types = item.get("types") or []

            # Generate a more reliable Google Maps URL
            place_url = None
            if place_id:
                # Use the more reliable place_id format for Google Maps URLs
                place_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

            # Only include likely restaurants
            if "restaurant" in types or "food" in types:
                results_with_ids.append(
                    {
                        "_place_id": place_id,
                        "name": name,
                        "rating": rating,
                        "reviews_count": reviews_count,
                        "price_level": price_level,
                        "types": types,
                        "place_url": place_url,
                    }
                )
    except Exception:
        logger.error("Failed to search for restaurants via Google Maps Places API")
        raise Exception("Failed to search for restaurants via Google Maps Places API")

    # Enrich missing data and validate URLs using Place Details API
    try:
        for r in results_with_ids:
            need_price = r.get("price_level") is None
            need_reviews = r.get("reviews_count") is None
            place_id = r.get("_place_id")
            current_url = r.get("place_url")

            # Always try to get the canonical URL from Place Details API for better reliability
            if place_id:
                fields = ["url"]  # Always request the canonical URL
                if need_price:
                    fields.append("price_level")
                if need_reviews:
                    fields.append("user_ratings_total")

                details_params = {
                    "place_id": place_id,
                    "fields": ",".join(fields),
                    "key": api_key,
                }
                try:
                    dresp = requests.get(
                        "https://maps.googleapis.com/maps/api/place/details/json",
                        params=details_params,
                        timeout=15,
                    )
                    djson = dresp.json()
                    result = (djson or {}).get("result", {})

                    # Update price and reviews if needed
                    if need_price and result.get("price_level") is not None:
                        r["price_level"] = result.get("price_level")
                    if need_reviews and result.get("user_ratings_total") is not None:
                        r["reviews_count"] = result.get("user_ratings_total")

                    # Use canonical URL if available and valid, otherwise keep the generated one
                    canonical_url = result.get("url")
                    if canonical_url and is_valid_google_maps_url(canonical_url):
                        r["place_url"] = canonical_url
                        logger.info(
                            f"Using canonical URL for {r.get('name')}: {canonical_url}"
                        )
                    elif current_url and is_valid_google_maps_url(current_url):
                        logger.info(
                            f"Using generated URL for {r.get('name')}: {current_url}"
                        )
                    else:
                        r["place_url"] = None
                        logger.warning(
                            f"No valid URL available for {r.get('name')} (canonical: {canonical_url}, generated: {current_url})"
                        )

                except Exception as e:
                    logger.warning(f"Failed to enrich place {r.get('name')}: {e}")
                    # Keep the current URL only if it's valid, otherwise set to None
                    if current_url and is_valid_google_maps_url(current_url):
                        logger.info(
                            f"Keeping valid generated URL for {r.get('name')}: {current_url}"
                        )
                    else:
                        r["place_url"] = None
                        logger.warning(
                            f"Setting URL to None for {r.get('name')} due to invalid URL: {current_url}"
                        )
                    continue
            else:
                # No place_id available, set URL to None
                r["place_url"] = None
                logger.warning(f"No place_id for {r.get('name')}, setting URL to None")

    except Exception as e:
        # If enrichment phase fails globally, we still return base results
        logger.warning(f"Failed to enrich results via Google Maps Places API: {e}")

    # Strip internal fields before returning
    for r in results_with_ids:
        if "_place_id" in r:
            del r["_place_id"]

    logger.info("Results are set")
    return results_with_ids
