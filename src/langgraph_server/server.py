import logging
import os

from dotenv import load_dotenv

load_dotenv()  # This loads the .env file

from agent import create_agent
from fastapi import FastAPI, Request
from langchain_core.messages import HumanMessage
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET"))


# --- FastAPI app ---
app = FastAPI()

agent = None


@app.on_event("startup")
async def startup() -> None:
    global agent
    try:
        agent = await create_agent()
        logger.info("Agent created successfully")
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        logger.error(
            "Make sure the MCP server is running at the URL specified in REVIEW_AGENT_MCP_SERVER_URL"
        )
        raise


@app.get("/health")
async def health():
    """Health check endpoint"""
    if agent is None:
        return {"status": "unhealthy", "message": "Agent not initialized"}
    return {"status": "healthy", "message": "Agent is ready"}


@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    events = parser.parse(body.decode("utf-8"), signature)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_message = event.message.text

            # make a stable thread id
            src = event.source
            thread_id = (
                f"user:{getattr(src, 'user_id', None)}"
                or f"group:{getattr(src, 'group_id', None)}"
                or f"room:{getattr(src, 'room_id', None)}"
                or f"reply:{event.reply_token}"  # last-resort fallback
            )

            config = {"configurable": {"thread_id": thread_id}}

            # Use async invocation since MCP tools are async
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=user_message)]}, config=config
            )

            reply_text = result["messages"][-1].content
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text=reply_text)
            )

    return "OK"
