# AI Agent Documentation

AI-powered conversational agent using OpenAI GPT-4o-mini with function calling to answer weather queries.

---

## Agent Features

### Model
- **GPT-4o-mini**: Cost-effective with excellent function calling
- **Implementation**: [app/services/weather_agent.py](app/services/weather_agent.py)
- **Architecture**: Async Python with FastAPI

### Three Custom Tools

#### 1. `get_current_weather_from_storage` (Primary)
- Fetches latest weather from BigQuery
- Use case: Current weather queries
- Example: "What's the weather in London?"

#### 2. `get_weather_history_from_storage`
- Fetches historical data with statistics (avg, min, max temperature)
- Parameters: `city`, `days` (default: 3)
- Example: "What was the average temperature in Tokyo last 3 days?"

#### 3. `get_current_weather_from_api` (Fallback)
- Fetches from OpenWeatherMap API when storage fails
- Ensures high availability

**Tool definitions**: [app/services/agent_tools.py](app/services/agent_tools.py)

### Automatic Fallback
```
User Query → Try BigQuery → (if fails) → Try OpenWeatherMap API → Response
```

### Two-Layer Guardrails

**Layer 1**: Pre-classification
- Separate LLM call checks if query is weather-related
- Refuses non-weather queries immediately

**Layer 2**: System prompt enforcement
- Instructs model to only answer weather questions
- Polite refusal for off-topic queries

**Example Refusal**:
```
"I'm sorry, but I can only help with weather-related questions.
Please ask me about current weather conditions, historical weather data,
or weather statistics for specific cities."
```

---

## API Usage

### Query the Agent

**Endpoint**: `POST /agent/query`

**Request**:
```json
{
  "query": "What is the current weather in Colombo?"
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
      "result": {"success": true, "temperature": 28}
    }
  ],
  "model": "gpt-4o-mini"
}
```

### Agent Health Check

**Endpoint**: `GET /agent/health`

**Response**:
```json
{
  "status": "healthy",
  "model": "gpt-4o-mini",
  "tools_available": 3
}
```

---

## Example Queries

### ✅ Accepted (Weather-Related)

- "What is the current weather in Colombo?"
- "How's the weather in London right now?"
- "What was the average temperature in Tokyo yesterday?"
- "Show me the weather history for Paris over the last 3 days"
- "Is it raining in Mumbai?"
- "How humid is it in Sydney?"
- "What's the wind speed in Berlin?"

### ❌ Refused (Non-Weather)

- "What's the capital of France?"
- "Tell me a joke"
- "What's the stock price of Tesla?"
- "Who won the game yesterday?"

---

## Testing

### Using curl

**Weather query**:
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current weather in London?"}'
```

**Non-weather query** (should be refused):
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of Sri Lanka?"}'
```

**Historical query**:
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What was the average temperature in Tokyo yesterday?"}'
```

### Interactive Documentation

Visit: http://localhost:8000/docs

---

## Architecture

### Complete System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION & STORAGE                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌───────────────────────────────────────┐
        │  OpenWeatherMap API (every hour)      │
        │  - Fetch 145 cities                   │
        │  - Temperature, humidity, wind, etc.  │
        └───────────────────────────────────────┘
                              ↓
        ┌───────────────────────────────────────┐
        │      APScheduler (Orchestration)      │
        │  - Backfill: 3 days at startup        │
        │  - Hourly: Update all cities          │
        └───────────────────────────────────────┘
                              ↓
        ┌───────────────────────────────────────┐
        │     BigQuery Storage (Clustered)      │
        │  - weather_records table              │
        │  - Clustered by [city, timestamp]     │
        │  - ~10,440 records (3 days)           │
        └───────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    AI AGENT QUERY WORKFLOW                       │
└─────────────────────────────────────────────────────────────────┘

User Query (Natural Language)
    ↓
Weather-Related Check (Guardrail Layer 1)
    ├── NO → Refusal message
    └── YES → Continue
    ↓
OpenAI GPT-4o-mini (with function calling)
    ↓
Execute Tool (with fallback)
    ├── Try: get_current_weather_from_storage
    │         ↓
    │   BigQuery Repository
    │         ↓
    │   Query weather_records table
    │
    └── Fallback: get_current_weather_from_api
              ↓
        OpenWeatherMap API (live)
    ↓
Natural Language Response
```

---

## Cost Optimization

- Uses GPT-4o-mini (~$6/month for 1000 queries/day)
- Caches data in BigQuery to minimize API calls
- Falls back to live API only when necessary

---

**Implementation Files**:
- [app/services/weather_agent.py](app/services/weather_agent.py) - Agent logic
- [app/services/agent_tools.py](app/services/agent_tools.py) - Tool definitions
- [app/routes/agent.py](app/routes/agent.py) - API endpoints
