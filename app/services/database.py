import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.auth.exceptions import DefaultCredentialsError
from app.config import get_settings
from app.models.schemas import WeatherData, WeatherRecord

logger = logging.getLogger(__name__)
settings = get_settings()


class BigQueryService:
    """Service for interacting with BigQuery"""

    def __init__(self):
        try:
            # Check if credentials file exists
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_path and not os.path.exists(creds_path):
                logger.error(f"Credentials file not found at: {creds_path}")
                logger.error("Please add your GCP service account JSON file to the credentials/ directory")
                raise FileNotFoundError(f"Google Cloud credentials file not found: {creds_path}")

            self.client = bigquery.Client(project=settings.gcp_project_id)
            self.dataset_id = settings.bigquery_dataset
            self.table_id = settings.bigquery_table
            self.full_table_id = f"{settings.gcp_project_id}.{self.dataset_id}.{self.table_id}"
            logger.info(f"BigQuery client initialized for project: {settings.gcp_project_id}")
        except DefaultCredentialsError as e:
            logger.error("Google Cloud credentials not found!")
            logger.error("Please set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            logger.error("or place credentials file in credentials/ directory")
            raise
        except Exception as e:
            logger.error(f"Error initializing BigQuery client: {e}")
            raise
        
    def initialize_schema(self):
        """
        Initialize BigQuery dataset and table with proper schema
        """
        try:
            # Create dataset if not exists
            dataset = bigquery.Dataset(f"{settings.gcp_project_id}.{self.dataset_id}")
            dataset.location = "US"
            
            try:
                self.client.get_dataset(dataset.dataset_id)
                logger.info(f"Dataset {self.dataset_id} already exists")
            except NotFound:
                dataset = self.client.create_dataset(dataset, timeout=30)
                logger.info(f"Created dataset {self.dataset_id}")
            
            # Define table schema
            schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("city", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("country", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("temperature", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("feels_like", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("temp_min", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("temp_max", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("pressure", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("humidity", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("wind_speed", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("wind_deg", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("clouds", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("condition", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("description", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            ]
            
            # Create table if not exists
            table = bigquery.Table(self.full_table_id, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp",
            )
            table.clustering_fields = ["city", "country"]
            
            try:
                self.client.get_table(self.full_table_id)
                logger.info(f"Table {self.table_id} already exists")
            except NotFound:
                table = self.client.create_table(table)
                logger.info(f"Created table {self.table_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing BigQuery schema: {e}")
            return False
    
    def insert_weather_data(self, weather_data: List[WeatherData]) -> bool:
        """
        Insert weather data into BigQuery with idempotency
        
        Args:
            weather_data: List of WeatherData objects
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not weather_data:
                logger.warning("No weather data to insert")
                return True
            
            rows_to_insert = []
            for data in weather_data:
                # Generate unique ID based on city, country, and timestamp (hour precision)
                timestamp_hour = data.timestamp.replace(minute=0, second=0, microsecond=0)
                row_id = f"{data.city}_{data.country}_{timestamp_hour.isoformat()}"
                
                row = {
                    "id": row_id,
                    "city": data.city,
                    "country": data.country,
                    "temperature": data.temperature,
                    "feels_like": data.feels_like,
                    "temp_min": data.temp_min,
                    "temp_max": data.temp_max,
                    "pressure": data.pressure,
                    "humidity": data.humidity,
                    "wind_speed": data.wind_speed,
                    "wind_deg": data.wind_deg,
                    "clouds": data.clouds,
                    "condition": data.condition,
                    "description": data.description,
                    "timestamp": data.timestamp.isoformat(),
                    "created_at": datetime.utcnow().isoformat(),
                }
                rows_to_insert.append(row)
            
            # Use MERGE to ensure idempotency
            temp_table_id = f"{self.full_table_id}_temp_{int(datetime.utcnow().timestamp())}"
            
            # Create temporary table
            job_config = bigquery.LoadJobConfig(
                schema=self.client.get_table(self.full_table_id).schema,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )
            
            # Insert into temp table
            job = self.client.load_table_from_json(
                rows_to_insert,
                temp_table_id,
                job_config=job_config
            )
            job.result()
            
            # Merge into main table
            merge_query = f"""
            MERGE `{self.full_table_id}` T
            USING `{temp_table_id}` S
            ON T.id = S.id
            WHEN NOT MATCHED THEN
                INSERT ROW
            """
            
            query_job = self.client.query(merge_query)
            query_job.result()
            
            # Delete temp table
            self.client.delete_table(temp_table_id)
            
            logger.info(f"Successfully inserted {len(weather_data)} weather records")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting weather data: {e}")
            return False
    
    def get_latest_weather(self, city: str) -> Optional[Dict]:
        """
        Get the latest weather data for a city
        
        Args:
            city: City name
            
        Returns:
            Weather data dictionary or None
        """
        try:
            query = f"""
            SELECT *
            FROM `{self.full_table_id}`
            WHERE LOWER(city) = LOWER(@city)
            ORDER BY timestamp DESC
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("city", "STRING", city)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results:
                return dict(results[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest weather for {city}: {e}")
            return None
    
    def get_weather_history(self, city: str, days: int = 7) -> List[Dict]:
        """
        Get weather history for a city
        
        Args:
            city: City name
            days: Number of days of history
            
        Returns:
            List of weather data dictionaries
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = f"""
            SELECT *
            FROM `{self.full_table_id}`
            WHERE LOWER(city) = LOWER(@city)
              AND timestamp >= @start_date
            ORDER BY timestamp DESC
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("city", "STRING", city),
                    bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = [dict(row) for row in query_job.result()]
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting weather history for {city}: {e}")
            return []
    
    def get_average_temperature(self, city: str, days: int = 7) -> Optional[float]:
        """
        Get average temperature for a city over a period
        
        Args:
            city: City name
            days: Number of days to average
            
        Returns:
            Average temperature or None
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = f"""
            SELECT AVG(temperature) as avg_temp
            FROM `{self.full_table_id}`
            WHERE LOWER(city) = LOWER(@city)
              AND timestamp >= @start_date
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("city", "STRING", city),
                    bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results and results[0]["avg_temp"] is not None:
                return round(results[0]["avg_temp"], 2)
            return None
            
        except Exception as e:
            logger.error(f"Error getting average temperature for {city}: {e}")
            return None
    
    def get_all_cities(self) -> List[str]:
        """
        Get list of all cities in database
        
        Returns:
            List of city names
        """
        try:
            query = f"""
            SELECT DISTINCT city
            FROM `{self.full_table_id}`
            ORDER BY city
            """
            
            query_job = self.client.query(query)
            results = [row["city"] for row in query_job.result()]
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting all cities: {e}")
            return []