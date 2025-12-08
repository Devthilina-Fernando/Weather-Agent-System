# Example API Queries & Results

This document shows real examples of API queries and their responses.

---

## AI Agent Queries

### Query 1: Current Weather

**Request:**
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current weather in London?"}'
```

**Response:**
```json
{
  "success": true,
  "response": "The current weather in London is as follows:\n- Temperature: 10.8°C\n- Humidity: 89%\n- Wind Speed: 4.63 m/s\n- Condition: Overcast clouds\n\n(Source: stored data)",
  "is_weather_related": true,
  "tool_calls": [
    {
      "function": "get_current_weather_from_storage",
      "arguments": {
        "city": "London"
      },
      "result": {
        "success": true,
        "city": "London",
        "timestamp": "2025-12-08T02:27:14+00:00",
        "temperature": 10.8,
        "temperature_unit": "Celsius",
        "humidity": 89,
        "humidity_unit": "percentage",
        "wind_speed": 4.63,
        "wind_speed_unit": "m/s",
        "condition": "overcast clouds",
        "source": "storage"
      }
    }
  ],
  "model": "gpt-4o-mini",
  "error": null
}
```

---

### Query 2: Historical Weather Statistics

**Request:**
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What was the average temperature in Tokyo over the last 3 days?"}'
```

**Response:**
```json
{
  "success": true,
  "response": "The average temperature in Tokyo over the last 3 days was 10.28°C. During this period, the minimum temperature recorded was 6.05°C, and the maximum temperature was 15.05°C. The average humidity was 54.0%. This data comes from stored records.",
  "is_weather_related": true,
  "tool_calls": [
    {
      "function": "get_weather_history_from_storage",
      "arguments": {
        "city": "Tokyo",
        "days": 3
      },
      "result": {
        "success": true,
        "city": "Tokyo",
        "period_days": 3,
        "record_count": 73,
        "statistics": {
          "average_temperature": 10.28,
          "min_temperature": 6.05,
          "max_temperature": 15.05,
          "average_humidity": 54,
          "temperature_unit": "Celsius",
          "humidity_unit": "percentage"
        },
        "records": [
          {
            "timestamp": "2025-12-08T02:21:11+00:00",
            "temperature": 14.48,
            "humidity": 51,
            "wind_speed": 4.63,
            "condition": "few clouds"
          },
          {
            "timestamp": "2025-12-08T01:30:22+00:00",
            "temperature": 13.17,
            "humidity": 48,
            "wind_speed": 5.14,
            "condition": "few clouds"
          },
          {
            "timestamp": "2025-12-08T00:32:15.651778+00:00",
            "temperature": 8.05,
            "humidity": 57,
            "wind_speed": 1.06,
            "condition": "clear sky"
          },
          {
            "timestamp": "2025-12-08T00:27:36+00:00",
            "temperature": 11.05,
            "humidity": 55,
            "wind_speed": 2.06,
            "condition": "clear sky"
          },
          {
            "timestamp": "2025-12-07T23:32:15.651778+00:00",
            "temperature": 8.05,
            "humidity": 57,
            "wind_speed": 3.06,
            "condition": "clear sky"
          },
          {
            "timestamp": "2025-12-07T22:32:15.651778+00:00",
            "temperature": 11.05,
            "humidity": 60,
            "wind_speed": 4.06,
            "condition": "clear sky"
          },
          {
            "timestamp": "2025-12-07T21:32:15.651778+00:00",
            "temperature": 6.05,
            "humidity": 55,
            "wind_speed": 1.06,
            "condition": "clear sky"
          },
          {
            "timestamp": "2025-12-07T20:32:15.651778+00:00",
            "temperature": 7.05,
            "humidity": 46,
            "wind_speed": 4.06,
            "condition": "clear sky"
          },
          {
            "timestamp": "2025-12-07T19:32:15.651778+00:00",
            "temperature": 7.05,
            "humidity": 56,
            "wind_speed": 4.06,
            "condition": "clear sky"
          },
          {
            "timestamp": "2025-12-07T18:32:15.651778+00:00",
            "temperature": 14.05,
            "humidity": 63,
            "wind_speed": 3.06,
            "condition": "clear sky"
          }
        ],
        "source": "storage"
      }
    }
  ],
  "model": "gpt-4o-mini",
  "error": null
}
```

