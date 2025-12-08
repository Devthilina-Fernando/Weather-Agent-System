"""OpenWeatherMap API client"""
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional
from app.models import WeatherData, OpenWeatherResponse
from app.config import settings

logger = logging.getLogger(__name__)


class WeatherAPIClient:
    """Client for fetching weather data from OpenWeatherMap"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.timeout = httpx.Timeout(30.0)
    
    async def fetch_current_weather(self, city: str) -> Optional[WeatherData]:
        """
        Fetch current weather data for a city
        
        Args:
            city: City name
            
        Returns:
            WeatherData object or None if failed
        """
        url = f"{self.BASE_URL}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"  # Get temperature in Celsius
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._normalize_weather_data(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather for {city}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching weather for {city}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather for {city}: {str(e)}")
            return None
    
    def _normalize_weather_data(self, data: dict) -> WeatherData:
        """
        Normalize OpenWeatherMap response to WeatherData model
        
        Args:
            data: Raw API response
            
        Returns:
            WeatherData object
        """
        # Extract weather condition description
        condition = data["weather"][0]["description"] if data.get("weather") else "Unknown"
        
        # Convert Unix timestamp to datetime
        timestamp = datetime.fromtimestamp(data["dt"], tz=timezone.utc)
        
        return WeatherData(
            city=data["name"],
            timestamp=timestamp,
            temperature=round(float(data["main"]["temp"]), 2),
            humidity=int(data["main"]["humidity"]),
            wind_speed=round(float(data["wind"]["speed"]), 2),
            condition=condition
        )
    
    async def fetch_multiple_cities(self, cities: list[str]) -> list[WeatherData]:
        """
        Fetch current weather for multiple cities
        
        Args:
            cities: List of city names
            
        Returns:
            List of WeatherData objects (only successful fetches)
        """
        results = []
        
        for city in cities:
            weather_data = await self.fetch_current_weather(city)
            if weather_data:
                results.append(weather_data)
                logger.info(f"Successfully fetched weather for {city}")
            else:
                logger.warning(f"Failed to fetch weather for {city}")
        
        return results