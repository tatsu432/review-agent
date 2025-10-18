#!/usr/bin/env python3
"""
Test script to verify that the Yelp MCP tools work correctly after the fix.
This tests both individual and batch Yelp operations.
"""

import os
import sys

from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_individual_yelp_search():
    """Test individual Yelp business search."""
    print("🔍 Testing individual Yelp business search...")

    try:
        from mcp_server.yelp import yelp_business_search

        result = yelp_business_search(
            restaurant_name="Italian Restaurant", location="San Francisco, CA"
        )

        print(f"✅ Individual search working: {result.name}")
        print(f"   Rating: {result.yelp_rating}")
        print(f"   Reviews: {result.yelp_review_count}")
        print(f"   URL: {result.yelp_url}")
        print(f"   Recent reviews: {len(result.reviews)}")

        return True

    except Exception as e:
        print(f"❌ Individual search failed: {e}")
        return False


def test_batch_yelp_enhancement():
    """Test batch Yelp enhancement."""
    print("\n🔍 Testing batch Yelp enhancement...")

    try:
        from mcp_server.yelp import yelp_enhance_google_maps_results

        restaurant_names = ["Italian Restaurant", "Sushi Restaurant", "Pizza Place"]

        results = yelp_enhance_google_maps_results(
            restaurant_names=restaurant_names, location="San Francisco, CA"
        )

        print(f"✅ Batch enhancement working: {len(results)} restaurants processed")
        for i, result in enumerate(results, 1):
            print(
                f"   {i}. {result.name}: {result.yelp_rating} stars ({result.yelp_review_count} reviews)"
            )

        return True

    except Exception as e:
        print(f"❌ Batch enhancement failed: {e}")
        return False


def test_internal_function():
    """Test the internal function directly."""
    print("\n🔍 Testing internal Yelp function...")

    try:
        from mcp_server.yelp import _search_yelp_business_internal

        result = _search_yelp_business_internal(
            restaurant_name="Test Restaurant", location="San Francisco, CA"
        )

        print(f"✅ Internal function working: {result.name}")
        print(f"   Rating: {result.yelp_rating}")
        print(f"   Reviews: {result.yelp_review_count}")

        return True

    except Exception as e:
        print(f"❌ Internal function failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Yelp MCP Tools Test Suite")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Check if Yelp API key is set
    if not os.getenv("YELP_API_KEY"):
        print("❌ YELP_API_KEY not set in environment")
        return

    print("✅ Yelp API key found")
    print("=" * 50)

    # Test individual search
    individual_ok = test_individual_yelp_search()

    # Test batch enhancement
    batch_ok = test_batch_yelp_enhancement()

    # Test internal function
    internal_ok = test_internal_function()

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Individual Search: {'✅' if individual_ok else '❌'}")
    print(f"   Batch Enhancement: {'✅' if batch_ok else '❌'}")
    print(f"   Internal Function: {'✅' if internal_ok else '❌'}")

    if individual_ok and batch_ok and internal_ok:
        print("\n🎉 All Yelp tests passed! The fix is working correctly.")
        print("The 'FunctionTool object is not callable' error should be resolved.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
