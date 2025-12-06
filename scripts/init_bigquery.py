#!/usr/bin/env python3
"""
Script to initialize BigQuery schema
Run this before starting the application
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.database import BigQueryService
from app.config import get_settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """
    Initialize BigQuery dataset and table
    """
    try:
        logger.info("Initializing BigQuery schema")
        
        settings = get_settings()
        logger.info(f"Project ID: {settings.gcp_project_id}")
        logger.info(f"Dataset: {settings.bigquery_dataset}")
        logger.info(f"Table: {settings.bigquery_table}")
        
        db_service = BigQueryService()
        success = db_service.initialize_schema()
        
        if success:
            logger.info("BigQuery schema initialized successfully")
            return 0
        else:
            logger.error("Failed to initialize BigQuery schema")
            return 1
            
    except Exception as e:
        logger.error(f"Error initializing BigQuery schema: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())