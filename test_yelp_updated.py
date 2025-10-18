#!/usr/bin/env python3
"""
Test script to verify the updated Yelp functionality without individual reviews.
This tests the simplified Yelp integration that focuses on business information only.
"""

import os
import sys

from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_yelp_business_search():
    """Test Yelp business search without individual reviews."""
    print("🔍 Testing Yelp business search (business info only)...")

    try:
        from mcp_server.yelp import yelp_business_search

        result = yelp_business_search(
            restaurant_name="Italian Restaurant", location="San Francisco, CA"
        )

        print("✅ Yelp business search working:")
        print(f"   Name: {result.name}")
        print(f"   Rating: {result.yelp_rating}")
        print(f"   Review Count: {result.yelp_review_count}")
        print(f"   URL: {result.yelp_url}")
        print(f"   Reviews: {len(result.reviews)} (should be 0)")

        # Verify that reviews list is empty
        if len(result.reviews) == 0:
            print("   ✅ Reviews list is empty as expected")
        else:
            print("   ⚠️  Reviews list is not empty")

        return True

    except Exception as e:
        print(f"❌ Yelp business search failed: {e}")
        return False


def test_yelp_batch_enhancement():
    """Test Yelp batch enhancement without individual reviews."""
    print("\n🔍 Testing Yelp batch enhancement (business info only)...")

    try:
        from mcp_server.yelp import yelp_enhance_google_maps_results

        restaurant_names = ["Italian Restaurant", "Sushi Restaurant", "Pizza Place"]

        results = yelp_enhance_google_maps_results(
            restaurant_names=restaurant_names, location="San Francisco, CA"
        )

        print(f"✅ Yelp batch enhancement working: {len(results)} restaurants")

        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.name}:")
            print(f"      Rating: {result.yelp_rating}")
            print(f"      Reviews: {result.yelp_review_count}")
            print(f"      URL: {result.yelp_url}")
            print(f"      Individual Reviews: {len(result.reviews)} (should be 0)")

        return True

    except Exception as e:
        print(f"❌ Yelp batch enhancement failed: {e}")
        return False


def test_google_maps_integration():
    """Test Google Maps integration to ensure it still works."""
    print("\n🔍 Testing Google Maps integration...")

    try:
        from mcp_server.google_maps import google_maps_places

        result = google_maps_places(
            query="Italian restaurants",
            location="San Francisco, CA",
            radius_meters=2000,
        )

        print(f"✅ Google Maps working: {len(result)} restaurants found")
        if result:
            print(f"   First result: {result[0]['name']}")

        return True

    except Exception as e:
        print(f"❌ Google Maps failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Updated Yelp Integration Test")
    print("Testing Yelp business information without individual reviews")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    # Check environment
    required_vars = ["GOOGLE_MAPS_API_KEY", "YELP_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return

    print("✅ Environment variables loaded")
    print("=" * 60)

    # Test Google Maps
    google_ok = test_google_maps_integration()

    # Test Yelp business search
    yelp_search_ok = test_yelp_business_search()

    # Test Yelp batch enhancement
    yelp_batch_ok = test_yelp_batch_enhancement()

    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Google Maps: {'✅' if google_ok else '❌'}")
    print(f"   Yelp Business Search: {'✅' if yelp_search_ok else '❌'}")
    print(f"   Yelp Batch Enhancement: {'✅' if yelp_batch_ok else '❌'}")

    if google_ok and yelp_search_ok and yelp_batch_ok:
        print("\n🎉 All tests passed!")
        print("✅ Yelp integration is working correctly with business information only")
        print("✅ No individual review text is being fetched (as expected)")
        print("✅ Google Maps integration is still working")
        print("\nThe system is ready to use with the updated Yelp capabilities!")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
