"""Custom tools for the OpenAI weather agent"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from app.repositories.bigquery_repo import BigQueryRepository
from app.services.weather_api import WeatherAPIClient

logger = logging.getLogger(__name__)


class WeatherAgentTools:
    """Collection of tools for the weather agent"""

    def __init__(self):
        self.bigquery_repo = BigQueryRepository()
        self.weather_api = WeatherAPIClient()

    async def get_current_weather_from_storage(self, city: str) -> Dict[str, Any]:
        """
        Get the latest weather data for a city from BigQuery storage.

        Args:
            city: Name of the city (e.g., "London")

        Returns:
            Dictionary with weather information or error message
        """
        try:
            logger.info(f"Fetching current weather for {city} from storage")
            weather_data = await self.bigquery_repo.get_latest_weather(city)

            if weather_data:
                return {
                    "success": True,
                    "city": weather_data.city,
                    "timestamp": weather_data.timestamp.isoformat(),
                    "temperature": weather_data.temperature,
                    "temperature_unit": "Celsius",
                    "humidity": weather_data.humidity,
                    "humidity_unit": "percentage",
                    "wind_speed": weather_data.wind_speed,
                    "wind_speed_unit": "m/s",
                    "condition": weather_data.condition,
                    "source": "storage"
                }
            else:
                return {
                    "success": False,
                    "error": f"No weather data found for {city} in storage",
                    "city": city
                }

        except Exception as e:
            logger.error(f"Error fetching weather from storage for {city}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch weather data from storage: {str(e)}",
                "city": city
            }

    async def get_weather_history_from_storage(
        self,
        city: str,
        days: Optional[int] = 7
    ) -> Dict[str, Any]:
        """
        Get historical weather data for a city from BigQuery storage.

        Args:
            city: Name of the city (e.g., "London")
            days: Number of days of history to retrieve (default: 3)

        Returns:
            Dictionary with historical weather information or error message
        """
        try:
            logger.info(f"Fetching {days} days of weather history for {city} from storage")
            weather_records = await self.bigquery_repo.get_weather_history(city, days)

            if weather_records:
                # Calculate statistics
                temperatures = [w.temperature for w in weather_records]
                humidities = [w.humidity for w in weather_records]

                avg_temp = sum(temperatures) / len(temperatures)
                min_temp = min(temperatures)
                max_temp = max(temperatures)
                avg_humidity = sum(humidities) / len(humidities)

                return {
                    "success": True,
                    "city": city,
                    "period_days": days,
                    "record_count": len(weather_records),
                    "statistics": {
                        "average_temperature": round(avg_temp, 2),
                        "min_temperature": round(min_temp, 2),
                        "max_temperature": round(max_temp, 2),
                        "average_humidity": round(avg_humidity, 2),
                        "temperature_unit": "Celsius",
                        "humidity_unit": "percentage"
                    },
                    "records": [
                        {
                            "timestamp": w.timestamp.isoformat(),
                            "temperature": w.temperature,
                            "humidity": w.humidity,
                            "wind_speed": w.wind_speed,
                            "condition": w.condition
                        }
                        for w in weather_records[:10]  # Return max 10 detailed records
                    ],
                    "source": "storage"
                }
            else:
                return {
                    "success": False,
                    "error": f"No weather history found for {city} in the last {days} days",
                    "city": city
                }

        except Exception as e:
            logger.error(f"Error fetching weather history from storage for {city}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch weather history from storage: {str(e)}",
                "city": city
            }

    async def get_current_weather_from_api(self, city: str) -> Dict[str, Any]:
        """
        Fallback: Get current weather data directly from OpenWeatherMap API.
        This is used when storage query fails.

        Args:
            city: Name of the city

        Returns:
            Dictionary with weather information or error message
        """
        try:
            logger.info(f"Fetching current weather for {city} from OpenWeatherMap API (fallback)")
            weather_data = await self.weather_api.fetch_current_weather(city)

            if weather_data:
                return {
                    "success": True,
                    "city": weather_data.city,
                    "timestamp": weather_data.timestamp.isoformat(),
                    "temperature": weather_data.temperature,
                    "temperature_unit": "Celsius",
                    "humidity": weather_data.humidity,
                    "humidity_unit": "percentage",
                    "wind_speed": weather_data.wind_speed,
                    "wind_speed_unit": "m/s",
                    "condition": weather_data.condition,
                    "source": "OpenWeatherMap API (live)"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to fetch weather data from API for {city}",
                    "city": city
                }

        except Exception as e:
            logger.error(f"Error fetching weather from API for {city}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch weather data from API: {str(e)}",
                "city": city
            }


# Tool function definitions for OpenAI function calling
def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get the OpenAI function calling tool definitions.

    Returns:
        List of tool definitions in OpenAI format
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather_from_storage",
                "description": "Get the current weather for a city from stored data. Use this as the primary method to retrieve weather information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The name of the city (e.g., 'Colombo', 'Galle', 'London')"
                        }
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather_history_from_storage",
                "description": "Get historical weather data and statistics for a city from stored data. Use this to answer questions about past weather patterns, averages, or trends.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The name of the city (e.g., 'Colombo', 'Galle', 'London')"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days of history to retrieve (default: 7)",
                            "default": 7
                        }
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_current_weather_from_api",
                "description": "FALLBACK ONLY: Get current weather directly from OpenWeatherMap API. Use this only when the storage query fails or returns no data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The name of the city"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]
