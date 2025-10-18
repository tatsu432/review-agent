#!/usr/bin/env python3
"""
Example of the multilingual review agent with English and Japanese support.
This demonstrates how the agent can switch between languages and provide
appropriate responses in both English and Japanese.
"""

import asyncio
import os

from dotenv import load_dotenv

from src.langgraph_server.agent import create_agent
from src.langgraph_server.prompt import build_restaurant_prompt

load_dotenv()


async def run_english_example():
    """Run the agent with English prompts."""

    print("🇺🇸 English Example")
    print("=" * 50)

    # Create the agent
    graph = await create_agent()

    # Thread configuration
    thread_config = {
        "configurable": {
            "thread_id": "english-demo-thread",
            "user_id": "demo-user",
        },
        "recursion_limit": 25,
    }

    # English query
    request = build_restaurant_prompt(
        location="San Francisco, CA",
        preferences="Italian cuisine, romantic atmosphere, and excellent service",
        language="en",
    )

    print("🔍 Searching for Italian restaurants in San Francisco...")
    print("-" * 50)

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


async def run_japanese_example():
    """Run the agent with Japanese prompts."""

    print("\n🇯🇵 Japanese Example")
    print("=" * 50)

    # Create the agent
    graph = await create_agent()

    # Thread configuration
    thread_config = {
        "configurable": {
            "thread_id": "japanese-demo-thread",
            "user_id": "demo-user",
        },
        "recursion_limit": 25,
    }

    # Japanese query
    request = build_restaurant_prompt(
        location="新宿、東京、日本",
        preferences="本格的なラーメン、伝統的な雰囲気、地元の人気店",
        language="jp",
    )

    print("🔍 新宿で本格的なラーメン店を検索中...")
    print("-" * 50)

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


async def run_comparison_example():
    """Run both English and Japanese examples for comparison."""

    print("🔄 Language Comparison Example")
    print("=" * 60)

    # Create the agent
    graph = await create_agent()

    # Thread configuration
    thread_config = {
        "configurable": {
            "thread_id": "comparison-demo-thread",
            "user_id": "demo-user",
        },
        "recursion_limit": 25,
    }

    # English query
    print("\n🇺🇸 English Query:")
    print("Location: New York, NY")
    print("Preferences: Affordable sushi, fresh fish, and casual dining")
    print("-" * 40)

    request_en = build_restaurant_prompt(
        location="New York, NY",
        preferences="affordable sushi, fresh fish, and casual dining",
        language="en",
    )

    async for event in graph.astream(request_en, config=thread_config):
        if "model" in event:
            msg = event["model"]["messages"]
            try:
                content = getattr(msg, "content", None) or str(msg)
            except Exception:
                content = str(msg)
            if content:
                print(content)

    # Japanese query
    print("\n🇯🇵 Japanese Query:")
    print("Location: 渋谷、東京、日本")
    print("Preferences: 手頃な価格の寿司、新鮮な魚、カジュアルな雰囲気")
    print("-" * 40)

    request_jp = build_restaurant_prompt(
        location="渋谷、東京、日本",
        preferences="手頃な価格の寿司、新鮮な魚、カジュアルな雰囲気",
        language="jp",
    )

    async for event in graph.astream(request_jp, config=thread_config):
        if "model" in event:
            msg = event["model"]["messages"]
            try:
                content = getattr(msg, "content", None) or str(msg)
            except Exception:
                content = str(msg)
            if content:
                print(content)


async def run_interactive_example():
    """Run an interactive example where user can choose language and preferences."""

    print("🎯 Interactive Multilingual Example")
    print("=" * 50)

    # Get user input
    print("\nChoose your language:")
    print("1. English")
    print("2. Japanese")

    lang_choice = input("Enter your choice (1 or 2): ").strip()
    language = "jp" if lang_choice == "2" else "en"

    if language == "jp":
        print("\n場所を入力してください (例: 新宿、東京、日本):")
        location = input("Location: ").strip() or "新宿、東京、日本"

        print("\n好みを入力してください (例: 本格的なラーメン、伝統的な雰囲気):")
        preferences = (
            input("Preferences: ").strip() or "本格的なラーメン、伝統的な雰囲気"
        )
    else:
        print("\nEnter location (e.g., San Francisco, CA):")
        location = input("Location: ").strip() or "San Francisco, CA"

        print("\nEnter preferences (e.g., Italian cuisine, romantic atmosphere):")
        preferences = (
            input("Preferences: ").strip() or "Italian cuisine, romantic atmosphere"
        )

    # Create the agent
    graph = await create_agent()

    # Thread configuration
    thread_config = {
        "configurable": {
            "thread_id": f"interactive-{language}-thread",
            "user_id": "demo-user",
        },
        "recursion_limit": 25,
    }

    # Build request
    request = build_restaurant_prompt(
        location=location, preferences=preferences, language=language
    )

    print("\n🔍 Searching for restaurants...")
    print("-" * 50)

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
    """Main function to run multilingual examples."""

    print("🌍 Multilingual Review Agent Demo")
    print("Supporting English and Japanese")
    print("=" * 60)

    # Check if we have the required API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY is required for the agent to work")
        print("Please set it in your .env file")
        return

    # Choose which example to run
    print("\nChoose an example to run:")
    print("1. English example")
    print("2. Japanese example")
    print("3. Language comparison")
    print("4. Interactive example")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "1":
        await run_english_example()
    elif choice == "2":
        await run_japanese_example()
    elif choice == "3":
        await run_comparison_example()
    elif choice == "4":
        await run_interactive_example()
    else:
        print("Invalid choice. Running English example...")
        await run_english_example()


if __name__ == "__main__":
    asyncio.run(main())
