from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
import logging

# Load variables from .env into environment
load_dotenv()

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # OpenWeatherMap API
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY")
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"

    # Google Cloud / BigQuery
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID")
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "weather_data")
    bigquery_table: str = os.getenv("BIGQUERY_TABLE", "weather_records")
    google_application_credentials: str = "/credentials/adup-assignment-cc3101fc9d70.json"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # Application
    app_env: str = "production"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Scheduler
    hourly_update_enabled: bool = True
    backfill_on_startup: bool = True
    backfill_days: int = 60
    
    # Rate limiting
    max_retries: int = 3
    retry_delay: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()