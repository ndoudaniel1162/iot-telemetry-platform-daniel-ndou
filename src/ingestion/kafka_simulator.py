"""Kafka simulation for IoT telemetry data ingestion."""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Generator, List, Dict, Any
from pathlib import Path

class KafkaSimulator:
    """Simulates Kafka consumer for IoT telemetry events."""
    
    def __init__(self, data_file: str = None):
        self.data_file = data_file
        self.sample_devices = [
            "device_001", "device_002", "device_003", "device_004", "device_005"
        ]
    
    def generate_sample_event_v1(self, device_id: str = None) -> Dict[str, Any]:
        """Generate a sample V1 telemetry event."""
        if not device_id:
            device_id = random.choice(self.sample_devices)
            
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "device_id": device_id,
            "temperature": round(random.uniform(15.0, 35.0), 2),
            "humidity": round(random.uniform(30.0, 80.0), 2),
            "pressure": round(random.uniform(980.0, 1020.0), 2),
            "battery_level": round(random.uniform(10.0, 100.0), 2)
        }
    
    def generate_sample_event_v2(self, device_id: str = None) -> Dict[str, Any]:
        """Generate a sample V2 telemetry event with location."""
        event = self.generate_sample_event_v1(device_id)
        event["location"] = {
            "lat": round(random.uniform(40.0, 41.0), 6),
            "lon": round(random.uniform(-74.5, -73.5), 6)
        }
        return event
    
    def generate_sample_data(self, count: int = 1000, output_file: str = "data/sample_events.jsonl"):
        """Generate sample data file for testing."""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            for i in range(count):
                # Mix of V1 and V2 events (70% V1, 30% V2)
                if random.random() < 0.7:
                    event = self.generate_sample_event_v1()
                else:
                    event = self.generate_sample_event_v2()
                
                f.write(json.dumps(event) + "\n")
        
        print(f"Generated {count} sample events in {output_file}")
    
    def consume_events(self, batch_size: int = 100) -> Generator[List[str], None, None]:
        """Simulate consuming events from Kafka topic."""
        if self.data_file and Path(self.data_file).exists():
            # Read from file
            with open(self.data_file, 'r') as f:
                batch = []
                for line in f:
                    line = line.strip()
                    if line:
                        batch.append(line)
                        if len(batch) >= batch_size:
                            yield batch
                            batch = []
                
                # Yield remaining events
                if batch:
                    yield batch
        else:
            # Generate events in real-time
            while True:
                batch = []
                for _ in range(batch_size):
                    if random.random() < 0.7:
                        event = self.generate_sample_event_v1()
                    else:
                        event = self.generate_sample_event_v2()
                    batch.append(json.dumps(event))
                
                yield batch
                time.sleep(1)  # Simulate delay between batches

class DeadLetterQueue:
    """Simple dead letter queue for failed events."""
    
    def __init__(self, file_path: str = "data/dead_letter_queue.jsonl"):
        self.file_path = file_path
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    def add_failed_event(self, event: str, error: str):
        """Add a failed event to the dead letter queue."""
        failed_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "error": str(error)
        }
        
        with open(self.file_path, 'a') as f:
            f.write(json.dumps(failed_record) + "\n")
    
    def get_failed_events(self) -> List[Dict[str, Any]]:
        """Retrieve all failed events."""
        if not Path(self.file_path).exists():
            return []
        
        failed_events = []
        with open(self.file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    failed_events.append(json.loads(line))
        
        return failed_events