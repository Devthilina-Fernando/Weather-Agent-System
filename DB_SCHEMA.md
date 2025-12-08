# Database Schema Documentation

## Overview

The Weather Agent System uses **Google BigQuery** as its primary data warehouse for storing weather records. This document describes the schema design, relationships, indexing strategies, and incremental data handling.

## Database: Google BigQuery

- **Platform**: Google Cloud BigQuery
- **Project**: Configurable via `GCP_PROJECT_ID`
- **Dataset**: `weather_data` (default, configurable)
- **Primary Table**: `weather_records`

## Schema Diagram

```
┌─────────────────────────────────────────────────────┐
│              weather_records                         │
├─────────────────────────────────────────────────────┤
│ PK  id              STRING       (UUID)              │
│     city            STRING       (REQUIRED)          │
│     timestamp       TIMESTAMP    (REQUIRED)          │
│     temperature     FLOAT64      (REQUIRED, °C)      │
│     humidity        INTEGER      (REQUIRED, %)       │
│     wind_speed      FLOAT64      (REQUIRED, m/s)     │
│     condition       STRING       (REQUIRED)          │
├─────────────────────────────────────────────────────┤
│ CLUSTERING: [city, timestamp]                        │
│ PARTITION: None (clustering provides time-based opt) │
└─────────────────────────────────────────────────────┘
```

## Table: `weather_records`

### Purpose
Stores all weather data snapshots collected from the OpenWeatherMap API with hourly granularity.

### Fields

| Field Name    | Data Type  | Mode     | Description                                    |
|--------------|------------|----------|------------------------------------------------|
| `id`         | STRING     | REQUIRED | Unique identifier (UUID v4)                    |
| `city`       | STRING     | REQUIRED | City name (e.g., "London", "New York")         |
| `timestamp`  | TIMESTAMP  | REQUIRED | UTC timestamp when weather was recorded        |
| `temperature`| FLOAT64    | REQUIRED | Temperature in Celsius                         |
| `humidity`   | INTEGER    | REQUIRED | Humidity percentage (0-100)                    |
| `wind_speed` | FLOAT64    | REQUIRED | Wind speed in meters per second (m/s)          |
| `condition`  | STRING     | REQUIRED | Weather condition (e.g., "Clear", "Rain")      |

### Field Details

#### `id` (Primary Key)
- **Type**: STRING
- **Format**: UUID v4 (e.g., `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"`)
- **Generation**: Automatically generated via Python's `uuid.uuid4()`
- **Purpose**: Ensures globally unique record identification for idempotency

#### `city`
- **Type**: STRING
- **Validation**: Must match one of 100+ tracked cities in `app/config.py`
- **Case**: As provided by OpenWeatherMap API (typically title case)
- **Examples**: `"London"`, `"New York"`, `"São Paulo"`

#### `timestamp`
- **Type**: TIMESTAMP
- **Timezone**: UTC
- **Format**: ISO 8601 (e.g., `2025-12-07T14:30:00Z`)
- **Source**: Current UTC time when data is fetched from API
- **Granularity**: Hourly updates (can have sub-hour precision)

#### `temperature`
- **Type**: FLOAT64
- **Unit**: Celsius (°C)
- **Conversion**: Kelvin to Celsius handled by weather API client
- **Range**: Typically -50 to +50°C (varies by location)
- **Precision**: 2 decimal places

#### `humidity`
- **Type**: INTEGER
- **Unit**: Percentage (%)
- **Range**: 0-100
- **Source**: Relative humidity from OpenWeatherMap

#### `wind_speed`
- **Type**: FLOAT64
- **Unit**: Meters per second (m/s)
- **Range**: 0-50+ m/s (varies by weather conditions)
- **Precision**: 2 decimal places

#### `condition`
- **Type**: STRING
- **Examples**: `"Clear"`, `"Clouds"`, `"Rain"`, `"Snow"`, `"Drizzle"`, `"Thunderstorm"`
- **Source**: Main weather condition from OpenWeatherMap API
- **Case**: Title case

