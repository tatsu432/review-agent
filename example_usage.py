#!/usr/bin/env python3
"""
Example usage of the enhanced review agent with Google Maps + Yelp integration.
This demonstrates how to get comprehensive restaurant information.
"""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the MCP tools
from src.mcp_server.google_maps import google_maps_places
from src.mcp_server.yelp import yelp_business_search


async def get_comprehensive_restaurant_info(query: str, location: str = None):
    """
    Get comprehensive restaurant information by combining Google Maps and Yelp data.

    Args:
        query: Search query for restaurants
        location: Location to search in

    Returns:
        List of dictionaries with comprehensive restaurant information
    """
    print(f"🔍 Searching for '{query}' in {location or 'any location'}")
    print("=" * 60)

    # Step 1: Get restaurants from Google Maps
    print("\n1️⃣ Getting restaurants from Google Maps...")
    try:
        google_results = google_maps_places(
            query=query, location=location, radius_meters=2000
        )

        if not google_results:
            print("❌ No restaurants found on Google Maps")
            return []

        print(f"✅ Found {len(google_results)} restaurants from Google Maps")

    except Exception as e:
        print(f"❌ Google Maps search failed: {e}")
        return []

    # Step 2: Enhance each restaurant with Yelp data
    print("\n2️⃣ Enhancing restaurants with Yelp data...")
    enhanced_results = []

    for i, restaurant in enumerate(google_results[:5], 1):  # Limit to first 5 for demo
        print(
            f"\n   📍 Processing {i}/{min(5, len(google_results))}: {restaurant['name']}"
        )

        try:
            # Get Yelp data for this restaurant
            yelp_data = yelp_business_search(
                restaurant_name=restaurant["name"], location=location
            )

            # Combine Google Maps and Yelp data
            enhanced_restaurant = {
                # Google Maps data
                "name": restaurant["name"],
                "google_rating": restaurant.get("rating"),
                "google_reviews_count": restaurant.get("reviews_count"),
                "google_price_level": restaurant.get("price_level"),
                "google_types": restaurant.get("types", []),
                "google_url": restaurant.get("place_url"),
                # Yelp data
                "yelp_rating": yelp_data.yelp_rating,
                "yelp_review_count": yelp_data.yelp_review_count,
                "yelp_url": yelp_data.yelp_url,
                "yelp_reviews": [
                    {
                        "text": review.text,
                        "rating": review.rating,
                        "user": review.user_name,
                        "date": review.time_created,
                        "url": review.url,
                    }
                    for review in yelp_data.reviews
                ],
            }

            enhanced_results.append(enhanced_restaurant)

            print("      ✅ Enhanced with Yelp data")
            print(
                f"         Google: {restaurant.get('rating', 'N/A')} stars ({restaurant.get('reviews_count', 0)} reviews)"
            )
            print(
                f"         Yelp: {yelp_data.yelp_rating or 'N/A'} stars ({yelp_data.yelp_review_count or 0} reviews)"
            )

        except Exception as e:
            print(f"      ⚠️  Yelp enhancement failed: {e}")
            # Still include the restaurant with just Google Maps data
            enhanced_restaurant = {
                "name": restaurant["name"],
                "google_rating": restaurant.get("rating"),
                "google_reviews_count": restaurant.get("reviews_count"),
                "google_price_level": restaurant.get("price_level"),
                "google_types": restaurant.get("types", []),
                "google_url": restaurant.get("place_url"),
                "yelp_rating": None,
                "yelp_review_count": None,
                "yelp_url": None,
                "yelp_reviews": [],
            }
            enhanced_results.append(enhanced_restaurant)

    return enhanced_results


def display_results(results):
    """Display the enhanced restaurant results in a nice format."""
    if not results:
        print("❌ No results to display")
        return

    print(f"\n🎉 Enhanced Results ({len(results)} restaurants)")
    print("=" * 60)

    for i, restaurant in enumerate(results, 1):
        print(f"\n{i}. 🍽️  {restaurant['name']}")
        print("   " + "─" * 50)

        # Google Maps info
        print("   📍 Google Maps:")
        print(f"      Rating: {restaurant['google_rating'] or 'N/A'} stars")
        print(f"      Reviews: {restaurant['google_reviews_count'] or 0}")
        print(f"      Price Level: {restaurant['google_price_level'] or 'N/A'}")
        print(f"      Types: {', '.join(restaurant['google_types'][:3])}")
        if restaurant["google_url"]:
            print(f"      URL: {restaurant['google_url']}")

        # Yelp info
        print("   🟡 Yelp:")
        if restaurant["yelp_rating"]:
            print(f"      Rating: {restaurant['yelp_rating']} stars")
            print(f"      Reviews: {restaurant['yelp_review_count']}")
            if restaurant["yelp_url"]:
                print(f"      URL: {restaurant['yelp_url']}")

            # Show recent reviews
            if restaurant["yelp_reviews"]:
                print(f"      Recent Reviews ({len(restaurant['yelp_reviews'])}):")
                for review in restaurant["yelp_reviews"][:2]:  # Show first 2
                    print(
                        f"         • {review['user']} ({review['rating']}/5): {review['text'][:80]}..."
                    )
        else:
            print("      No Yelp data available")


async def main():
    """Main function to demonstrate the enhanced review agent."""
    print("🚀 Enhanced Review Agent Demo")
    print("Combining Google Maps + Yelp for comprehensive restaurant data")
    print("=" * 70)

    # Check environment variables
    required_vars = ["GOOGLE_MAPS_API_KEY", "YELP_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment.")
        return

    print("✅ Environment variables configured")

    # Example searches
    examples = [
        ("Italian restaurants", "San Francisco, CA"),
        ("Sushi", "New York, NY"),
        ("Coffee shops", "Seattle, WA"),
    ]

    for query, location in examples:
        print(f"\n{'=' * 70}")
        results = await get_comprehensive_restaurant_info(query, location)
        display_results(results)

        # Ask user if they want to continue
        if query != examples[-1][0]:  # Not the last example
            input("\nPress Enter to continue to next example...")


if __name__ == "__main__":
    asyncio.run(main())
