"""Data quality validation for telemetry events."""

import logging
from datetime import datetime, timedelta
from typing import List
from ..models import ProcessedTelemetryEvent, DataQualityResult
from ..config import config

logger = logging.getLogger(__name__)

class DataQualityValidator:
    """Validates telemetry events for data quality."""
    
    def __init__(self):
        self.quality_config = config["quality"]
    
    def validate_event(self, event: ProcessedTelemetryEvent) -> DataQualityResult:
        """Validate a single telemetry event."""
        errors = []
        warnings = []
        
        # Required fields check
        if not event.device_id:
            errors.append("Missing device_id")
        
        if not event.time:
            errors.append("Missing timestamp")
        
        # Timestamp validation
        if event.time:
            now = datetime.utcnow()
            if event.time > now + timedelta(minutes=5):
                errors.append("Timestamp is too far in the future")
            elif event.time < now - timedelta(days=30):
                warnings.append("Timestamp is older than 30 days")
        
        # Value range validation
        if event.temperature is not None:
            if not (self.quality_config.temperature_min <= event.temperature <= self.quality_config.temperature_max):
                errors.append(f"Temperature {event.temperature} out of valid range")
        
        if event.humidity is not None:
            if not (self.quality_config.humidity_min <= event.humidity <= self.quality_config.humidity_max):
                errors.append(f"Humidity {event.humidity} out of valid range")
        
        if event.pressure is not None:
            if not (self.quality_config.pressure_min <= event.pressure <= self.quality_config.pressure_max):
                errors.append(f"Pressure {event.pressure} out of valid range")
        
        if event.battery_level is not None:
            if not (self.quality_config.battery_min <= event.battery_level <= self.quality_config.battery_max):
                errors.append(f"Battery level {event.battery_level} out of valid range")
        
        # Location validation
        if event.location_lat is not None:
            if not (-90 <= event.location_lat <= 90):
                errors.append(f"Invalid latitude {event.location_lat}")
        
        if event.location_lon is not None:
            if not (-180 <= event.location_lon <= 180):
                errors.append(f"Invalid longitude {event.location_lon}")
        
        # Determine overall status
        if errors:
            status = "FAIL"
            message = "; ".join(errors)
        elif warnings:
            status = "WARNING"
            message = "; ".join(warnings)
        else:
            status = "PASS"
            message = "All validations passed"
        
        return DataQualityResult(
            check_type="event_validation",
            status=status,
            message=message,
            record_count=1,
            error_count=len(errors),
            details={
                "errors": errors,
                "warnings": warnings,
                "device_id": event.device_id
            }
        )
    
    def validate_batch(self, events: List[ProcessedTelemetryEvent]) -> DataQualityResult:
        """Validate a batch of telemetry events."""
        total_errors = 0
        device_errors = {}
        
        for event in events:
            result = self.validate_event(event)
            if result.status == "FAIL":
                total_errors += 1
                device_id = event.device_id
                if device_id not in device_errors:
                    device_errors[device_id] = 0
                device_errors[device_id] += 1
        
        error_rate = total_errors / len(events) if events else 0
        
        if error_rate > 0.1:  # More than 10% errors
            status = "FAIL"
            message = f"High error rate: {error_rate:.2%}"
        elif error_rate > 0.05:  # More than 5% errors
            status = "WARNING"
            message = f"Elevated error rate: {error_rate:.2%}"
        else:
            status = "PASS"
            message = f"Batch validation passed with {error_rate:.2%} error rate"
        
        return DataQualityResult(
            check_type="batch_validation",
            status=status,
            message=message,
            record_count=len(events),
            error_count=total_errors,
            details={
                "error_rate": error_rate,
                "device_errors": device_errors
            }
        )