#!/usr/bin/env python3
"""
Test script to demonstrate the Yelp integration with Google Maps results.
This script shows how to use both MCP tools together to get enhanced restaurant data.
"""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the MCP tools
from src.mcp_server.google_maps import google_maps_places
from src.mcp_server.yelp import yelp_business_search, yelp_enhance_google_maps_results


async def test_integration():
    """Test the integration between Google Maps and Yelp MCP tools."""

    print("🔍 Testing Google Maps + Yelp Integration")
    print("=" * 50)

    # Test 1: Search for restaurants using Google Maps
    print("\n1. Searching for restaurants using Google Maps...")
    try:
        google_results = google_maps_places(
            query="Italian restaurants",
            location="San Francisco, CA",
            radius_meters=2000,
        )

        print(f"Found {len(google_results)} restaurants from Google Maps:")
        for i, restaurant in enumerate(google_results[:3], 1):  # Show first 3
            print(
                f"  {i}. {restaurant['name']} (Rating: {restaurant.get('rating', 'N/A')})"
            )

    except Exception as e:
        print(f"❌ Google Maps search failed: {e}")
        return

    # Test 2: Enhance specific restaurant with Yelp data
    if google_results:
        print(f"\n2. Enhancing '{google_results[0]['name']}' with Yelp data...")
        try:
            yelp_result = yelp_business_search(
                restaurant_name=google_results[0]["name"], location="San Francisco, CA"
            )

            print(f"✅ Yelp data for {yelp_result.name}:")
            print(f"   - Yelp Rating: {yelp_result.yelp_rating}")
            print(f"   - Review Count: {yelp_result.yelp_review_count}")
            print(f"   - Yelp URL: {yelp_result.yelp_url}")
            print(f"   - Recent Reviews: {len(yelp_result.reviews)}")

            if yelp_result.reviews:
                print("\n   Recent Reviews:")
                for review in yelp_result.reviews[:2]:  # Show first 2 reviews
                    print(
                        f"     • {review.user_name} ({review.rating}/5): {review.text[:100]}..."
                    )

        except Exception as e:
            print(f"❌ Yelp enhancement failed: {e}")

    # Test 3: Batch enhance multiple restaurants
    print(
        f"\n3. Batch enhancing {min(3, len(google_results))} restaurants with Yelp data..."
    )
    try:
        restaurant_names = [r["name"] for r in google_results[:3]]
        enhanced_results = yelp_enhance_google_maps_results(
            restaurant_names=restaurant_names, location="San Francisco, CA"
        )

        print(f"✅ Enhanced {len(enhanced_results)} restaurants:")
        for result in enhanced_results:
            print(
                f"   - {result.name}: {result.yelp_rating} stars ({result.yelp_review_count} reviews)"
            )

    except Exception as e:
        print(f"❌ Batch enhancement failed: {e}")

    print("\n🎉 Integration test completed!")


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["GOOGLE_MAPS_API_KEY", "YELP_API_KEY"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment.")
        return False

    print("✅ All required environment variables are set.")
    return True


if __name__ == "__main__":
    print("🧪 Yelp + Google Maps Integration Test")
    print("=" * 50)

    if not check_environment():
        exit(1)

    asyncio.run(test_integration())
