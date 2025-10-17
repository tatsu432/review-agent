import asyncio
import os

from agent import create_agent
from dotenv import load_dotenv
from prompt import build_restaurant_prompt

load_dotenv()  # This loads the .env file


async def main() -> None:
    graph = await create_agent()

    graph.get_graph().draw_mermaid_png(output_file_path="graph.png")

    # Thread-aware config: persist messages per user/thread for memory
    thread_config = {
        "configurable": {
            "thread_id": os.getenv("THREAD_ID", "demo-thread"),
            "user_id": os.getenv("USER_ID", "demo-user"),
        },
        "recursion_limit": 25,
    }

    # Build request from prompt template (flexible by location)
    request = build_restaurant_prompt(location="Shinjuku, Tokyo, Japan")

    # Stream with cleaner output while capturing inner state
    print("=== Streaming Agent Output ===")
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

    # await graph.ainvoke(request, config=thread_config)

    print("\n=== Final Inner State Snapshot ===")
    print(final_state["agent"]["messages"][-1].pretty_print())


if __name__ == "__main__":
    asyncio.run(main())
