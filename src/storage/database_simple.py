"""Simple SQLite database handler without pandas dependency."""

import logging
import sqlite3
from typing import List, Optional
from datetime import datetime
from models import ProcessedTelemetryEvent, DataQualityResult

logger = logging.getLogger(__name__)

class SimpleSQLiteHandler:
    """Simple SQLite handler without pandas dependency."""
    
    def __init__(self, db_path: str = "iot_telemetry.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create telemetry table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    pressure REAL,
                    battery_level REAL,
                    location_lat REAL,
                    location_lon REAL,
                    schema_version INTEGER DEFAULT 1,
                    ingestion_time TEXT
                )
            """)
            
            # Create data quality log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    check_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    record_count INTEGER,
                    error_count INTEGER
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def insert_telemetry_batch(self, events: List[ProcessedTelemetryEvent]) -> bool:
        """Insert a batch of telemetry events."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for event in events:
                cursor.execute("""
                    INSERT INTO telemetry (
                        time, device_id, temperature, humidity, pressure, 
                        battery_level, location_lat, location_lon, 
                        schema_version, ingestion_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.time.isoformat(),
                    event.device_id,
                    event.temperature,
                    event.humidity,
                    event.pressure,
                    event.battery_level,
                    event.location_lat,
                    event.location_lon,
                    event.schema_version,
                    event.ingestion_time.isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Inserted {len(events)} telemetry records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert telemetry batch: {e}")
            return False
    
    def log_data_quality(self, result: DataQualityResult):
        """Log data quality check result."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO data_quality_log (
                    check_type, status, message, record_count, error_count
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                result.check_type,
                result.status,
                result.message,
                result.record_count,
                result.error_count
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log data quality result: {e}")
    
    def get_telemetry_count(self) -> int:
        """Get total count of telemetry records."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM telemetry")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Failed to get telemetry count: {e}")
            return 0
    
    def get_unique_devices(self) -> int:
        """Get count of unique devices."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(DISTINCT device_id) FROM telemetry")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Failed to get unique devices count: {e}")
            return 0
    
    def get_device_summary(self) -> dict:
        """Get summary by device."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT device_id, COUNT(*) FROM telemetry GROUP BY device_id")
            results = cursor.fetchall()
            
            conn.close()
            return {device_id: count for device_id, count in results}
            
        except Exception as e:
            logger.error(f"Failed to get device summary: {e}")
            return {}