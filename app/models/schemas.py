from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class WeatherCondition(str, Enum):
    CLEAR = "Clear"
    CLOUDS = "Clouds"
    RAIN = "Rain"
    DRIZZLE = "Drizzle"
    THUNDERSTORM = "Thunderstorm"
    SNOW = "Snow"
    MIST = "Mist"
    SMOKE = "Smoke"
    HAZE = "Haze"
    DUST = "Dust"
    FOG = "Fog"
    SAND = "Sand"
    ASH = "Ash"
    SQUALL = "Squall"
    TORNADO = "Tornado"


class WeatherData(BaseModel):
    """Schema for weather data from API"""
    city: str
    country: str
    temperature: float = Field(..., description="Temperature in Celsius")
    feels_like: float = Field(..., description="Feels like temperature in Celsius")
    temp_min: float
    temp_max: float
    pressure: int = Field(..., description="Atmospheric pressure in hPa")
    humidity: int = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    wind_deg: Optional[int] = Field(None, description="Wind direction in degrees")
    clouds: int = Field(..., description="Cloudiness percentage")
    condition: str = Field(..., description="Weather condition")
    description: str = Field(..., description="Weather description")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('temperature', 'feels_like', 'temp_min', 'temp_max')
    def round_temperature(cls, v):
        return round(v, 2)
    
    @validator('wind_speed')
    def round_wind_speed(cls, v):
        return round(v, 2)


class WeatherRecord(WeatherData):
    """Schema for weather record in database (includes ID)"""
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WeatherQuery(BaseModel):
    """Schema for weather query requests"""
    city: str = Field(..., min_length=2, max_length=100)
    days: Optional[int] = Field(1, ge=1, le=60, description="Number of days of history")

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    services: dict


class CityConfig(BaseModel):
    """Schema for city configuration"""
    name: str
    country: str
    lat: float
    lon: float