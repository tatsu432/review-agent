# mcp_restaurant_search.py
from db_search import get_restaurant_by_name
from fastmcp import FastMCP
from schema import (
    TaberoguNameLookupOutput,
)

taberogu_mcp = FastMCP("taberogu_mcp")

@taberogu_mcp.tool(
    name="taberogu_get_by_name",
    description="Retrieve a single restaurant by name using vector similarity over names; returns None if below threshold.",
)
def taberogu_get_by_name(name: str, min_score: float = 0.6) -> TaberoguNameLookupOutput:
    return get_restaurant_by_name(name, min_score)
