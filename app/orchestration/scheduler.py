import logging
from app.orchestration.tasks import (
    fetch_and_store_weather,
    backfill_historical_data
)
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SchedulerService:
    """
    Service to manage scheduled tasks
    """
    
    @staticmethod
    def initialize():
        """
        Initialize the scheduler and run startup tasks
        """
        try:
            logger.info("Initializing scheduler service")
            
            # Run backfill on startup if enabled
            if settings.backfill_on_startup:
                logger.info("Starting initial backfill task")
                backfill_historical_data.delay(days=settings.backfill_days)
            
            # Trigger initial weather fetch
            logger.info("Triggering initial weather fetch")
            fetch_and_store_weather.delay()
            
            logger.info("Scheduler service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing scheduler: {e}")
            raise
    
    @staticmethod
    def trigger_manual_fetch():
        """
        Manually trigger a weather data fetch
        """
        try:
            logger.info("Manually triggering weather fetch")
            result = fetch_and_store_weather.delay()
            return {"task_id": result.id, "status": "queued"}
        except Exception as e:
            logger.error(f"Error triggering manual fetch: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def trigger_manual_backfill(days: int = 60):
        """
        Manually trigger a backfill operation
        
        Args:
            days: Number of days to backfill
        """
        try:
            logger.info(f"Manually triggering backfill for {days} days")
            result = backfill_historical_data.delay(days=days)
            return {"task_id": result.id, "status": "queued"}
        except Exception as e:
            logger.error(f"Error triggering manual backfill: {e}")
            return {"error": str(e)}