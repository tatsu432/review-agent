from mcp.shared.exceptions import McpError


def is_transient(err: BaseException) -> bool:
    """Return True if error is considered transient/retryable."""
    return isinstance(err, (ConnectionError, TimeoutError, OSError)) or (
        isinstance(err, McpError) and "Session terminated" in str(err)
    )