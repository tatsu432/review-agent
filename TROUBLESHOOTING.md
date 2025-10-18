# Troubleshooting Guide

## Common Issues and Solutions

### 1. "FunctionTool object is not callable" Error

**Problem**: You see errors like:
```
WARNING:yelp:Failed to enhance Restaurant Name with Yelp data: 'FunctionTool' object is not callable
```

**Cause**: This error occurs when MCP tools try to call other MCP tools directly, which is not allowed in the MCP context.

**Solution**: 
1. **The issue has been fixed** in the latest version of the code
2. **Start the MCP server first**:
   ```bash
   # Option 1: Use the shell script
   ./start_mcp_server.sh
   
   # Option 2: Run directly
   python run_mcp_server.py
   ```

3. **Keep the MCP server running** in a separate terminal

4. **Then run your agent** in another terminal:
   ```bash
   python src/langgraph_server/main.py
   # or
   python example_multilingual_agent.py
   ```

**Technical Details**: The error was caused by the `yelp_enhance_google_maps_results` function trying to call `yelp_business_search` directly. This has been fixed by extracting the core logic into an internal function `_search_yelp_business_internal` that can be called from within MCP tools.

### 2. MCP Server Connection Issues

**Problem**: Agent cannot connect to MCP server.

**Check**:
1. **MCP Server URL**: Make sure `REVIEW_AGENT_MCP_SERVER_URL` in `.env` is correct:
   ```bash
   REVIEW_AGENT_MCP_SERVER_URL="http://0.0.0.0:8081/mcp"
   ```

2. **Port Availability**: Ensure port 8081 is not used by another process:
   ```bash
   lsof -i :8081
   ```

3. **Server Status**: Check if MCP server is running:
   ```bash
   curl http://localhost:8081/mcp
   ```

### 3. API Key Issues

**Problem**: Tools fail with authentication errors.

**Check**:
1. **Google Maps API Key**: Ensure `GOOGLE_MAPS_API_KEY` is valid and has Places API enabled
2. **Yelp API Key**: Ensure `YELP_API_KEY` is valid and active
3. **OpenAI API Key**: Ensure `OPENAI_API_KEY` is valid for the agent

### 4. Environment Variables

**Problem**: Missing or incorrect environment variables.

**Solution**: Create/update `.env` file with:
```bash
# Required for the agent
OPENAI_API_KEY="your-openai-api-key"
LANGSMITH_API_KEY="your-langsmith-key"
LANGSMITH_PROJECT="review-agent"

# Required for Google Maps
GOOGLE_MAPS_API_KEY="your-google-maps-api-key"

# Required for Yelp
YELP_API_KEY="your-yelp-api-key"

# Required for MCP server connection
REVIEW_AGENT_MCP_SERVER_URL="http://0.0.0.0:8081/mcp"
```

### 5. Running the Complete System

**Step-by-step process**:

1. **Terminal 1 - Start MCP Server**:
   ```bash
   cd /path/to/review-agent
   ./start_mcp_server.sh
   ```

2. **Terminal 2 - Run Agent**:
   ```bash
   cd /path/to/review-agent
   python example_multilingual_agent.py
   ```

### 6. Debugging Tips

**Check MCP Server Logs**:
- Look for "Successfully imported server" messages
- Check for any import errors

**Check Agent Logs**:
- Look for tool loading messages
- Check for connection errors

**Test Individual Components**:
```bash
# Test Google Maps directly
python -c "
from src.mcp_server.google_maps import google_maps_places
result = google_maps_places('Italian restaurants', 'San Francisco, CA')
print(result)
"

# Test Yelp directly
python -c "
from src.mcp_server.yelp import yelp_business_search
result = yelp_business_search('Italian Restaurant', 'San Francisco, CA')
print(result)
"
```

### 7. Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `'FunctionTool' object is not callable` | MCP server not running | Start MCP server first |
| `Connection refused` | Wrong MCP server URL | Check `REVIEW_AGENT_MCP_SERVER_URL` |
| `API key invalid` | Wrong API key | Check API keys in `.env` |
| `No tools loaded` | MCP server not accessible | Check server status and URL |

### 8. Performance Issues

**Slow Responses**:
- Check API rate limits
- Reduce number of restaurants processed
- Check network connectivity

**Memory Issues**:
- Restart MCP server periodically
- Check for memory leaks in long-running sessions

### 9. Getting Help

If you're still having issues:

1. **Check the logs** for specific error messages
2. **Verify all environment variables** are set correctly
3. **Test individual components** separately
4. **Check API quotas** and limits
5. **Restart both MCP server and agent**

## Quick Start Checklist

- [ ] `.env` file exists with all required API keys
- [ ] MCP server is running on port 8081
- [ ] Agent can connect to MCP server
- [ ] Google Maps API key is valid
- [ ] Yelp API key is valid
- [ ] OpenAI API key is valid
- [ ] No port conflicts
- [ ] Network connectivity is working