## Clustering Strategy

### Why Clustering?
BigQuery clustering improves query performance and reduces costs by physically organizing data on disk based on specified columns.

### Clustering Columns: `[city, timestamp]`

```sql
CREATE TABLE weather_data.weather_records
(
  id STRING NOT NULL,
  city STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  temperature FLOAT64 NOT NULL,
  humidity INT64 NOT NULL,
  wind_speed FLOAT64 NOT NULL,
  condition STRING NOT NULL
)
CLUSTER BY city, timestamp;
```

### Benefits

1. **City-Based Queries**:
   - Queries filtering by city (e.g., `WHERE city = 'London'`) scan only relevant data blocks
   - Most common query pattern in the system

2. **Time-Range Queries**:
   - Historical queries (e.g., `WHERE timestamp >= DATE_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)`)
   - Benefits from timestamp ordering within each city cluster

3. **Cost Reduction**:
   - Queries scan fewer bytes due to data pruning
   - Significant savings on large datasets

4. **Query Performance**:
   - Faster response times for common access patterns
   - No need for explicit partitioning with hourly granularity

### Example Query Optimization

```sql
-- Optimized query (uses clustering)
SELECT *
FROM weather_data.weather_records
WHERE city = 'London'
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
ORDER BY timestamp DESC;

-- BigQuery scans only London's data within the time range
-- Typical scan: ~1-10 MB for 7 days of hourly data
```

## Indexes

BigQuery does not support traditional indexes like relational databases. Instead:

- **Clustering**: Serves as the primary optimization mechanism
- **Column Storage**: Columnar format allows efficient column pruning
- **Automatic Optimization**: BigQuery automatically optimizes query execution plans

## Entity-Relationship Model

### Simplified ER Diagram

```
┌──────────────┐
│    Cities    │
│  (Logical)   │
└──────┬───────┘
       │ 1
       │
       │ N
       ▼
┌──────────────┐
│   Weather    │
│   Records    │
└──────────────┘
```

### Relationship Details

- **Cities**: Logical entity (not a physical table)
  - Defined in `app/config.py` as `CITIES` list (100+ cities)
  - Acts as a constraint on the `city` field

- **Weather Records**: Physical table
  - Each record represents one weather snapshot for one city at one point in time
  - One city can have many weather records (time series)
  - Relationship: `1 City : N Weather Records`

### No Foreign Keys
BigQuery is a data warehouse, not a transactional database. It doesn't enforce foreign key constraints. Instead:
- Application-level validation ensures city names are valid
- Data integrity maintained through Pydantic models and API validation

## Incremental Data Handling

### Strategy: Append-Only with Unique IDs

The system uses an **append-only** strategy with unique identifiers to handle incremental updates.

### How It Works

1. **Hourly Data Collection**:
   ```python
   # Scheduler runs every hour
   weather_records = fetch_weather_for_all_cities()
   ```

2. **UUID Generation**:
   ```python
   # Each record gets a unique ID
   record_id = str(uuid.uuid4())
   ```

3. **BigQuery Insert**:
   ```python
   # Append new rows to table
   job = client.load_table_from_json(
       records,
       table_ref,
       job_config=LoadJobConfig()
   )
   ```

4. **No Duplicates**:
   - Each hourly job creates new UUIDs
   - Even if the same city/time is collected twice, different UUIDs ensure separate rows
   - Clustering + timestamp allows de-duplication in queries if needed

### Idempotency Considerations

**Current Implementation**: Not strictly idempotent
- Re-running the same hourly job will create new records with new UUIDs
- Acceptable for append-only analytics use case


## Data Retention

### Current Policy
- **No automatic deletion**: All historical data is retained
- **Storage**: BigQuery active storage costs apply
- **Access**: Full history accessible for analytics

**Location**: [app/repositories/bigquery_repo.py](app/repositories/bigquery_repo.py)

```python
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
table.clustering_fields = ["city", "timestamp"]
```