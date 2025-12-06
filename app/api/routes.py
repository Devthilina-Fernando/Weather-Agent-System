import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.schemas import (
    WeatherQuery,
    AgentRequest,
    AgentResponse,
    HealthResponse
)
from app.services.database import BigQueryService
from app.services.agent import WeatherAgent
from app.orchestration.scheduler import SchedulerService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
db_service = BigQueryService()
agent = WeatherAgent()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Check database connectivity
        cities = db_service.get_all_cities()
        db_healthy = len(cities) >= 0
        
        return HealthResponse(
            status="healthy" if db_healthy else "degraded",
            timestamp=datetime.utcnow(),
            services={
                "database": "healthy" if db_healthy else "unhealthy",
                "api": "healthy"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            services={
                "database": "unhealthy",
                "api": "healthy"
            }
        )


@router.get("/weather/current/{city}")
async def get_current_weather(city: str):
    """
    Get current weather for a city
    
    Args:
        city: City name
        
    Returns:
        Current weather data
    """
    try:
        weather_data = db_service.get_latest_weather(city)
        
        if not weather_data:
            raise HTTPException(
                status_code=404,
                detail=f"No weather data found for city: {city}"
            )
        
        return weather_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current weather for {city}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather/history/{city}")
async def get_weather_history(
    city: str,
    days: int = Query(7, ge=1, le=60, description="Number of days of history")
):
    """
    Get weather history for a city
    
    Args:
        city: City name
        days: Number of days of history (1-60)
        
    Returns:
        List of weather records
    """
    try:
        history = db_service.get_weather_history(city, days)
        
        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No weather history found for city: {city}"
            )
        
        return {
            "city": city,
            "days": days,
            "records": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weather history for {city}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather/average/{city}")
async def get_average_temperature(
    city: str,
    days: int = Query(7, ge=1, le=60, description="Number of days to average")
):
    """
    Get average temperature for a city
    
    Args:
        city: City name
        days: Number of days to average (1-60)
        
    Returns:
        Average temperature data
    """
    try:
        avg_temp = db_service.get_average_temperature(city, days)
        
        if avg_temp is None:
            raise HTTPException(
                status_code=404,
                detail=f"No temperature data found for city: {city}"
            )
        
        return {
            "city": city,
            "average_temperature": avg_temp,
            "period_days": days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting average temperature for {city}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather/cities")
async def get_all_cities():
    """
    Get list of all cities in database
    
    Returns:
        List of city names
    """
    try:
        cities = db_service.get_all_cities()
        
        return {
            "cities": cities,
            "count": len(cities)
        }
        
    except Exception as e:
        logger.error(f"Error getting all cities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/chat", response_model=AgentResponse)
async def chat_with_agent(request: AgentRequest):
    """
    Chat with the weather agent
    
    Args:
        request: Agent request with message and optional session_id
        
    Returns:
        Agent response
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process message with agent
        result = await agent.chat(request.message)
        
        return AgentResponse(
            response=result["response"],
            tool_calls=result.get("tool_calls"),
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error in agent chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/trigger-fetch")
async def trigger_manual_fetch():
    """
    Manually trigger a weather data fetch (admin endpoint)
    
    Returns:
        Task status
    """
    try:
        result = SchedulerService.trigger_manual_fetch()
        return result
        
    except Exception as e:
        logger.error(f"Error triggering manual fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/trigger-backfill")
async def trigger_manual_backfill(days: int = Query(60, ge=1, le=365)):
    """
    Manually trigger a backfill operation (admin endpoint)
    
    Args:
        days: Number of days to backfill
        
    Returns:
        Task status
    """
    try:
        result = SchedulerService.trigger_manual_backfill(days)
        return result
        
    except Exception as e:
        logger.error(f"Error triggering manual backfill: {e}")
        raise HTTPException(status_code=500, detail=str(e))