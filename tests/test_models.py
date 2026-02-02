"""Tests for data models."""

import pytest
from datetime import datetime
import json
from src.models import TelemetryEventV1, TelemetryEventV2, ProcessedTelemetryEvent, parse_telemetry_event

def test_telemetry_event_v1():
    """Test TelemetryEventV1 model."""
    event = TelemetryEventV1(
        timestamp=datetime.utcnow(),
        device_id="device_001",
        temperature=25.5,
        humidity=60.0,
        pressure=1013.25,
        battery_level=85.0
    )
    
    assert event.device_id == "device_001"
    assert event.temperature == 25.5

def test_telemetry_event_v2():
    """Test TelemetryEventV2 model with location."""
    event = TelemetryEventV2(
        timestamp=datetime.utcnow(),
        device_id="device_002",
        temperature=22.0,
        humidity=55.0,
        pressure=1015.0,
        battery_level=90.0,
        location={"lat": 40.7128, "lon": -74.0060}
    )
    
    assert event.location["lat"] == 40.7128
    assert event.location["lon"] == -74.0060

def test_parse_telemetry_event_v1():
    """Test parsing V1 telemetry event."""
    raw_data = {
        "timestamp": "2024-01-01T12:00:00Z",
        "device_id": "device_001",
        "temperature": 25.5,
        "humidity": 60.0,
        "pressure": 1013.25,
        "battery_level": 85.0
    }
    
    event = parse_telemetry_event(json.dumps(raw_data))
    
    assert event.device_id == "device_001"
    assert event.temperature == 25.5
    assert event.schema_version == 1

def test_parse_telemetry_event_v2():
    """Test parsing V2 telemetry event with location."""
    raw_data = {
        "timestamp": "2024-01-01T12:00:00Z",
        "device_id": "device_002",
        "temperature": 22.0,
        "humidity": 55.0,
        "pressure": 1015.0,
        "battery_level": 90.0,
        "location": {"lat": 40.7128, "lon": -74.0060}
    }
    
    event = parse_telemetry_event(json.dumps(raw_data))
    
    assert event.device_id == "device_002"
    assert event.location_lat == 40.7128
    assert event.location_lon == -74.0060
    assert event.schema_version == 2

def test_parse_invalid_event():
    """Test parsing invalid telemetry event."""
    with pytest.raises(ValueError):
        parse_telemetry_event("invalid json")