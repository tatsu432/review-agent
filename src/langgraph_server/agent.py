import logging
from typing import Annotated, TypedDict

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from mcp_tool_loader import MCPToolLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class State(TypedDict):
    messages: Annotated[list, add_messages]


async def create_agent() -> StateGraph:
    logger.info("Creating agent")
    try:
        mcp_tool_loader = MCPToolLoader()
        async with mcp_tool_loader.get_mcp_tools() as mcp_tools:
            llm_model = init_chat_model(
                model="gpt-4o-mini",
                model_provider="openai",
                temperature=0.1,
            )
            logger.info("LLM model created")
            # Thread-aware memory so the chatbot remembers prior conversation
            memory = MemorySaver()
            logger.info("Memory created")

            graph = create_react_agent(
                model=llm_model, tools=mcp_tools, checkpointer=memory
            )
            logger.info("Graph created")

            return graph
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise
