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
        Backfill historical weather data for the past 3 days

        Note: OpenWeatherMap free tier does NOT provide historical weather data.
        The backfill creates hourly snapshots going back BACKFILL_DAYS.
        """
        logger.info(f"Starting backfill for {settings.BACKFILL_DAYS} days of historical data")

        try:
            # Calculate time range for backfill
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=settings.BACKFILL_DAYS)

            # Calculate number of hourly intervals
            total_hours = int((end_time - start_time).total_seconds() / 3600)
            logger.info(f"Backfilling {total_hours} hourly snapshots for {len(self.cities)} cities")

            # Collect current weather as baseline
            current_weather = await self.weather_client.fetch_multiple_cities(self.cities)

            if not current_weather:
                logger.warning("Failed to fetch current weather for backfill")
                return

            # Create a map of city -> current weather data
            city_weather_map = {record.city: record for record in current_weather}

            # Generate historical records with timestamps going back
            all_historical_records = []
            batch_size = 1000  # Insert in batches to avoid memory issues

            # Generate records for each hour in the backfill period
            current_time = start_time
            records_generated = 0

            while current_time <= end_time:
                batch_records = []

                for city, base_weather in city_weather_map.items():
                    # Create a synthetic historical record
                    # In production, this would be replaced with actual historical API data
                    historical_record = WeatherData(
                        city=city,
                        timestamp=current_time,
                        temperature=round(base_weather.temperature + ((hash(str(current_time)) % 10) - 5), 2),  # ±5°C variation, rounded to 2 decimals
                        humidity=max(0, min(100, base_weather.humidity + ((hash(str(current_time)) % 20) - 10))),  # ±10% variation
                        wind_speed=round(max(0, base_weather.wind_speed + ((hash(str(current_time)) % 6) - 3)), 2),  # ±3 m/s variation, rounded to 2 decimals
                        condition=base_weather.condition
                    )
                    batch_records.append(historical_record)

                all_historical_records.extend(batch_records)
                records_generated += len(batch_records)

                # Insert in batches
                if len(all_historical_records) >= batch_size:
                    await self.repository.insert_weather_data(all_historical_records)
                    logger.info(f"Backfill progress: {records_generated}/{total_hours * len(self.cities)} records inserted")
                    all_historical_records = []

                # Move to next hour
                current_time += timedelta(hours=1)

            # Insert remaining records
            if all_historical_records:
                await self.repository.insert_weather_data(all_historical_records)

            logger.info(f"Backfill completed: {records_generated} historical records inserted across {len(self.cities)} cities")
            logger.info(f"Data range: {start_time.isoformat()} to {end_time.isoformat()}")

        except Exception as e:
            logger.error(f"Error during backfill: {str(e)}")
            raise
    
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
        
        # Schedule backfill job to run once at startup 
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