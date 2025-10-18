#!/usr/bin/env python3
"""
Complete system runner that starts both the MCP server and the LangGraph agent.
This script demonstrates the proper way to run the entire system.
"""

import asyncio
import os
import subprocess
import sys
import time

from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        "OPENAI_API_KEY",
        "GOOGLE_MAPS_API_KEY",
        "YELP_API_KEY",
        "REVIEW_AGENT_MCP_SERVER_URL",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file")
        return False

    print("✅ All required environment variables are set")
    return True


def start_mcp_server():
    """Start the MCP server in the background."""
    print("🚀 Starting MCP Server...")

    # Start the MCP server as a subprocess
    mcp_process = subprocess.Popen(
        [sys.executable, "run_mcp_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait a moment for the server to start
    time.sleep(3)

    # Check if the server is running
    if mcp_process.poll() is None:
        print("✅ MCP Server started successfully")
        return mcp_process
    else:
        stdout, stderr = mcp_process.communicate()
        print("❌ Failed to start MCP server:")
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        return None


async def run_agent_example():
    """Run the LangGraph agent with an example."""
    print("\n🤖 Starting LangGraph Agent...")

    try:
        from langgraph_server.main import main as agent_main

        await agent_main()
    except Exception as e:
        print(f"❌ Agent failed: {e}")
        return False

    return True


async def main():
    """Main function to run the complete system."""
    print("🍽️  Complete Review Agent System")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Check environment
    if not check_environment():
        return

    # Start MCP server
    mcp_process = start_mcp_server()
    if not mcp_process:
        print("❌ Cannot start agent without MCP server")
        return

    try:
        # Run the agent
        print("\n" + "=" * 50)
        print("🎯 Running Agent Example")
        print("=" * 50)

        await run_agent_example()

    except KeyboardInterrupt:
        print("\n👋 Stopping system...")
    except Exception as e:
        print(f"❌ System error: {e}")
    finally:
        # Clean up MCP server
        if mcp_process:
            print("\n🛑 Stopping MCP server...")
            mcp_process.terminate()
            mcp_process.wait()
            print("✅ MCP server stopped")


if __name__ == "__main__":
    asyncio.run(main())
