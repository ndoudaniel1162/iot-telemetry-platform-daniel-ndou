"""Data models for IoT telemetry events."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import json

class TelemetryEventV1(BaseModel):
    """Version 1 of telemetry event schema."""
    timestamp: datetime
    device_id: str
    temperature: float
    humidity: float
    pressure: float
    battery_level: float
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TelemetryEventV2(BaseModel):
    """Version 2 of telemetry event schema with location data."""
    timestamp: datetime
    device_id: str
    temperature: float
    humidity: float
    pressure: float
    battery_level: float
    location: Optional[Dict[str, float]] = None  # {"lat": 40.7128, "lon": -74.0060}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProcessedTelemetryEvent(BaseModel):
    """Processed telemetry event for storage."""
    time: datetime
    device_id: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    battery_level: Optional[float] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    schema_version: int = 1
    ingestion_time: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('time', 'ingestion_time', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            # Handle different datetime string formats
            if v.endswith('Z'):
                # Replace Z with +00:00 for proper parsing
                v = v.replace('Z', '+00:00')
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # If fromisoformat fails, try without timezone info
                return datetime.fromisoformat(v.split('+')[0].split('Z')[0])
        return v

class DataQualityResult(BaseModel):
    """Data quality check result."""
    check_type: str
    status: str  # "PASS", "FAIL", "WARNING"
    message: str
    record_count: int = 0
    error_count: int = 0
    details: Dict[str, Any] = {}

def parse_telemetry_event(raw_data: str) -> ProcessedTelemetryEvent:
    """Parse raw JSON telemetry data into ProcessedTelemetryEvent."""
    try:
        data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        
        # Determine schema version based on presence of location field
        has_location = 'location' in data
        schema_version = 2 if has_location else 1
        
        # Create processed event
        processed = ProcessedTelemetryEvent(
            time=data['timestamp'],
            device_id=data['device_id'],
            temperature=data.get('temperature'),
            humidity=data.get('humidity'),
            pressure=data.get('pressure'),
            battery_level=data.get('battery_level'),
            schema_version=schema_version
        )
        
        # Handle location data if present
        if has_location and data['location']:
            processed.location_lat = data['location'].get('lat')
            processed.location_lon = data['location'].get('lon')
            
        return processed
        
    except Exception as e:
        raise ValueError(f"Failed to parse telemetry event: {e}")