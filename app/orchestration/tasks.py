import logging
import asyncio
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from app.config import get_settings
from app.services.weather_api import WeatherAPIService, get_cities_list
from app.services.database import BigQueryService

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "weather_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


@celery_app.task(name="tasks.fetch_and_store_weather", bind=True, max_retries=3)
def fetch_and_store_weather(self):
    """
    Fetch current weather for all cities and store in BigQuery
    """
    try:
        logger.info("Starting hourly weather data collection")
        
        # Get services
        weather_api = WeatherAPIService()
        db_service = BigQueryService()
        
        # Get cities list
        cities = get_cities_list()
        logger.info(f"Fetching weather for {len(cities)} cities")
        
        # Fetch weather data (run async function in sync context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        weather_data = loop.run_until_complete(
            weather_api.fetch_multiple_cities(cities)
        )
        loop.close()
        
        logger.info(f"Successfully fetched weather for {len(weather_data)} cities")
        
        # Store in BigQuery
        if weather_data:
            success = db_service.insert_weather_data(weather_data)
            if success:
                logger.info(f"Successfully stored {len(weather_data)} weather records")
                return {
                    "status": "success",
                    "cities_fetched": len(weather_data),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                logger.error("Failed to store weather data")
                raise Exception("Failed to store weather data in BigQuery")
        else:
            logger.warning("No weather data fetched")
            return {
                "status": "warning",
                "message": "No weather data fetched",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error in fetch_and_store_weather: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(name="tasks.backfill_historical_data", bind=True)
def backfill_historical_data(self, days: int = 60):
    """
    Backfill historical weather data
    
    Note: OpenWeatherMap free tier doesn't provide historical data API.
    This is a placeholder that would need to be adapted based on your data source.
    For production, you would either:
    1. Use OpenWeatherMap One Call API 3.0 (paid)
    2. Start collecting from now and build history over time
    3. Use another historical weather data source
    
    Args:
        days: Number of days to backfill
    """
    try:
        logger.info(f"Starting historical data backfill for {days} days")
        
        # For this implementation, we'll simulate by just ensuring the table exists
        # and documenting that historical data will be built over time
        db_service = BigQueryService()
        db_service.initialize_schema()
        
        logger.info(
            "Historical data backfill initialized. "
            "Weather data will accumulate as hourly updates run. "
            "For immediate historical data, consider using OpenWeatherMap One Call API 3.0 (paid tier)"
        )
        
        return {
            "status": "initialized",
            "message": "Schema ready, historical data will build over time",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in backfill_historical_data: {e}")
        raise


@celery_app.task(name="tasks.cleanup_old_data")
def cleanup_old_data(retention_days: int = 90):
    """
    Clean up old weather data beyond retention period
    
    Args:
        retention_days: Number of days to retain
    """
    try:
        logger.info(f"Starting cleanup of data older than {retention_days} days")
        
        db_service = BigQueryService()
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        query = f"""
        DELETE FROM `{db_service.full_table_id}`
        WHERE timestamp < @cutoff_date
        """
        
        from google.cloud import bigquery
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("cutoff_date", "TIMESTAMP", cutoff_date)
            ]
        )
        
        query_job = db_service.client.query(query, job_config=job_config)
        query_job.result()
        
        logger.info(f"Successfully cleaned up data older than {retention_days} days")
        
        return {
            "status": "success",
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_data: {e}")
        raise


# Celery Beat Schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'fetch-weather-hourly': {
        'task': 'tasks.fetch_and_store_weather',
        'schedule': crontab(minute=0),  # Every hour at minute 0
        'options': {'queue': 'weather_queue'}
    },
    'cleanup-old-data-weekly': {
        'task': 'tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Every Sunday at 2 AM
        'options': {'queue': 'maintenance_queue'}
    },
}

celery_app.conf.task_routes = {
    'tasks.fetch_and_store_weather': {'queue': 'weather_queue'},
    'tasks.backfill_historical_data': {'queue': 'weather_queue'},
    'tasks.cleanup_old_data': {'queue': 'maintenance_queue'},
}