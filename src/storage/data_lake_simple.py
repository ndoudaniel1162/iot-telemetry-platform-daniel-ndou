"""Simplified data lake storage handler without pandas/pyarrow dependencies."""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List
from models import ProcessedTelemetryEvent
from config_standalone import config

logger = logging.getLogger(__name__)

class SimpleDataLakeHandler:
    """Simplified data lake handler using JSON files."""
    
    def __init__(self):
        self.base_path = Path(config["storage"].data_lake_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def write_telemetry_batch(self, events: List[ProcessedTelemetryEvent]) -> bool:
        """Write telemetry events to JSON files partitioned by date."""
        try:
            if not events:
                return True
            
            # Group events by date
            events_by_date = {}
            for event in events:
                date_key = event.time.strftime("%Y-%m-%d")
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append(event)
            
            # Write each date group to a separate file
            for date_key, date_events in events_by_date.items():
                year, month, day = date_key.split('-')
                partition_path = self.base_path / f"year={year}" / f"month={month}" / f"day={day}"
                partition_path.mkdir(parents=True, exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"telemetry_{timestamp}.json"
                file_path = partition_path / filename
                
                # Convert events to JSON-serializable format
                json_events = []
                for event in date_events:
                    event_dict = event.dict()
                    # Convert datetime to string
                    event_dict['time'] = event_dict['time'].isoformat()
                    event_dict['ingestion_time'] = event_dict['ingestion_time'].isoformat()
                    json_events.append(event_dict)
                
                # Write to JSON file
                with open(file_path, 'w') as f:
                    json.dump(json_events, f, indent=2)
            
            logger.info(f"Wrote {len(events)} events to data lake (JSON format)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write to data lake: {e}")
            return False
    
    def read_telemetry_data(self, start_date: datetime = None, 
                           end_date: datetime = None,
                           device_id: str = None) -> List[dict]:
        """Read telemetry data from data lake."""
        try:
            all_events = []
            
            # Read all JSON files
            json_files = list(self.base_path.rglob("*.json"))
            
            for file_path in json_files:
                try:
                    with open(file_path, 'r') as f:
                        events = json.load(f)
                        if isinstance(events, list):
                            all_events.extend(events)
                        else:
                            all_events.append(events)
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
            
            # Apply filters
            filtered_events = []
            for event in all_events:
                # Filter by device_id
                if device_id and event.get('device_id') != device_id:
                    continue
                
                # Filter by date range
                if start_date or end_date:
                    event_time = datetime.fromisoformat(event['time'].replace('Z', '+00:00'))
                    if start_date and event_time < start_date:
                        continue
                    if end_date and event_time > end_date:
                        continue
                
                filtered_events.append(event)
            
            return filtered_events
            
        except Exception as e:
            logger.error(f"Failed to read from data lake: {e}")
            return []
    
    def get_partition_info(self) -> dict:
        """Get information about data lake partitions."""
        partitions = {}
        for year_dir in self.base_path.glob("year=*"):
            year = year_dir.name.split("=")[1]
            partitions[year] = {}
            
            for month_dir in year_dir.glob("month=*"):
                month = month_dir.name.split("=")[1]
                partitions[year][month] = {}
                
                for day_dir in month_dir.glob("day=*"):
                    day = day_dir.name.split("=")[1]
                    files = list(day_dir.glob("*.json"))
                    partitions[year][month][day] = len(files)
        
        return partitions