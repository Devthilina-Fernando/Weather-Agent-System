"""Configuration management for weather pipeline"""
from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv
import os

# Load variables from .env into environment
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenWeatherMap API
    OPENWEATHER_API_KEY: str
    
    # Google BigQuery
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "adup-assignment")
    BIGQUERY_DATASET: str = os.getenv("BIGQUERY_DATASET", "weather_data")
    BIGQUERY_TABLE: str = os.getenv("BIGQUERY_TABLE", "weather_records")
    
    # Application
    BACKFILL_MONTHS: int = 2
    UPDATE_INTERVAL_HOURS: int = 1
    
    # Cities to track
    CITIES: List[str] = [
        "London", "Paris", "New York", "Tokyo", "Beijing", "Moscow", "Berlin",
        "Madrid", "Rome", "Amsterdam", "Vienna", "Stockholm", "Oslo", "Helsinki",
        "Copenhagen", "Dublin", "Brussels", "Lisbon", "Athens", "Warsaw"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()