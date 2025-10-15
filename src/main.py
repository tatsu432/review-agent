from dotenv import load_dotenv

load_dotenv()  # This loads the .env file

import os

from agent import create_agent
from prompt import build_restaurant_prompt


def main():
    graph = create_agent()

    graph.get_graph().draw_mermaid_png(output_file_path="graph.png")

    # Thread-aware config: persist messages per user/thread for memory
    thread_config = {
        "configurable": {
            "thread_id": os.getenv("THREAD_ID", "demo-thread"),
            "user_id": os.getenv("USER_ID", "demo-user"),
        }
    }

    # Build request from prompt template (flexible by location)
    request = build_restaurant_prompt(location="Shinjuku, Tokyo, Japan")

    # Stream with cleaner output while capturing inner state
    print("=== Streaming Agent Output ===")
    final_state = None
    for event in graph.stream(request, config=thread_config):
        if "model" in event:
            msg = event["model"]["messages"]
            try:
                content = getattr(msg, "content", None) or str(msg)
            except Exception:
                content = str(msg)
            if content:
                print(content)
        final_state = event

    print("\n=== Final Inner State Snapshot ===")
    print(final_state)


if __name__ == "__main__":
    main()
