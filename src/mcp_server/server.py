import asyncio
import logging

from fastmcp import FastMCP
from google_maps import google_maps_places_mcp
from settings import get_settings
from yelp import yelp_mcp
from taberogu import taberogu_mcp
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

mcp = FastMCP("review_agent_mcp")


def get_mcp_servers() -> list[FastMCP]:
    """Get the MCP servers."""
    return [
        google_maps_places_mcp,
        yelp_mcp,
        taberogu_mcp,
    ]


async def import_mcp_servers() -> None:
    """Create and configure the AnyAI MCP server with all necessary components."""
    servers = get_mcp_servers()
    for server in servers:
        try:
            await mcp.import_server(server, server.name)
            logger.info(f"Successfully imported server: {server.name}")
        except Exception as e:
            logger.error(f"Failed to import server {server.name}: {e}")
            raise

    logger.info(f"Successfully configured MCP with {len(servers)} servers")


async def main() -> None:
    """Main function."""
    try:
        await import_mcp_servers()
        await mcp.run_async(
            transport=settings.transport, host=settings.host, port=settings.port
        )
    except Exception as e:
        logger.error(f"Failed to run MCP: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
