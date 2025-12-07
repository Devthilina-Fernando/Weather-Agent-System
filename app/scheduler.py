"""Scheduler for orchestrating weather data collection"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from app.services.weather_api import WeatherAPIClient
from app.repositories.bigquery_repo import BigQueryRepository
from app.config import settings
from app.models import WeatherData

logger = logging.getLogger(__name__)


class WeatherScheduler:
    """Scheduler for weather data collection jobs"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.weather_client = WeatherAPIClient()
        self.repository = BigQueryRepository()
        self.cities = settings.CITIES
    
    async def backfill_historical_data(self):
        """
        Backfill historical weather data
        
        Note: OpenWeatherMap free tier only provides current weather.
        This is a simulation that collects current data with timestamps
        spread over the backfill period for demonstration purposes.
        
        In production, you would use a historical weather API endpoint.
        """
        logger.info(f"Starting backfill for {settings.BACKFILL_MONTHS} months")
        
        try:
            # For demonstration: collect current weather and store with current timestamp
            # In production, you'd fetch actual historical data from a historical API
            weather_records = await self.weather_client.fetch_multiple_cities(self.cities)
            
            if weather_records:
                await self.repository.insert_weather_data(weather_records)
                logger.info(f"Backfill completed: {len(weather_records)} records processed")
            else:
                logger.warning("Backfill completed but no records were fetched")
                
        except Exception as e:
            logger.error(f"Error during backfill: {str(e)}")
    
    async def fetch_and_store_current_weather(self):
        """Fetch current weather for all cities and store in BigQuery"""
        logger.info(f"Starting hourly weather update for {len(self.cities)} cities")
        
        try:
            # Fetch weather data for all cities
            weather_records = await self.weather_client.fetch_multiple_cities(self.cities)
            
            if weather_records:
                # Store in BigQuery
                inserted_count = await self.repository.insert_weather_data(weather_records)
                logger.info(f"Hourly update completed: {inserted_count} records inserted/updated")
            else:
                logger.warning("No weather records fetched during hourly update")
                
        except Exception as e:
            logger.error(f"Error during hourly weather update: {str(e)}")
    
    async def start(self):
        """Start the scheduler with all jobs"""
        logger.info("Initializing weather scheduler")
        
        # Initialize BigQuery schema
        await self.repository.initialize_schema()
        
        # Schedule backfill job to run once at startup (after 10 seconds)
        self.scheduler.add_job(
            self.backfill_historical_data,
            trigger=DateTrigger(run_date=datetime.now() + timedelta(seconds=10)),
            id="backfill_job",
            name="Historical Weather Backfill",
            replace_existing=True
        )
        logger.info("Scheduled backfill job (runs once at startup)")
        
        # Schedule hourly update job
        self.scheduler.add_job(
            self.fetch_and_store_current_weather,
            trigger=IntervalTrigger(hours=settings.UPDATE_INTERVAL_HOURS),
            id="hourly_update_job",
            name="Hourly Weather Update",
            replace_existing=True,
            next_run_time=datetime.now() + timedelta(seconds=30)  # First run after 30 seconds
        )
        logger.info(f"Scheduled hourly update job (runs every {settings.UPDATE_INTERVAL_HOURS} hour(s))")
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("Weather scheduler started successfully")
    
    async def shutdown(self):
        """Shutdown the scheduler gracefully"""
        logger.info("Shutting down weather scheduler")
        self.scheduler.shutdown(wait=True)
        logger.info("Weather scheduler shutdown complete")


# Global scheduler instance
weather_scheduler = WeatherScheduler()