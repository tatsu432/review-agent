# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a restaurant recommendation agent that provides personalized suggestions by analyzing reviews from multiple sources (Google Maps, Tabelog). The system uses AI to help users find restaurants that match their preferences by processing review data and correcting biases in rating systems.

## Architecture

The project consists of two main components:

### 1. LangGraph Server (`src/langgraph_server/`)
- **Agent (`agent.py`)**: Creates LangGraph ReAct agent with GPT-4o-mini, memory, and MCP tools
- **Server (`server.py`)**: FastAPI server with LINE Bot webhook integration for chat interface
- **Main (`main.py`)**: Standalone CLI runner for testing the agent locally
- **MCP Tool Loader (`mcp_tool_loader.py`)**: Manages connections to MCP servers with retry logic
- **Prompt (`prompt.py`)**: System prompts and message templates for restaurant recommendations
- **Settings (`setting.py`)**: Pydantic settings with environment variable management

### 2. MCP Server (`src/mcp_server/`)
- **Server (`server.py`)**: FastMCP server that aggregates Google Maps and Tabelog tools
- **Google Maps (`google_maps.py`)**: Google Maps Places API integration with place search and details
- **Tabelog (`taberogu.py`)**: Tabelog scraper for Japanese restaurant reviews and ratings
- **Schema (`schema.py`)**: Data models for API responses
- **Settings (`settings.py`)**: MCP server configuration

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -e .

# Activate virtual environment (if using .venv)
source .venv/bin/activate
```

### Running the System

#### 1. Start MCP Server (required first)
```bash
cd src/mcp_server
python server.py
```

#### 2. Run LangGraph Agent
```bash
# CLI mode for testing
cd src/langgraph_server
python main.py

# Server mode for LINE Bot integration
cd src/langgraph_server
python server.py
```

### Environment Variables Required

Create `.env` file with:
```
# LLM API Keys
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key (optional)

# External APIs
GOOGLE_MAPS_API_KEY=your_key
TAVILY_API_KEY=your_key

# LangSmith Tracing (optional)
LANGSMITH_API_KEY=your_key
LANGSMITH_TRACING_V2=true
LANGSMITH_PROJECT=your_project

# MCP Server Connection
REVIEW_AGENT_MCP_SERVER_URL=http://localhost:8080

# LINE Bot (for webhook mode)
LINE_CHANNEL_SECRET=your_secret
LINE_CHANNEL_ACCESS_TOKEN=your_token
```

## Testing

The project currently has no automated tests. To test:

1. Start the MCP server first
2. Run the main.py script to test agent functionality
3. Check the generated `graph.png` for workflow visualization
4. Use `/health` endpoint to verify server status

## Key Dependencies

- **LangGraph**: Agent workflow orchestration
- **FastMCP**: MCP (Model Context Protocol) server framework
- **LangChain**: LLM integration and tool management
- **FastAPI**: Web server for LINE Bot webhook
- **BeautifulSoup4**: Web scraping for Tabelog
- **Requests**: HTTP client for external APIs
- **Pydantic**: Configuration and data validation

## Architecture Notes

- The system uses MCP (Model Context Protocol) to separate tool logic from agent logic
- Restaurant data is fetched from Google Maps API and enriched with Tabelog scraping
- Agent maintains conversation memory using LangGraph's MemorySaver
- LINE Bot integration allows deployment as a chat service
- Settings use Pydantic with environment variable validation
- Error handling includes retry logic for transient MCP connection failures

## Important Patterns

- All MCP tools are loaded asynchronously with connection pooling
- Google Maps URLs are validated and canonical URLs are preferred
- Tabelog entity resolution uses fuzzy matching with confidence scoring
- LLM settings support multiple providers (OpenAI, Anthropic, Google)
- Environment variables are strictly validated with clear error messages