#!/usr/bin/env python3
"""
Example of the enhanced review agent with Yelp integration.
This demonstrates how the agent now uses both Google Maps and Yelp data
to provide comprehensive restaurant recommendations.
"""

import asyncio
import os

from dotenv import load_dotenv

from src.langgraph_server.agent import create_agent
from src.langgraph_server.prompt import build_restaurant_prompt

load_dotenv()


async def run_enhanced_agent_example():
    """Run the enhanced agent with Yelp integration."""

    print("🚀 Enhanced Review Agent with Yelp Integration")
    print("=" * 60)

    # Check environment variables
    required_vars = ["GOOGLE_MAPS_API_KEY", "YELP_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment.")
        return

    print("✅ Environment variables configured")

    # Create the agent
    print("\n🤖 Creating enhanced agent...")
    try:
        graph = await create_agent()
        print("✅ Agent created successfully")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return

    # Thread configuration for memory
    thread_config = {
        "configurable": {
            "thread_id": "enhanced-demo-thread",
            "user_id": "demo-user",
        },
        "recursion_limit": 25,
    }

    # Example queries with different preferences
    examples = [
        {
            "location": "San Francisco, CA",
            "preferences": "Italian cuisine, romantic atmosphere, and excellent service",
        },
        {
            "location": "New York, NY",
            "preferences": "affordable sushi, fresh fish, and casual dining",
        },
        {
            "location": "Seattle, WA",
            "preferences": "coffee shops, local roasters, and cozy atmosphere",
        },
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{'=' * 60}")
        print(f"Example {i}: {example['location']}")
        print(f"Preferences: {example['preferences']}")
        print("=" * 60)

        # Build the request with location and preferences
        request = build_restaurant_prompt(
            location=example["location"],
            preferences=example["preferences"],
            language="en",  # Can be "en" for English or "jp" for Japanese
        )

        print("\n🔍 Agent is searching and analyzing...")
        print("-" * 40)

        # Stream the agent's response
        final_state = None
        async for event in graph.astream(request, config=thread_config):
            if "model" in event:
                msg = event["model"]["messages"]
                try:
                    content = getattr(msg, "content", None) or str(msg)
                except Exception:
                    content = str(msg)
                if content:
                    print(content)
            final_state = event

        print("\n" + "=" * 60)

        # Show final state for debugging
        if final_state and "agent" in final_state:
            print("\n📊 Final Agent State:")
            print("-" * 20)
            try:
                print(final_state["agent"]["messages"][-1].pretty_print())
            except Exception as e:
                print(f"Could not display final state: {e}")

        # Ask user if they want to continue
        if i < len(examples):
            input("\nPress Enter to continue to next example...")


async def run_single_query_example():
    """Run a single query example."""

    print("🎯 Single Query Example")
    print("=" * 40)

    # Create the agent
    graph = await create_agent()

    # Thread configuration
    thread_config = {
        "configurable": {
            "thread_id": "single-query-thread",
            "user_id": "demo-user",
        },
        "recursion_limit": 25,
    }

    # Single focused query
    request = build_restaurant_prompt(
        location="Tokyo, Japan",
        preferences="authentic ramen, traditional atmosphere, and local favorites",
        language="en",  # Can be "en" for English or "jp" for Japanese
    )

    print("🔍 Searching for authentic ramen in Tokyo...")
    print("-" * 40)

    # Stream the response
    async for event in graph.astream(request, config=thread_config):
        if "model" in event:
            msg = event["model"]["messages"]
            try:
                content = getattr(msg, "content", None) or str(msg)
            except Exception:
                content = str(msg)
            if content:
                print(content)


async def main():
    """Main function to run examples."""

    print("🍽️  Enhanced Review Agent Demo")
    print("Combining Google Maps + Yelp for comprehensive recommendations")
    print("=" * 70)

    # Check if we have the required API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY is required for the agent to work")
        print("Please set it in your .env file")
        return

    # Choose which example to run
    print("\nChoose an example to run:")
    print("1. Multiple examples with different preferences")
    print("2. Single focused query")

    choice = input("\nEnter your choice (1 or 2): ").strip()

    if choice == "1":
        await run_enhanced_agent_example()
    elif choice == "2":
        await run_single_query_example()
    else:
        print("Invalid choice. Running single query example...")
        await run_single_query_example()


if __name__ == "__main__":
    asyncio.run(main())