---

### Query 3: Multiple Metrics

**Request:**
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Is it humid in Mumbai right now? Also tell me the wind speed."}'
```

**Response:**
```json
{
  "success": true,
  "response": "Currently, in Mumbai, the humidity is 53% and the wind speed is 2.57 m/s. The temperature is approximately 24°C, and the weather condition is haze. (Data source: storage)",
  "is_weather_related": true,
  "tool_calls": [
    {
      "function": "get_current_weather_from_storage",
      "arguments": {
        "city": "Mumbai"
      },
      "result": {
        "success": true,
        "city": "Mumbai",
        "timestamp": "2025-12-08T02:28:46+00:00",
        "temperature": 23.99,
        "temperature_unit": "Celsius",
        "humidity": 53,
        "humidity_unit": "percentage",
        "wind_speed": 2.57,
        "wind_speed_unit": "m/s",
        "condition": "haze",
        "source": "storage"
      }
    }
  ],
  "model": "gpt-4o-mini",
  "error": null
}
```

---

### Query 4: Weather Comparison

**Request:**
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the weather in Paris compare to Berlin today?"}'
```

**Response:**
```json
{
  "success": true,
  "response": "Today, the weather in Paris and Berlin is as follows:\n\n**Paris:**\n- Temperature: 14.6°C\n- Humidity: 90%\n- Wind Speed: 5.66 m/s\n- Condition: Overcast clouds\n\n**Berlin:**\n- Temperature: 7.11°C\n- Humidity: 94%\n- Wind Speed: 5.66 m/s\n- Condition: Broken clouds\n\nSource: Stored data. \n\nIn summary, Paris is significantly warmer than Berlin today, with both cities experiencing high humidity levels.",
  "is_weather_related": true,
  "tool_calls": [
    {
      "function": "get_current_weather_from_storage",
      "arguments": {
        "city": "Paris"
      },
      "result": {
        "success": true,
        "city": "Paris",
        "timestamp": "2025-12-08T02:23:45+00:00",
        "temperature": 14.6,
        "temperature_unit": "Celsius",
        "humidity": 90,
        "humidity_unit": "percentage",
        "wind_speed": 5.66,
        "wind_speed_unit": "m/s",
        "condition": "overcast clouds",
        "source": "storage"
      }
    },
    {
      "function": "get_current_weather_from_storage",
      "arguments": {
        "city": "Berlin"
      },
      "result": {
        "success": true,
        "city": "Berlin",
        "timestamp": "2025-12-08T02:29:59+00:00",
        "temperature": 7.11,
        "temperature_unit": "Celsius",
        "humidity": 94,
        "humidity_unit": "percentage",
        "wind_speed": 5.66,
        "wind_speed_unit": "m/s",
        "condition": "broken clouds",
        "source": "storage"
      }
    }
  ],
  "model": "gpt-4o-mini",
  "error": null
}
```

---

### Query 5: Non-Weather Query (Refused)

**Request:**
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

**Response:**
```json
{
  "success": true,
  "response": "I'm sorry, but I can only help with weather-related questions. Please ask me about current weather conditions, historical weather data, or weather statistics for specific cities.",
  "is_weather_related": false,
  "tool_calls": [],
  "model": null,
  "error": null
}
```

---

## Direct Weather API Queries

### Get Latest Weather for a City

**Request:**
```bash
curl http://localhost:8000/weather/latest/London
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "city": "London",
  "timestamp": "2025-12-08T10:30:00Z",
  "temperature": 8.5,
  "humidity": 81,
  "wind_speed": 6.2,
  "condition": "overcast clouds"
}
```

