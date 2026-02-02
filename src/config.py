"""Configuration settings for the IoT telemetry platform."""

import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "iot_telemetry")
    username: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "password")
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class KafkaConfig:
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic: str = os.getenv("KAFKA_TOPIC", "iot-telemetry")
    group_id: str = os.getenv("KAFKA_GROUP_ID", "telemetry-processor")

@dataclass
class StorageConfig:
    data_lake_path: str = os.getenv("DATA_LAKE_PATH", "./data/lake")
    batch_size: int = int(os.getenv("BATCH_SIZE", "1000"))
    compression: str = os.getenv("COMPRESSION", "snappy")

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

# Global configuration instance
config = {
    "database": DatabaseConfig(),
    "kafka": KafkaConfig(),
    "storage": StorageConfig(),
    "quality": QualityConfig()
}