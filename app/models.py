"""Pydantic models for weather data"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class WeatherData(BaseModel):
    """Normalized weather data model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    city: str
    timestamp: datetime
    temperature: float  # Celsius
    humidity: int  # Percentage
    wind_speed: float  # m/s
    condition: str  # Weather description
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "city": "London",
                "timestamp": "2024-12-07T12:00:00Z",
                "temperature": 15.5,
                "humidity": 72,
                "wind_speed": 5.2,
                "condition": "Clear sky"
            }
        }


class OpenWeatherResponse(BaseModel):
    """OpenWeatherMap API response model"""
    coord: dict
    weather: list
    base: str
    main: dict
    visibility: int
    wind: dict
    clouds: dict
    dt: int
    sys: dict
    timezone: int
    id: int
    name: str
    cod: int


class WeatherLatestResponse(BaseModel):
    """Response model for latest weather endpoint"""
    city: str
    timestamp: datetime
    temperature: float
    humidity: int
    wind_speed: float
    condition: str


class WeatherHistoryResponse(BaseModel):
    """Response model for weather history endpoint"""
    city: str
    records: list[WeatherLatestResponse]
    count: int


class AgentQueryRequest(BaseModel):
    """Request model for agent query endpoint"""
    query: str = Field(..., description="The user's weather-related question")
    conversation_history: Optional[list[dict]] = Field(
        default=None,
        description="Optional conversation history for context"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the current weather in Colombo?",
                "conversation_history": None
            }
        }


class AgentQueryResponse(BaseModel):
    """Response model for agent query endpoint"""
    success: bool
    response: str
    is_weather_related: bool
    tool_calls: list[dict] = []
    model: Optional[str] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "The current weather in Colombo is 28°C with clear skies...",
                "is_weather_related": True,
                "tool_calls": [
                    {
                        "function": "get_current_weather_from_storage",
                        "arguments": {"city": "Colombo"},
                        "result": {"success": True, "temperature": 28}
                    }
                ],
                "model": "gpt-4o-mini"
            }
        }