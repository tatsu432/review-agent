#!/usr/bin/env python3
"""
Script to run the MCP server with all the tools (Google Maps and Yelp).
This server needs to be running for the LangGraph agent to access the tools.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp_server.server import main

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    print("🚀 Starting MCP Server with Google Maps and Yelp tools...")
    print("=" * 60)
    print("This server provides the tools that the LangGraph agent needs.")
    print("Keep this running while using the agent.")
    print("=" * 60)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 MCP Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        sys.exit(1)