---

### Get Weather History

**Request:**
```bash
curl "http://localhost:8000/weather/history/Tokyo?days=3"
```

**Response:**
```json
{
  "city": "Tokyo",
  "records": [
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "city": "Tokyo",
      "timestamp": "2025-12-08T10:00:00Z",
      "temperature": 13.2,
      "humidity": 62,
      "wind_speed": 3.8,
      "condition": "clear sky"
    },
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "city": "Tokyo",
      "timestamp": "2025-12-08T09:00:00Z",
      "temperature": 12.8,
      "humidity": 64,
      "wind_speed": 3.5,
      "condition": "few clouds"
    },
    {
      "id": "d4e5f6a7-b8c9-0123-def1-234567890123",
      "city": "Tokyo",
      "timestamp": "2025-12-08T08:00:00Z",
      "temperature": 11.9,
      "humidity": 68,
      "wind_speed": 3.2,
      "condition": "scattered clouds"
    }
    // ... more records (up to 72 for 3 days)
  ],
  "count": 72
}
```

---

### Get All Cities

**Request:**
```bash
curl http://localhost:8000/weather/cities
```

**Response:**
```json
{
  "cities": [
    "London", "Paris", "Berlin", "Madrid", "Rome", "Amsterdam", "Vienna",
    "Stockholm", "Oslo", "Helsinki", "Copenhagen", "Dublin", "Brussels",
    "Lisbon", "Athens", "Warsaw", "Prague", "Budapest", "Bucharest", "Sofia",
    "Zagreb", "Belgrade", "Bratislava", "Ljubljana", "Vilnius", "Riga",
    "Tallinn", "Reykjavik", "Luxembourg", "Monaco", "Zurich", "Geneva",
    "Milan", "Venice", "Barcelona", "Valencia", "Seville", "Porto",
    "Manchester", "Birmingham", "Glasgow", "Edinburgh",
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Boston", "Portland", "Las Vegas", "Detroit",
    "Toronto", "Montreal", "Vancouver", "Calgary", "Ottawa", "Edmonton",
    "Mexico City", "Guadalajara", "Monterrey", "Cancun", "Tijuana",
    "São Paulo", "Rio de Janeiro", "Buenos Aires", "Lima", "Bogotá",
    "Santiago", "Caracas", "Brasília", "Quito", "La Paz", "Montevideo",
    "Asunción", "Medellín", "Cali", "Cartagena",
    "Tokyo", "Beijing", "Shanghai", "Mumbai", "Delhi", "Bangalore", "Kolkata",
    "Chennai", "Hyderabad", "Pune", "Seoul", "Bangkok", "Singapore",
    "Jakarta", "Manila", "Kuala Lumpur", "Ho Chi Minh City", "Hanoi",
    "Taipei", "Hong Kong", "Macau", "Osaka", "Kyoto", "Nagoya",
    "Busan", "Tel Aviv", "Jerusalem", "Dubai", "Abu Dhabi", "Doha",
    "Riyadh", "Jeddah", "Kuwait City", "Muscat", "Karachi", "Lahore",
    "Dhaka", "Colombo", "Kathmandu", "Yangon", "Phnom Penh",
    "Cairo", "Lagos", "Nairobi", "Johannesburg", "Cape Town", "Casablanca",
    "Algiers", "Tunis", "Accra", "Addis Ababa", "Dar es Salaam", "Kampala",
    "Khartoum", "Luanda", "Dakar", "Abidjan",
    "Sydney", "Melbourne", "Brisbane", "Perth", "Auckland", "Wellington",
    "Adelaide", "Canberra"
  ],
  "count": 145
}
```

---

### Health Check

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T10:30:45Z"
}
```

---

### Agent Health Check

**Request:**
```bash
curl http://localhost:8000/agent/health
```

**Response:**
```json
{
  "status": "healthy",
  "model": "gpt-4o-mini",
  "tools_available": 3
}
```

---
