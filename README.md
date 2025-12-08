# Weather Agent System

AI-powered weather data pipeline that collects, stores, and intelligently serves weather information for 145 cities worldwide using OpenAI GPT-4o-mini and Google BigQuery.

## Features

- **Automated Data Collection**: Hourly weather updates for 145 cities
- **BigQuery Storage**: Scalable cloud storage with 3-day historical backfill
- **AI Agent**: Natural language queries with GPT-4o-mini
- **REST API**: FastAPI endpoints with automatic documentation
- **Docker**: Single-command deployment

## Quick Start

### Step 1: Add Credentials

1. **Get the `.env` file from the email** and place it in the project root:
   ```
   Weather-Agent-System/
   └── .env
   ```

2. **Get the `adup-assignment-cc3101fc9d70.json` file from the email** and place it in the `credentials/` folder:
   ```
   Weather-Agent-System/
   └── credentials/
       └── adup-assignment-cc3101fc9d70.json
   ```

### Step 2: Run with Docker

```bash
docker-compose up --build
```

That's it! The system will:
- Start the API server on http://localhost:8000
- Run 3-day historical backfill (~30-60 seconds)
- Begin hourly weather updates automatically

## Usage

### Interactive API Documentation
Visit: http://localhost:8000/docs

### Example Queries

**AI Agent** (Natural language):
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current weather in London?"}'
```

**Direct API** (Programmatic):
```bash
# Get latest weather
curl http://localhost:8000/weather/latest/London

# Get 7-day history
curl http://localhost:8000/weather/history/London?days=7

# List all cities
curl http://localhost:8000/weather/cities
```

### Example AI Queries
- "What is the current weather in Colombo?"
- "What was the average temperature in Tokyo yesterday?"
- "How humid is it in Mumbai?"
- "Show me the weather history for Paris over the last 3 days"

## What Happens After Startup

1. **Backfill** (30-60 sec): Generates 3 days of historical data (~10,440 records)
2. **Hourly Updates**: Fetches current weather for all 145 cities every hour
3. **AI Agent**: Ready to answer weather queries in natural language

## Monitored Cities

145 cities across:

Full list in [app/config.py](app/config.py)

## Tech Stack

- **Python 3.11** + FastAPI
- **OpenAI GPT-4o-mini** (AI agent with function calling)
- **Google BigQuery** (serverless data warehouse)
- **APScheduler** (background jobs)
- **Docker** (containerization)

## Documentation

- [DB_SCHEMA.md](DB_SCHEMA.md) - Database schema and design
- [RATIONALE.md](RATIONALE.md) - Technology choices and architecture
- [AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md) - AI agent details

## Troubleshooting

**Container won't start?**
- Check `.env` file is in project root
- Check `adup-assignment-cc3101fc9d70.json` is in `credentials/` folder
- View logs: `docker-compose logs -f`

**API errors?**
- Verify API keys in `.env` are valid
- Ensure Google credentials have BigQuery Admin role

## Stopping the System

```bash
docker-compose down
```

---

