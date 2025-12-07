# Weather Agent System - AI Agentic Workflow Documentation

## Overview

This Weather Agent System implements an AI-powered conversational agent using the OpenAI API with function calling capabilities. The agent can answer weather-related queries by intelligently using custom tools to fetch data from BigQuery storage or fall back to the OpenWeatherMap API when needed.

## Features

### 1. Agent Implementation

The agent is implemented using the OpenAI API (GPT-4o-mini model) with function calling capabilities:

- **Location**: [app/services/weather_agent.py](app/services/weather_agent.py)
- **Model**: `gpt-4o-mini` (cost-effective with function calling support)
- **Architecture**: Asynchronous Python implementation with FastAPI integration

### 2. Custom Tools

Three custom tools are available to the agent:

#### a) `get_current_weather_from_storage` (Primary)
- **Purpose**: Fetch the latest weather data for a city from BigQuery storage
- **Source**: BigQuery weather data repository
- **Use Case**: Primary method for current weather queries

#### b) `get_weather_history_from_storage`
- **Purpose**: Fetch historical weather data with statistics (average, min, max temperatures)
- **Source**: BigQuery weather data repository
- **Use Case**: Questions about past weather patterns and trends
- **Parameters**:
  - `city`: City name
  - `days`: Number of days of history (default: 7)

#### c) `get_current_weather_from_api` (Fallback)
- **Purpose**: Fetch current weather directly from OpenWeatherMap API
- **Source**: OpenWeatherMap API (live data)
- **Use Case**: Fallback when storage query fails or returns no data

**Tool Definitions**: [app/services/agent_tools.py](app/services/agent_tools.py)

### 3. Tool Call Reliability with Fallback

The agent implements automatic fallback mechanisms:

1. **Primary Path**: Agent attempts to fetch data from BigQuery storage first
2. **Fallback Path**: If storage query fails or returns no data, the agent automatically falls back to the OpenWeatherMap API
3. **Error Handling**: Each tool returns structured success/error responses that the agent can interpret and act upon

Example workflow:
```
User Query → Agent → Try get_current_weather_from_storage
                  ↓ (if fails)
                  → Fallback to get_current_weather_from_api
                  ↓
                  → Return natural language response
```

### 4. Guardrails

Multiple layers of guardrails ensure the agent only answers weather-related questions:

#### Layer 1: LLM-based Classification
- **Method**: Separate LLM call to classify if query is weather-related
- **Location**: `_check_if_weather_related()` in [app/services/weather_agent.py](app/services/weather_agent.py:178)
- **Response**: Returns refusal message for non-weather queries

#### Layer 2: System Prompt Instructions
- **Method**: Detailed system prompt with explicit guardrail instructions
- **Location**: `SYSTEM_PROMPT` in [app/services/weather_agent.py](app/services/weather_agent.py:18)
- **Content**: Instructs the model to refuse non-weather queries politely

#### Refusal Response Example
```
"I'm sorry, but I can only help with weather-related questions.
Please ask me about current weather conditions, historical weather data,
or weather statistics for specific cities."
```

## API Endpoints

### POST `/agent/query`

Query the weather agent with natural language questions.

**Request Body**:
```json
{
  "query": "What is the current weather in Colombo?",
  "conversation_history": null
}
```

**Response**:
```json
{
  "success": true,
  "response": "The current weather in Colombo is 28°C with clear skies...",
  "is_weather_related": true,
  "tool_calls": [
    {
      "function": "get_current_weather_from_storage",
      "arguments": {"city": "Colombo"},
      "result": {"success": true, "temperature": 28, ...}
    }
  ],
  "model": "gpt-4o-mini"
}
```

### GET `/agent/health`

Check the health status of the agent service.

**Response**:
```json
{
  "status": "healthy",
  "model": "gpt-4o-mini",
  "tools_available": 3
}
```

## Example Queries

### Weather-Related Queries (Accepted)

1. **Current Weather**:
   - "What is the current weather in Colombo?"
   - "How's the weather in London right now?"
   - "Is it raining in Tokyo?"

2. **Historical Data**:
   - "What was the average temperature in Galle last week?"
   - "Show me the weather history for Paris over the last 30 days"
   - "What was the temperature trend in New York last month?"

3. **Specific Metrics**:
   - "How humid is it in Mumbai?"
   - "What's the wind speed in Sydney?"
   - "Tell me about the temperature and conditions in Berlin"

### Non-Weather Queries (Refused)

- "What's the capital of France?" → Refused
- "Who won the game yesterday?" → Refused
- "Tell me a joke" → Refused
- "What's the stock price of Tesla?" → Refused

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# OpenWeatherMap API Configuration
OPENWEATHER_API_KEY=your-openweathermap-api-key-here

# Google Cloud BigQuery Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
GCP_PROJECT_ID=your-gcp-project-id
BIGQUERY_DATASET=weather_data
BIGQUERY_TABLE=weather_records
```

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## Architecture

```
User Query
    ↓
FastAPI Endpoint (/agent/query)
    ↓
WeatherAgent.process_query()
    ↓
├── Check if weather-related (Guardrail)
│   ├── YES → Continue
│   └── NO → Return refusal message
    ↓
OpenAI API (with function calling)
    ↓
├── Tool Call: get_current_weather_from_storage
│   ├── SUCCESS → Return data
│   └── FAIL → Try fallback
│       ↓
│       Tool Call: get_current_weather_from_api
│       ├── SUCCESS → Return data
│       └── FAIL → Return error
    ↓
OpenAI API (final response generation)
    ↓
Natural Language Response to User
```

## Key Files

- [app/services/weather_agent.py](app/services/weather_agent.py) - Main agent implementation
- [app/services/agent_tools.py](app/services/agent_tools.py) - Custom tool definitions
- [app/routes/agent.py](app/routes/agent.py) - FastAPI endpoints
- [app/models.py](app/models.py) - Request/Response models
- [app/config.py](app/config.py) - Configuration management

## Testing

You can test the agent using curl:

```bash
# Test weather query
curl -X POST "http://localhost:8000/agent/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current weather in Colombo?"}'

# Test non-weather query (should be refused)
curl -X POST "http://localhost:8000/agent/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of Sri Lanka?"}'

# Test historical query
curl -X POST "http://localhost:8000/agent/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What was the average temperature in Galle last week?"}'
```

Or use the interactive API documentation at `http://localhost:8000/docs`

## Cost Optimization

- Uses `gpt-4o-mini` model for cost-effectiveness
- Implements caching through BigQuery storage to minimize API calls
- Only falls back to OpenWeatherMap API when necessary
- Efficient tool calling reduces token usage

## Security Considerations

- API keys stored in environment variables
- Guardrails prevent prompt injection attacks
- Input validation on all endpoints
- Rate limiting recommended for production use

## Future Enhancements

- Conversation memory for multi-turn dialogues
- Support for weather forecasts
- Integration with additional weather data sources
- Caching layer for frequently asked questions
- User authentication and rate limiting
