#!/usr/bin/env python3
"""
Test script to verify that the MCP server is working correctly.
This script tests the MCP tools directly to ensure they're accessible.
"""

import os
import sys

from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_google_maps():
    """Test Google Maps MCP tool directly."""
    print("🔍 Testing Google Maps MCP tool...")

    try:
        from mcp_server.google_maps import google_maps_places

        result = google_maps_places(
            query="Italian restaurants",
            location="San Francisco, CA",
            radius_meters=2000,
        )

        print(f"✅ Google Maps tool working: Found {len(result)} restaurants")
        if result:
            print(f"   First result: {result[0]['name']}")
        return True

    except Exception as e:
        print(f"❌ Google Maps tool failed: {e}")
        return False


def test_yelp():
    """Test Yelp MCP tool directly."""
    print("🔍 Testing Yelp MCP tool...")

    try:
        from mcp_server.yelp import yelp_business_search

        result = yelp_business_search(
            restaurant_name="Italian Restaurant", location="San Francisco, CA"
        )

        print(f"✅ Yelp tool working: {result.name}")
        print(f"   Rating: {result.yelp_rating}")
        print(f"   Reviews: {result.yelp_review_count}")
        return True

    except Exception as e:
        print(f"❌ Yelp tool failed: {e}")
        return False


def test_mcp_server_connection():
    """Test if MCP server is accessible."""
    print("🔍 Testing MCP server connection...")

    try:
        import requests

        mcp_url = os.getenv("REVIEW_AGENT_MCP_SERVER_URL", "http://0.0.0.0:8081/mcp")

        # Try to connect to the MCP server
        response = requests.get(mcp_url, timeout=5)

        if response.status_code == 200:
            print("✅ MCP server is accessible")
            return True
        else:
            print(f"❌ MCP server returned status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MCP server - is it running?")
        return False
    except Exception as e:
        print(f"❌ MCP server connection failed: {e}")
        return False


def check_environment():
    """Check if all required environment variables are set."""
    print("🔍 Checking environment variables...")

    required_vars = [
        "GOOGLE_MAPS_API_KEY",
        "YELP_API_KEY",
        "OPENAI_API_KEY",
        "REVIEW_AGENT_MCP_SERVER_URL",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False

    print("✅ All required environment variables are set")
    return True


def main():
    """Main test function."""
    print("🧪 MCP Server Test Suite")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed")
        return

    print("\n" + "=" * 50)

    # Test MCP server connection
    if not test_mcp_server_connection():
        print("\n❌ MCP server is not running or not accessible")
        print("Please start the MCP server first:")
        print("  ./start_mcp_server.sh")
        print("  OR")
        print("  python run_mcp_server.py")
        return

    print("\n" + "=" * 50)

    # Test individual tools
    google_ok = test_google_maps()
    yelp_ok = test_yelp()

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("   Environment: ✅")
    print("   MCP Server: ✅")
    print(f"   Google Maps: {'✅' if google_ok else '❌'}")
    print(f"   Yelp: {'✅' if yelp_ok else '❌'}")

    if google_ok and yelp_ok:
        print("\n🎉 All tests passed! The MCP server is working correctly.")
        print("You can now run the agent examples.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        print("Make sure all API keys are valid and the MCP server is running.")


if __name__ == "__main__":
    main()
