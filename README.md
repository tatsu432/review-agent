# review-agent

This is a repository for the review agent where you can find the personlized restaurant from Agentic AI.

Currently, the review agent tackles the following problem
1. It is hard to decide which restaurant is suitable for you just from the review score on Google map, Yelp, Taberogu, etc because some people are more willing to give higher scores but those people might not have similar taste as you.
2. It is time consuming to read the reviews to find a restaurant that you might wanna go. The more reviews you read, the more you are confident if the restaurant is suitable for you but the time is limited.
3. The reviews might be affected by the wrong information that the restaurant has already improved upon. Thus, it is important to correct those biases so that you can find the current best restaurant. 

## Features

### Google Maps Integration
- Search for restaurants using Google Maps Places API
- Get restaurant details including ratings, review counts, price levels, and types
- Generate reliable Google Maps URLs for each restaurant

### Yelp Integration (NEW!)
- Enhance Google Maps results with Yelp business data
- Get business information including:
  - Yelp ratings and review counts
  - Business URLs and basic information
  - Comparison with Google Maps ratings
- **Smart Name Validation**: Automatically validates that Yelp results match the requested restaurant to prevent incorrect information
- **Reliability Filtering**: Only reports Yelp data when restaurant names match reliably
- Batch process multiple restaurants for comprehensive data
- Note: Individual review text is not available through the Yelp API

## Setup

### Environment Variables
Create a `.env` file in the project root with the following variables:

```bash
# Google Maps API Key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Yelp API Key
YELP_API_KEY=your_yelp_api_key_here
```

### API Keys
1. **Google Maps API**: Get your API key from [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Places API
   - Create credentials and copy the API key

2. **Yelp API**: Get your API key from [Yelp for Developers](https://www.yelp.com/developers/)
   - Create a new app
   - Copy the API key from your app settings

## Usage

### Basic Usage
```python
from src.mcp_server.google_maps import google_maps_places
from src.mcp_server.yelp import yelp_business_search

# Search for restaurants
restaurants = google_maps_places(
    query="Italian restaurants",
    location="San Francisco, CA"
)

# Enhance with Yelp data
for restaurant in restaurants:
    yelp_data = yelp_business_search(
        restaurant_name=restaurant['name'],
        location="San Francisco, CA"
    )
    print(f"{restaurant['name']}: {yelp_data.yelp_rating} stars")
```

### Enhanced Integration
```python
from src.mcp_server.yelp import yelp_enhance_google_maps_results

# Batch enhance multiple restaurants
restaurant_names = ["Restaurant A", "Restaurant B", "Restaurant C"]
enhanced_results = yelp_enhance_google_maps_results(
    restaurant_names=restaurant_names,
    location="San Francisco, CA"
)
```

### Multilingual Usage
```python
from src.langgraph_server.prompt import build_restaurant_prompt

# English query
request_en = build_restaurant_prompt(
    location="San Francisco, CA",
    preferences="Italian cuisine, romantic atmosphere",
    language="en"
)

# Japanese query
request_jp = build_restaurant_prompt(
    location="新宿、東京、日本",
    preferences="本格的なラーメン、伝統的な雰囲気",
    language="jp"
)
```

### Running the Examples

**Important**: The MCP server must be running for the agent to access the tools!

#### Step 1: Start the MCP Server
```bash
# Start the MCP server (keep this running)
./start_mcp_server.sh

# OR run directly
python run_mcp_server.py
```

#### Step 2: Run the Agent (in another terminal)
```bash
# Test the integration
python test_yelp_integration.py

# Run comprehensive example
python example_usage.py

# Run enhanced agent with Yelp integration
python example_enhanced_agent.py

# Run multilingual examples (English and Japanese)
python example_multilingual_agent.py
```

#### Quick Start
```bash
# Terminal 1: Start MCP server
./start_mcp_server.sh

# Terminal 2: Run agent
python example_multilingual_agent.py
```

## Enhanced Agent Capabilities

The review agent now uses an intelligent prompt system that:

### 🤖 Smart Recommendations
- **Dual Platform Analysis**: Compares ratings and review counts from both Google Maps and Yelp
- **Personalized Insights**: Analyzes rating patterns to understand restaurant quality
- **Comprehensive Data**: Provides detailed business information and platform comparisons

### 📊 Enhanced Output Format
The agent now provides:
- Google Maps ratings and review counts
- Yelp ratings and review counts  
- Business URLs for both Google Maps and Yelp
- Comparison between platform ratings
- Personalized insights based on rating analysis

### 🎯 Intelligent Processing
- **Automatic Enhancement**: Automatically enriches Google Maps results with Yelp data
- **Fallback Handling**: Gracefully handles cases where Yelp data isn't available
- **Batch Processing**: Efficiently processes multiple restaurants simultaneously
- **Name Validation**: Prevents hallucination by validating Yelp results match requested restaurants
- **Reliability Scoring**: Only reports Yelp data when confidence is high

### 🌍 Multilingual Support
- **English and Japanese**: Full support for both English and Japanese prompts and responses
- **Language Switching**: Easy switching between languages using the `language` parameter
- **Localized Examples**: In-context examples provided in both languages
- **Cultural Adaptation**: Responses adapted to cultural preferences and expectations

## MCP Tools Available

### Google Maps Tools
- `google_maps_places`: Search for restaurants using Google Maps Places API

### Yelp Tools
- `yelp_business_search`: Search for a specific restaurant on Yelp and get detailed review information
- `yelp_enhance_google_maps_results`: Batch enhance multiple restaurants with Yelp data

## Data Structure

### Google Maps Output
```python
{
    "name": "Restaurant Name",
    "rating": 4.5,
    "reviews_count": 150,
    "price_level": 2,
    "types": ["restaurant", "food"],
    "place_url": "https://maps.google.com/..."
}
```

### Yelp Output
```python
{
    "name": "Restaurant Name",
    "yelp_rating": 4.2,
    "yelp_review_count": 89,
    "yelp_url": "https://yelp.com/...",
    "reviews": []  # Individual reviews not available through Yelp API
}
```

## Troubleshooting

### Common Issues

**"FunctionTool object is not callable" Error**:
- This means the MCP server is not running
- Start the MCP server first: `./start_mcp_server.sh`
- Keep it running while using the agent

**Connection Issues**:
- Check that `REVIEW_AGENT_MCP_SERVER_URL` is set to `"http://0.0.0.0:8081/mcp"`
- Ensure port 8081 is not used by another process
- Verify the MCP server is running

**API Key Issues**:
- Ensure all required API keys are set in `.env`
- Check that Google Maps API has Places API enabled
- Verify Yelp API key is active

For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

Hope you enjoy talking with the review agent and we are looking forward to hearing from how you felt!
