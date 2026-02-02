"""Standalone configuration for running without Docker."""

import os
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """SQLite configuration for standalone mode."""
    connection_string: str = "sqlite:///iot_telemetry.db"

@dataclass
class StorageConfig:
    data_lake_path: str = "./data/lake"
    batch_size: int = 1000
    compression: str = "snappy"

@dataclass
class QualityConfig:
    temperature_min: float = -50.0
    temperature_max: float = 100.0
    humidity_min: float = 0.0
    humidity_max: float = 100.0
    pressure_min: float = 800.0
    pressure_max: float = 1200.0
    battery_min: float = 0.0
    battery_max: float = 100.0

# Standalone configuration
config = {
    "database": DatabaseConfig(),
    "storage": StorageConfig(),
    "quality": QualityConfig()
}