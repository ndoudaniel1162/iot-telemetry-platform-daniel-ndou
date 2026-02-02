"""SQLite database storage handler for standalone mode."""

import logging
from typing import List, Optional
from sqlalchemy import create_engine, text, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime
from models import ProcessedTelemetryEvent, DataQualityResult
from config_standalone import config

logger = logging.getLogger(__name__)

Base = declarative_base()

class TelemetryRecord(Base):
    __tablename__ = 'telemetry'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, nullable=False)
    device_id = Column(String(50), nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    battery_level = Column(Float)
    location_lat = Column(Float)
    location_lon = Column(Float)
    schema_version = Column(Integer, default=1)
    ingestion_time = Column(DateTime, default=datetime.utcnow)

class DataQualityLog(Base):
    __tablename__ = 'data_quality_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    check_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    message = Column(String(500))
    record_count = Column(Integer)
    error_count = Column(Integer)

class SQLiteHandler:
    """Handler for SQLite operations."""
    
    def __init__(self):
        self.engine = create_engine(config["database"].connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def insert_telemetry_batch(self, events: List[ProcessedTelemetryEvent]) -> bool:
        """Insert a batch of telemetry events."""
        try:
            records = []
            for event in events:
                record = TelemetryRecord(
                    time=event.time,
                    device_id=event.device_id,
                    temperature=event.temperature,
                    humidity=event.humidity,
                    pressure=event.pressure,
                    battery_level=event.battery_level,
                    location_lat=event.location_lat,
                    location_lon=event.location_lon,
                    schema_version=event.schema_version,
                    ingestion_time=event.ingestion_time
                )
                records.append(record)
            
            with self.Session() as session:
                session.add_all(records)
                session.commit()
            
            logger.info(f"Inserted {len(events)} telemetry records")
            return True
        except Exception as e:
            logger.error(f"Failed to insert telemetry batch: {e}")
            return False
    
    def log_data_quality(self, result: DataQualityResult):
        """Log data quality check result."""
        try:
            with self.Session() as session:
                log_entry = DataQualityLog(
                    check_type=result.check_type,
                    status=result.status,
                    message=result.message,
                    record_count=result.record_count,
                    error_count=result.error_count
                )
                session.add(log_entry)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to log data quality result: {e}")
    
    def get_telemetry_data(self, device_id: Optional[str] = None, 
                          hours: int = 24) -> pd.DataFrame:
        """Retrieve telemetry data for analysis."""
        try:
            query = "SELECT * FROM telemetry WHERE time >= datetime('now', '-{} hours')".format(hours)
            
            if device_id:
                query += f" AND device_id = '{device_id}'"
            
            query += " ORDER BY time DESC"
            
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logger.error(f"Failed to retrieve telemetry data: {e}")
            return pd.DataFrame()