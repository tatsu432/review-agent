#!/usr/bin/env python3
"""
Test script to verify MCP tools work directly without the server.
This helps isolate whether the issue is with the MCP server or the tools themselves.
"""

import os
import sys

from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_google_maps_direct():
    """Test Google Maps tool directly."""
    print("🔍 Testing Google Maps tool directly...")

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


def test_yelp_direct():
    """Test Yelp tools directly."""
    print("\n🔍 Testing Yelp tools directly...")

    try:
        from mcp_server.yelp import (
            yelp_business_search,
            yelp_enhance_google_maps_results,
        )

        # Test individual search
        print("   Testing individual search...")
        result1 = yelp_business_search("Italian Restaurant", "San Francisco, CA")
        print(f"   ✅ Individual search: {result1.name}")

        # Test batch enhancement
        print("   Testing batch enhancement...")
        result2 = yelp_enhance_google_maps_results(
            ["Italian Restaurant", "Sushi Restaurant"], "San Francisco, CA"
        )
        print(f"   ✅ Batch enhancement: {len(result2)} restaurants")

        return True

    except Exception as e:
        print(f"❌ Yelp tools failed: {e}")
        return False


def test_mcp_server_import():
    """Test that MCP server can be imported and configured."""
    print("\n🔍 Testing MCP server import...")

    try:
        from mcp_server.server import get_mcp_servers

        servers = get_mcp_servers()
        print(f"✅ MCP servers found: {len(servers)}")
        for server in servers:
            print(f"   - {server.name}")

        return True

    except Exception as e:
        print(f"❌ MCP server import failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Direct MCP Tools Test")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Check environment
    required_vars = ["GOOGLE_MAPS_API_KEY", "YELP_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return

    print("✅ Environment variables loaded")
    print("=" * 50)

    # Test Google Maps
    google_ok = test_google_maps_direct()

    # Test Yelp
    yelp_ok = test_yelp_direct()

    # Test MCP server
    mcp_ok = test_mcp_server_import()

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Google Maps: {'✅' if google_ok else '❌'}")
    print(f"   Yelp Tools: {'✅' if yelp_ok else '❌'}")
    print(f"   MCP Server: {'✅' if mcp_ok else '❌'}")

    if google_ok and yelp_ok and mcp_ok:
        print("\n🎉 All direct tests passed!")
        print("The tools themselves are working correctly.")
        print("The issue was likely in the MCP server communication.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
