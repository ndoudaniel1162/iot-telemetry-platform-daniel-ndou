"""Tests for data quality validator."""

import pytest
from datetime import datetime, timedelta
from src.models import ProcessedTelemetryEvent
from src.quality.validator import DataQualityValidator

def test_valid_event():
    """Test validation of a valid event."""
    validator = DataQualityValidator()
    
    event = ProcessedTelemetryEvent(
        time=datetime.utcnow(),
        device_id="device_001",
        temperature=25.0,
        humidity=60.0,
        pressure=1013.25,
        battery_level=85.0
    )
    
    result = validator.validate_event(event)
    assert result.status == "PASS"

def test_invalid_temperature():
    """Test validation with invalid temperature."""
    validator = DataQualityValidator()
    
    event = ProcessedTelemetryEvent(
        time=datetime.utcnow(),
        device_id="device_001",
        temperature=150.0,  # Too high
        humidity=60.0,
        pressure=1013.25,
        battery_level=85.0
    )
    
    result = validator.validate_event(event)
    assert result.status == "FAIL"
    assert "Temperature" in result.message

def test_missing_device_id():
    """Test validation with missing device ID."""
    validator = DataQualityValidator()
    
    event = ProcessedTelemetryEvent(
        time=datetime.utcnow(),
        device_id="",  # Empty device ID
        temperature=25.0,
        humidity=60.0,
        pressure=1013.25,
        battery_level=85.0
    )
    
    result = validator.validate_event(event)
    assert result.status == "FAIL"
    assert "device_id" in result.message

def test_future_timestamp():
    """Test validation with future timestamp."""
    validator = DataQualityValidator()
    
    future_time = datetime.utcnow() + timedelta(hours=1)
    event = ProcessedTelemetryEvent(
        time=future_time,
        device_id="device_001",
        temperature=25.0,
        humidity=60.0,
        pressure=1013.25,
        battery_level=85.0
    )
    
    result = validator.validate_event(event)
    assert result.status == "FAIL"
    assert "future" in result.message