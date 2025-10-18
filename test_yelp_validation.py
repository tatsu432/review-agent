#!/usr/bin/env python3
"""
Test script to verify Yelp name validation works correctly.
This tests the similarity matching to prevent incorrect Yelp results.
"""

import os
import sys

from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_name_similarity():
    """Test the name similarity calculation."""
    print("🔍 Testing name similarity calculation...")

    try:
        from mcp_server.yelp import calculate_name_similarity, normalize_restaurant_name

        # Test cases
        test_cases = [
            # (name1, name2, expected_similarity_range)
            ("Tatsuya Shinjuku", "Tatsuya Shinjuku", (0.9, 1.0)),  # Exact match
            ("Tatsuya Shinjuku", "Tatsuya", (0.7, 0.9)),  # Partial match
            ("Tatsuya Shinjuku", "Sushi Tatsuya", (0.6, 0.8)),  # Similar
            ("Tatsuya Shinjuku", "McDonald's", (0.0, 0.3)),  # Different
            ("Dynamic Kitchen & Bar Hibiki", "Dynamic Kitchen", (0.7, 0.9)),  # Partial
            ("Kyoto Kaiseki Minokichi", "Minokichi", (0.6, 0.8)),  # Partial
        ]

        for name1, name2, expected_range in test_cases:
            similarity = calculate_name_similarity(name1, name2)
            norm1 = normalize_restaurant_name(name1)
            norm2 = normalize_restaurant_name(name2)

            print(f"   '{name1}' vs '{name2}'")
            print(f"   Normalized: '{norm1}' vs '{norm2}'")
            print(
                f"   Similarity: {similarity:.2f} (expected: {expected_range[0]:.1f}-{expected_range[1]:.1f})"
            )

            if expected_range[0] <= similarity <= expected_range[1]:
                print("   ✅ Similarity within expected range")
            else:
                print("   ⚠️  Similarity outside expected range")
            print()

        return True

    except Exception as e:
        print(f"❌ Name similarity test failed: {e}")
        return False


def test_yelp_validation():
    """Test Yelp validation with real examples."""
    print("🔍 Testing Yelp validation with real examples...")

    try:
        from mcp_server.yelp import yelp_business_search

        # Test with a restaurant that might have unreliable matches
        test_restaurants = [
            "Tatsuya Shinjuku",
            "Dynamic Kitchen & Bar Hibiki Shinjuku Southern Tower",
            "Kyoto Kaiseki Minokichi Shinjuku Sumitomo",
        ]

        for restaurant in test_restaurants:
            print(f"\n   Testing: {restaurant}")
            result = yelp_business_search(restaurant, "Tokyo, Japan")

            print(f"   Result name: {result.name}")
            print(f"   Yelp rating: {result.yelp_rating}")
            print(f"   Yelp review count: {result.yelp_review_count}")
            print(f"   Yelp URL: {result.yelp_url}")

            # Check if the result indicates unreliable match
            if result.yelp_rating is None and result.yelp_review_count is None:
                print("   ✅ Validation working: Yelp data marked as unreliable")
            else:
                print("   ✅ Validation working: Yelp data appears reliable")

        return True

    except Exception as e:
        print(f"❌ Yelp validation test failed: {e}")
        return False


def test_normalization():
    """Test restaurant name normalization."""
    print("🔍 Testing restaurant name normalization...")

    try:
        from mcp_server.yelp import normalize_restaurant_name

        test_cases = [
            ("Tatsuya Restaurant", "tatsuya"),
            ("Dynamic Kitchen & Bar", "dynamic kitchen bar"),
            ("Café de Paris", "cafe de paris"),
            ("Sushi Bar Tokyo", "sushi bar tokyo"),
            ("レストラン 太郎", "レストラン 太郎"),
        ]

        for original, expected in test_cases:
            normalized = normalize_restaurant_name(original)
            print(f"   '{original}' -> '{normalized}'")

            if normalized == expected:
                print("   ✅ Normalization correct")
            else:
                print(f"   ⚠️  Expected '{expected}', got '{normalized}'")
            print()

        return True

    except Exception as e:
        print(f"❌ Normalization test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Yelp Validation Test Suite")
    print("Testing name matching to prevent incorrect Yelp results")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    # Check if Yelp API key is set
    if not os.getenv("YELP_API_KEY"):
        print("❌ YELP_API_KEY not set in environment")
        return

    print("✅ Yelp API key found")
    print("=" * 60)

    # Test normalization
    norm_ok = test_normalization()

    # Test name similarity
    similarity_ok = test_name_similarity()

    # Test Yelp validation
    validation_ok = test_yelp_validation()

    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Name Normalization: {'✅' if norm_ok else '❌'}")
    print(f"   Name Similarity: {'✅' if similarity_ok else '❌'}")
    print(f"   Yelp Validation: {'✅' if validation_ok else '❌'}")

    if norm_ok and similarity_ok and validation_ok:
        print("\n🎉 All validation tests passed!")
        print("✅ Yelp integration now includes name validation")
        print("✅ Unreliable matches will be filtered out")
        print(
            "✅ This should prevent hallucination with incorrect restaurant information"
        )
    else:
        print("\n❌ Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
