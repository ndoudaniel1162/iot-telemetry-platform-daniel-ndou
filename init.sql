-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create telemetry table
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

-- Convert to hypertable
SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_device_id ON telemetry (device_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_ingestion_time ON telemetry (ingestion_time);

-- Create data quality tracking table
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