#!/usr/bin/env python3
"""
Manual backfill script for historical weather data

Note: OpenWeatherMap free tier doesn't provide historical data.
This script demonstrates the structure. For production:
1. Use OpenWeatherMap One Call API 3.0 (paid)
2. Use another historical weather data provider
3. Let data accumulate over time from hourly updates
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.weather_api import WeatherAPIService, get_cities_list
from app.services.database import BigQueryService
from app.config import get_settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def backfill_current_data():
    """
    Fetch current weather data for all cities and store it
    This serves as the starting point for historical data collection
    """
    try:
        logger.info("Starting backfill with current weather data")
        
        weather_api = WeatherAPIService()
        db_service = BigQueryService()
        
        # Get cities
        cities = get_cities_list()
        logger.info(f"Fetching weather for {len(cities)} cities")
        
        # Fetch weather data
        weather_data = await weather_api.fetch_multiple_cities(cities)
        logger.info(f"Successfully fetched weather for {len(weather_data)} cities")
        
        # Store in BigQuery
        if weather_data:
            success = db_service.insert_weather_data(weather_data)
            if success:
                logger.info(f"Successfully stored {len(weather_data)} weather records")
                return True
            else:
                logger.error("Failed to store weather data")
                return False
        
        return False
        
    except Exception as e:
        logger.error(f"Error in backfill: {e}", exc_info=True)
        return False


def main():
    """
    Main backfill function
    """
    try:
        logger.info("=" * 80)
        logger.info("Weather Data Backfill Script")
        logger.info("=" * 80)
        
        settings = get_settings()
        logger.info(f"Project ID: {settings.gcp_project_id}")
        logger.info(f"Dataset: {settings.bigquery_dataset}")
        
        # Initialize schema
        logger.info("\nInitializing BigQuery schema...")
        db_service = BigQueryService()
        db_service.initialize_schema()
        
        # Run backfill
        logger.info("\nStarting data collection...")
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(backfill_current_data())
        
        if success:
            logger.info("\n" + "=" * 80)
            logger.info("Backfill completed successfully!")
            logger.info("Historical data will build up as hourly updates run.")
            logger.info("=" * 80)
            return 0
        else:
            logger.error("\nBackfill failed")
            return 1
            
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())