"""Database setup script."""

import logging
from sqlalchemy import create_engine, text
from config import config

logger = logging.getLogger(__name__)

def setup_database():
    """Initialize the database with required tables and extensions."""
    
    try:
        engine = create_engine(config["database"].connection_string)
        
        with engine.connect() as conn:
            # Enable TimescaleDB extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
            
            # Create telemetry table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    time TIMESTAMPTZ NOT NULL,
                    device_id VARCHAR(50) NOT NULL,
                    temperature DOUBLE PRECISION,
                    humidity DOUBLE PRECISION,
                    pressure DOUBLE PRECISION,
                    battery_level DOUBLE PRECISION,
                    location_lat DOUBLE PRECISION,
                    location_lon DOUBLE PRECISION,
                    schema_version INTEGER DEFAULT 1,
                    ingestion_time TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (time, device_id)
                );
            """))
            
            # Convert to hypertable
            try:
                conn.execute(text("SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);"))
            except Exception as e:
                if "already a hypertable" not in str(e):
                    raise
            
            # Create indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_telemetry_device_id ON telemetry (device_id, time DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_telemetry_ingestion_time ON telemetry (ingestion_time);"))
            
            # Create data quality log table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS data_quality_log (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    check_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    message TEXT,
                    record_count INTEGER,
                    error_count INTEGER,
                    details JSONB
                );
            """))
            
            conn.commit()
            
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_database()