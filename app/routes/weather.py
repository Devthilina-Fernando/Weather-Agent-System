"""API routes for weather data endpoints"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
import logging
from app.repositories.bigquery_repo import BigQueryRepository
from app.models import WeatherLatestResponse, WeatherHistoryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["weather"])


def get_repository():
    """Dependency for BigQuery repository"""
    return BigQueryRepository()


@router.get("/latest/{city}", response_model=WeatherLatestResponse)
async def get_latest_weather(city: str):
    """
    Get the latest weather data for a specific city
    
    Args:
        city: City name
        
    Returns:
        Latest weather data for the city
        
    Raises:
        HTTPException: If city not found or error occurs
    """
    repository = get_repository()
    
    try:
        weather_data = await repository.get_latest_weather(city)
        
        if not weather_data:
            raise HTTPException(
                status_code=404,
                detail=f"No weather data found for city: {city}"
            )
        
        return WeatherLatestResponse(
            city=weather_data.city,
            timestamp=weather_data.timestamp,
            temperature=weather_data.temperature,
            humidity=weather_data.humidity,
            wind_speed=weather_data.wind_speed,
            condition=weather_data.condition
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest weather for {city}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/history/{city}", response_model=WeatherHistoryResponse)
async def get_weather_history(
    city: str,
    days: int = Query(default=7, ge=1, le=60, description="Number of days of history to retrieve")
):
    """
    Get weather history for a specific city
    
    Args:
        city: City name
        days: Number of days of history (1-60)
        
    Returns:
        Historical weather data for the city
        
    Raises:
        HTTPException: If error occurs
    """
    repository = get_repository()
    
    try:
        weather_records = await repository.get_weather_history(city, days)
        
        records_response = [
            WeatherLatestResponse(
                city=record.city,
                timestamp=record.timestamp,
                temperature=record.temperature,
                humidity=record.humidity,
                wind_speed=record.wind_speed,
                condition=record.condition
            )
            for record in weather_records
        ]
        
        return WeatherHistoryResponse(
            city=city,
            records=records_response,
            count=len(records_response)
        )
        
    except Exception as e:
        logger.error(f"Error fetching weather history for {city}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/cities", response_model=List[str])
async def get_tracked_cities():
    """
    Get list of all tracked cities
    
    Returns:
        List of city names
    """
    from app.config import settings
    return settings.CITIES