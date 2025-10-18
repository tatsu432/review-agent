import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # This loads the .env file

from agent import create_agent
from fastapi import FastAPI, Request
from langchain_core.messages import HumanMessage
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LINE Bot API v3 setup
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Global agent variable
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    yield
    # Cleanup code can go here if needed


# --- FastAPI app with lifespan ---
app = FastAPI(lifespan=lifespan)


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
    
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Please check your channel secret.")
        return "Invalid signature", 400
    
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
async def handle_message(event):
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
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
    )
