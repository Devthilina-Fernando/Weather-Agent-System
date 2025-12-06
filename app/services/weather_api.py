import httpx
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings
from app.models.schemas import WeatherData

logger = logging.getLogger(__name__)
settings = get_settings()


class WeatherAPIService:
    """Service for interacting with OpenWeatherMap API"""
    
    def __init__(self):
        self.api_key = settings.openweather_api_key
        self.base_url = settings.openweather_base_url
        self.timeout = 30.0
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_current_weather(self, city: str, country: Optional[str] = None) -> Optional[WeatherData]:
        """
        Fetch current weather data for a city
        
        Args:
            city: City name
            country: Optional country code (ISO 3166)
            
        Returns:
            WeatherData object or None if failed
        """
        try:
            query = f"{city},{country}" if country else city
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "q": query,
                        "appid": self.api_key,
                        "units": "metric"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return self._parse_weather_data(data)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather for {city}: {e}")
            if e.response.status_code == 404:
                logger.warning(f"City not found: {city}")
            return None
        except Exception as e:
            logger.error(f"Error fetching weather for {city}: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_weather_by_coords(self, lat: float, lon: float) -> Optional[WeatherData]:
        """
        Fetch current weather data by coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            WeatherData object or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.api_key,
                        "units": "metric"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return self._parse_weather_data(data)
                
        except Exception as e:
            logger.error(f"Error fetching weather for coords ({lat}, {lon}): {e}")
            return None
    
    def _parse_weather_data(self, data: dict) -> WeatherData:
        """
        Parse API response into WeatherData object
        
        Args:
            data: Raw API response
            
        Returns:
            WeatherData object
        """
        return WeatherData(
            city=data["name"],
            country=data["sys"]["country"],
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            temp_min=data["main"]["temp_min"],
            temp_max=data["main"]["temp_max"],
            pressure=data["main"]["pressure"],
            humidity=data["main"]["humidity"],
            wind_speed=data["wind"]["speed"],
            wind_deg=data["wind"].get("deg"),
            clouds=data["clouds"]["all"],
            condition=data["weather"][0]["main"],
            description=data["weather"][0]["description"],
            timestamp=datetime.utcfromtimestamp(data["dt"])
        )
    
    async def fetch_multiple_cities(self, cities: List[tuple]) -> List[WeatherData]:
        """
        Fetch weather data for multiple cities
        
        Args:
            cities: List of (city, country) tuples
            
        Returns:
            List of WeatherData objects
        """
        results = []
        for city, country in cities:
            weather_data = await self.fetch_current_weather(city, country)
            if weather_data:
                results.append(weather_data)
                logger.info(f"Fetched weather for {city}, {country}")
            else:
                logger.warning(f"Failed to fetch weather for {city}, {country}")
        
        return results


# List of 100+ cities worldwide
CITIES_LIST = [
    ("Tokyo", "JP"), ("Delhi", "IN"), ("Shanghai", "CN"), ("Sao Paulo", "BR"),
    ("Mumbai", "IN"), ("Mexico City", "MX"), ("Beijing", "CN"), ("Osaka", "JP"),
    ("Cairo", "EG"), ("New York", "US"), ("Dhaka", "BD"), ("Karachi", "PK"),
    ("Buenos Aires", "AR"), ("Istanbul", "TR"), ("Kolkata", "IN"), ("Manila", "PH"),
    ("Lagos", "NG"), ("Rio de Janeiro", "BR"), ("Tianjin", "CN"), ("Kinshasa", "CD"),
    ("Guangzhou", "CN"), ("Los Angeles", "US"), ("Moscow", "RU"), ("Shenzhen", "CN"),
    ("Lahore", "PK"), ("Bangalore", "IN"), ("Paris", "FR"), ("Bogota", "CO"),
    ("Jakarta", "ID"), ("Chennai", "IN"), ("Lima", "PE"), ("Bangkok", "TH"),
    ("Seoul", "KR"), ("Nagoya", "JP"), ("Hyderabad", "IN"), ("London", "GB"),
    ("Tehran", "IR"), ("Chicago", "US"), ("Chengdu", "CN"), ("Nanjing", "CN"),
    ("Wuhan", "CN"), ("Ho Chi Minh City", "VN"), ("Luanda", "AO"), ("Ahmedabad", "IN"),
    ("Kuala Lumpur", "MY"), ("Xi'an", "CN"), ("Hong Kong", "HK"), ("Dongguan", "CN"),
    ("Hangzhou", "CN"), ("Foshan", "CN"), ("Shenyang", "CN"), ("Riyadh", "SA"),
    ("Baghdad", "IQ"), ("Santiago", "CL"), ("Surat", "IN"), ("Madrid", "ES"),
    ("Suzhou", "CN"), ("Pune", "IN"), ("Harbin", "CN"), ("Houston", "US"),
    ("Dallas", "US"), ("Toronto", "CA"), ("Dar es Salaam", "TZ"), ("Miami", "US"),
    ("Belo Horizonte", "BR"), ("Singapore", "SG"), ("Philadelphia", "US"), ("Atlanta", "US"),
    ("Fukuoka", "JP"), ("Khartoum", "SD"), ("Barcelona", "ES"), ("Johannesburg", "ZA"),
    ("Saint Petersburg", "RU"), ("Qingdao", "CN"), ("Dalian", "CN"), ("Washington", "US"),
    ("Yangon", "MM"), ("Alexandria", "EG"), ("Jinan", "CN"), ("Guadalajara", "MX"),
    ("Colombo", "LK"), ("Galle", "LK"), ("Kandy", "LK"), ("Jaffna", "LK"),
    ("Negombo", "LK"), ("Matara", "LK"), ("Sydney", "AU"), ("Melbourne", "AU"),
    ("Brisbane", "AU"), ("Perth", "AU"), ("Adelaide", "AU"), ("Dubai", "AE"),
    ("Abu Dhabi", "AE"), ("Doha", "QA"), ("Kuwait City", "KW"), ("Muscat", "OM"),
    ("Beirut", "LB"), ("Amman", "JO"), ("Jerusalem", "IL"), ("Tel Aviv", "IL"),
    ("Athens", "GR"), ("Rome", "IT"), ("Milan", "IT"), ("Naples", "IT"),
    ("Berlin", "DE"), ("Munich", "DE"), ("Hamburg", "DE"), ("Frankfurt", "DE"),
    ("Vienna", "AT"), ("Zurich", "CH"), ("Geneva", "CH"), ("Brussels", "BE"),
    ("Amsterdam", "NL"), ("Stockholm", "SE"), ("Copenhagen", "DK"), ("Oslo", "NO")
]


def get_cities_list() -> List[tuple]:
    """Get the list of cities to track"""
    return CITIES_LIST