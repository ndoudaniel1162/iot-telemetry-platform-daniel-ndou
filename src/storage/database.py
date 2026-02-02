"""Database storage handler for TimescaleDB."""

import logging
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
from models import ProcessedTelemetryEvent, DataQualityResult
from config import config

logger = logging.getLogger(__name__)

class TimescaleDBHandler:
    """Handler for TimescaleDB operations."""
    
    def __init__(self):
        self.engine = create_engine(config["database"].connection_string)
        self.Session = sessionmaker(bind=self.engine)
    
    def insert_telemetry_batch(self, events: List[ProcessedTelemetryEvent]) -> bool:
        """Insert a batch of telemetry events."""
        try:
            df = pd.DataFrame([event.dict() for event in events])
            df.to_sql('telemetry', self.engine, if_exists='append', index=False, method='multi')
            logger.info(f"Inserted {len(events)} telemetry records")
            return True
        except Exception as e:
            logger.error(f"Failed to insert telemetry batch: {e}")
            return False
    
    def log_data_quality(self, result: DataQualityResult):
        """Log data quality check result."""
        try:
            with self.Session() as session:
                query = text("""
                    INSERT INTO data_quality_log (check_type, status, message, record_count, error_count, details)
                    VALUES (:check_type, :status, :message, :record_count, :error_count, :details)
                """)
                session.execute(query, {
                    'check_type': result.check_type,
                    'status': result.status,
                    'message': result.message,
                    'record_count': result.record_count,
                    'error_count': result.error_count,
                    'details': result.details
                })
                session.commit()
        except Exception as e:
            logger.error(f"Failed to log data quality result: {e}")
    
    def get_telemetry_data(self, device_id: Optional[str] = None, 
                          hours: int = 24) -> pd.DataFrame:
        """Retrieve telemetry data for analysis."""
        query = """
            SELECT * FROM telemetry 
            WHERE time >= NOW() - INTERVAL '%s hours'
        """ % hours
        
        if device_id:
            query += f" AND device_id = '{device_id}'"
        
        query += " ORDER BY time DESC"
        
        return pd.read_sql(query, self.engine)