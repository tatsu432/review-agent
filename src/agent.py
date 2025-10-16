import logging
from typing import Annotated, TypedDict

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent, ReactAgent

from tool import (
    google_maps_places,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def create_agent() -> ReactAgent:
    logger.info("Creating agent")

    tools = [
        google_maps_places,
    ]

    llm_model = init_chat_model(
        model="gpt-4o-mini",
        model_provider="openai",
        temperature=0.1,
    )
    # Thread-aware memory so the chatbot remembers prior conversation
    memory = MemorySaver()
    logger.info("Memory created")

    graph = create_react_agent(model=llm_model, tools=tools, checkpointer=memory)
    logger.info("Graph created")

    return graph
