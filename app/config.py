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

    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Google BigQuery
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "adup-assignment")
    BIGQUERY_DATASET: str = os.getenv("BIGQUERY_DATASET", "weather_data")
    BIGQUERY_TABLE: str = os.getenv("BIGQUERY_TABLE", "weather_records")
    
    # Application
    BACKFILL_DAYS: int = 3  # 3 days of historical data
    UPDATE_INTERVAL_HOURS: int = 1
    
    # Cities to track 
    CITIES: List[str] = [
        # Europe
        "London", "Paris", "Berlin", "Madrid", "Rome", "Amsterdam", "Vienna",
        "Stockholm", "Oslo", "Helsinki", "Copenhagen", "Dublin", "Brussels",
        "Lisbon", "Athens", "Warsaw", "Prague", "Budapest", "Bucharest", "Sofia",
        "Zagreb", "Belgrade", "Bratislava", "Ljubljana", "Vilnius", "Riga",
        "Tallinn", "Reykjavik", "Luxembourg", "Monaco", "Zurich", "Geneva",
        "Milan", "Venice", "Barcelona", "Valencia", "Seville", "Porto",
        "Manchester", "Birmingham", "Glasgow", "Edinburgh",

        # North America
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
        "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
        "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
        "Seattle", "Denver", "Boston", "Portland", "Las Vegas", "Detroit",
        "Toronto", "Montreal", "Vancouver", "Calgary", "Ottawa", "Edmonton",
        "Mexico City", "Guadalajara", "Monterrey", "Cancun", "Tijuana",

        # South America
        "São Paulo", "Rio de Janeiro", "Buenos Aires", "Lima", "Bogotá",
        "Santiago", "Caracas", "Brasília", "Quito", "La Paz", "Montevideo",
        "Asunción", "Medellín", "Cali", "Cartagena",

        # Asia
        "Tokyo", "Beijing", "Shanghai", "Mumbai", "Delhi", "Bangalore", "Kolkata",
        "Chennai", "Hyderabad", "Pune", "Seoul", "Bangkok", "Singapore",
        "Jakarta", "Manila", "Kuala Lumpur", "Ho Chi Minh City", "Hanoi",
        "Taipei", "Hong Kong", "Macau", "Osaka", "Kyoto", "Nagoya",
        "Busan", "Tel Aviv", "Jerusalem", "Dubai", "Abu Dhabi", "Doha",
        "Riyadh", "Jeddah", "Kuwait City", "Muscat", "Karachi", "Lahore",
        "Dhaka", "Colombo", "Kathmandu", "Yangon", "Phnom Penh",

        # Africa
        "Cairo", "Lagos", "Nairobi", "Johannesburg", "Cape Town", "Casablanca",
        "Algiers", "Tunis", "Accra", "Addis Ababa", "Dar es Salaam", "Kampala",
        "Khartoum", "Luanda", "Dakar", "Abidjan",

        # Oceania
        "Sydney", "Melbourne", "Brisbane", "Perth", "Auckland", "Wellington",
        "Adelaide", "Canberra"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()