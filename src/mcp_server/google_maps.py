import logging
import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()  # This loads the .env file

import requests
from fastmcp import FastMCP
from schema import GoogleMapsPlacesOutput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

google_maps_places_mcp = FastMCP("google_maps_places_mcp")


@google_maps_places_mcp.tool(
    name="google_maps_places",
    description="Search restaurants via Google Maps Places API and return structured data.",
)
def google_maps_places(
    query: str,
    location: str | None = None,
    radius_meters: int | None = 2000,
) -> list[GoogleMapsPlacesOutput]:
    """Search restaurants via Google Maps Places API and return structured data.

    Inputs:
    - query: The search query (e.g., "best sushi")
    - location: Optional lat,lng or place text to bias results
    - radius_meters: Optional radius in meters when location provided

    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise Exception("GOOGLE_MAPS_API_KEY is not set")

    def _first_photo_reference(photos: list) -> str:
        if not photos:
            return ""
        ref = photos[0].get("photo_reference") or ""
        return ref

    # We'll keep internal mapping to place_id for optional enrichment
    results_with_ids: List[Dict] = []

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
            photos = item.get("photos") or []
            photo_ref = _first_photo_reference(photos)
            place_url = (
                f"https://www.google.com/maps/search/?api=1&query_place_id={place_id}"
                if place_id
                else ""
            )

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
                        "photo_reference": photo_ref,
                        "place_url": place_url,
                    }
                )
    except Exception:
        logger.error("Failed to search for restaurants via Google Maps Places API")
        raise Exception("Failed to search for restaurants via Google Maps Places API")

    # Enrich missing price_level or reviews_count using Place Details (more reliable)
    try:
        for r in results_with_ids:
            need_price = r.get("price_level") is None
            need_reviews = r.get("reviews_count") is None
            place_id = r.get("_place_id")
            if not (need_price or need_reviews) or not place_id:
                continue
            fields = []
            if need_price:
                fields.append("price_level")
            if need_reviews:
                fields.append("user_ratings_total")
            # Also request canonical Maps URL if enriching
            fields.append("url")
            if not fields:
                continue
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
                if need_price and result.get("price_level") is not None:
                    r["price_level"] = result.get("price_level")
                if need_reviews and result.get("user_ratings_total") is not None:
                    r["reviews_count"] = result.get("user_ratings_total")
                # Prefer canonical place URL if Google returns it
                if result.get("url"):
                    r["place_url"] = result.get("url")
            except Exception:
                # Skip enrichment for this place on error
                logger.warning("Failed to enrich results via Google Maps Places API")
                continue
    except Exception:
        # If enrichment phase fails globally, we still return base results
        logger.warning("Failed to enrich results via Google Maps Places API")

    # Strip internal fields before returning
    for r in results_with_ids:
        if "_place_id" in r:
            del r["_place_id"]

    logger.info("Results are set")
    return results_with_ids
