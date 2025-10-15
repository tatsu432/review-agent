import logging
import os
from typing import Dict, List

import requests
from langchain_core.tools import tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
      name, rating, reviews_count, price_level, types, photo_url, place_url

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

    # We'll keep internal mapping to place_id for optional enrichment
    results_with_ids: List[Dict] = []

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
            reviews_count = item.get("user_ratings_total")
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
                results_with_ids.append(
                    {
                        "_place_id": place_id,
                        "name": name,
                        "rating": rating,
                        "reviews_count": reviews_count,
                        "price_level": price_level,
                        "types": types,
                        "photo_url": photo_url,
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
            if not fields:
                continue
            details_params = {
                "place_id": place_id,
                "fields": ",".join(fields),
                "key": api_key,
            }
            try:
                dresp = session.get(
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
