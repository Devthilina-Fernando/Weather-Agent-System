"""BigQuery repository for weather data storage and retrieval"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from app.models import WeatherData
from app.config import settings

logger = logging.getLogger(__name__)


class BigQueryRepository:
    """Repository for managing weather data in BigQuery"""
    
    def __init__(self):
        self.client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        self.dataset_id = settings.BIGQUERY_DATASET
        self.table_id = settings.BIGQUERY_TABLE
        self.full_table_id = f"{settings.GCP_PROJECT_ID}.{self.dataset_id}.{self.table_id}"
    
    async def initialize_schema(self):
        """Create dataset and table if they don't exist"""
        # Create dataset
        dataset_ref = self.client.dataset(self.dataset_id)
        try:
            self.client.get_dataset(dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            dataset = self.client.create_dataset(dataset)
            logger.info(f"Created dataset {self.dataset_id}")
        
        # Create table
        table_ref = dataset_ref.table(self.table_id)
        try:
            self.client.get_table(table_ref)
            logger.info(f"Table {self.table_id} already exists")
        except NotFound:
            schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("city", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("temperature", "FLOAT64", mode="REQUIRED"),
                bigquery.SchemaField("humidity", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("wind_speed", "FLOAT64", mode="REQUIRED"),
                bigquery.SchemaField("condition", "STRING", mode="REQUIRED"),
            ]
            
            table = bigquery.Table(table_ref, schema=schema)
            
            # Create clustering for better query performance
            table.clustering_fields = ["city", "timestamp"]
            
            table = self.client.create_table(table)
            logger.info(f"Created table {self.table_id}")
    
    async def insert_weather_data(self, weather_records: List[WeatherData]) -> int:
        """
        Insert weather data into BigQuery (idempotent)
        
        Args:
            weather_records: List of WeatherData objects
            
        Returns:
            Number of records inserted
        """
        if not weather_records:
            logger.warning("No weather records to insert")
            return 0
        
        # Convert to dict format for BigQuery
        rows_to_insert = []
        for record in weather_records:
            rows_to_insert.append({
                "id": record.id,
                "city": record.city,
                "timestamp": record.timestamp.isoformat(),
                "temperature": record.temperature,
                "humidity": record.humidity,
                "wind_speed": record.wind_speed,
                "condition": record.condition
            })
        
        try:
            # Use MERGE pattern for idempotency
            # First, insert into a temp table, then merge
            temp_table_id = f"{self.full_table_id}_temp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create temporary table
            job_config = bigquery.LoadJobConfig(
                schema=[
                    bigquery.SchemaField("id", "STRING"),
                    bigquery.SchemaField("city", "STRING"),
                    bigquery.SchemaField("timestamp", "TIMESTAMP"),
                    bigquery.SchemaField("temperature", "FLOAT64"),
                    bigquery.SchemaField("humidity", "INTEGER"),
                    bigquery.SchemaField("wind_speed", "FLOAT64"),
                    bigquery.SchemaField("condition", "STRING"),
                ],
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )
            
            # Load data to temp table
            job = self.client.load_table_from_json(
                rows_to_insert,
                temp_table_id,
                job_config=job_config
            )
            job.result()  # Wait for the job to complete
            
            # Merge with main table (idempotent operation)
            merge_query = f"""
            MERGE `{self.full_table_id}` AS target
            USING `{temp_table_id}` AS source
            ON target.city = source.city 
               AND target.timestamp = source.timestamp
            WHEN NOT MATCHED THEN
              INSERT (id, city, timestamp, temperature, humidity, wind_speed, condition)
              VALUES (source.id, source.city, source.timestamp, source.temperature, 
                      source.humidity, source.wind_speed, source.condition)
            """
            
            query_job = self.client.query(merge_query)
            query_job.result()
            
            # Clean up temp table
            self.client.delete_table(temp_table_id, not_found_ok=True)
            
            logger.info(f"Successfully inserted/merged {len(rows_to_insert)} weather records")
            return len(rows_to_insert)
            
        except Exception as e:
            logger.error(f"Error inserting weather data: {str(e)}")
            raise
    
    async def get_latest_weather(self, city: str) -> Optional[WeatherData]:
        """
        Get latest weather data for a city
        
        Args:
            city: City name
            
        Returns:
            WeatherData object or None
        """
        query = f"""
        SELECT id, city, timestamp, temperature, humidity, wind_speed, condition
        FROM `{self.full_table_id}`
        WHERE city = @city
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("city", "STRING", city)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                return WeatherData(
                    id=row.id,
                    city=row.city,
                    timestamp=row.timestamp,
                    temperature=row.temperature,
                    humidity=row.humidity,
                    wind_speed=row.wind_speed,
                    condition=row.condition
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching latest weather for {city}: {str(e)}")
            raise
    
    async def get_weather_history(self, city: str, days: int) -> List[WeatherData]:
        """
        Get weather history for a city
        
        Args:
            city: City name
            days: Number of days to retrieve
            
        Returns:
            List of WeatherData objects
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = f"""
        SELECT id, city, timestamp, temperature, humidity, wind_speed, condition
        FROM `{self.full_table_id}`
        WHERE city = @city
          AND timestamp >= @start_date
        ORDER BY timestamp DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("city", "STRING", city),
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            weather_records = []
            for row in results:
                weather_records.append(WeatherData(
                    id=row.id,
                    city=row.city,
                    timestamp=row.timestamp,
                    temperature=row.temperature,
                    humidity=row.humidity,
                    wind_speed=row.wind_speed,
                    condition=row.condition
                ))
            
            return weather_records
            
        except Exception as e:
            logger.error(f"Error fetching weather history for {city}: {str(e)}")
            raise