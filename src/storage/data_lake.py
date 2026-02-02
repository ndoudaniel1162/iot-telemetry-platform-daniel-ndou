"""Data lake storage handler using Parquet files."""

import logging
from pathlib import Path
from datetime import datetime
from typing import List
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from models import ProcessedTelemetryEvent
from config import config

logger = logging.getLogger(__name__)

class DataLakeHandler:
    """Handler for data lake operations using Parquet files."""
    
    def __init__(self):
        self.base_path = Path(config["storage"].data_lake_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def write_telemetry_batch(self, events: List[ProcessedTelemetryEvent]) -> bool:
        """Write telemetry events to partitioned Parquet files."""
        try:
            if not events:
                return True
            
            # Convert to DataFrame
            df = pd.DataFrame([event.dict() for event in events])
            
            # Add partition columns
            df['year'] = pd.to_datetime(df['time']).dt.year
            df['month'] = pd.to_datetime(df['time']).dt.month
            df['day'] = pd.to_datetime(df['time']).dt.day
            
            # Group by partition and write
            for (year, month, day), group_df in df.groupby(['year', 'month', 'day']):
                partition_path = self.base_path / f"year={year}" / f"month={month:02d}" / f"day={day:02d}"
                partition_path.mkdir(parents=True, exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"telemetry_{timestamp}.parquet"
                file_path = partition_path / filename
                
                # Remove partition columns before writing
                group_df = group_df.drop(['year', 'month', 'day'], axis=1)
                
                # Write to Parquet with compression
                table = pa.Table.from_pandas(group_df)
                pq.write_table(table, file_path, compression=config["storage"].compression)
            
            logger.info(f"Wrote {len(events)} events to data lake")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write to data lake: {e}")
            return False
    
    def read_telemetry_data(self, start_date: datetime = None, 
                           end_date: datetime = None,
                           device_id: str = None) -> pd.DataFrame:
        """Read telemetry data from data lake with optional filtering."""
        try:
            # Build file pattern for reading
            if start_date and end_date:
                # Read specific date range (simplified - would need more complex logic for full range)
                year = start_date.year
                month = start_date.month
                pattern = self.base_path / f"year={year}" / f"month={month:02d}" / "*" / "*.parquet"
            else:
                pattern = self.base_path / "**" / "*.parquet"
            
            # Read all matching Parquet files
            parquet_files = list(self.base_path.rglob("*.parquet"))
            
            if not parquet_files:
                return pd.DataFrame()
            
            # Read and combine all files
            dfs = []
            for file_path in parquet_files:
                df = pd.read_parquet(file_path)
                dfs.append(df)
            
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Apply filters
            if device_id:
                combined_df = combined_df[combined_df['device_id'] == device_id]
            
            if start_date:
                combined_df = combined_df[pd.to_datetime(combined_df['time']) >= start_date]
            
            if end_date:
                combined_df = combined_df[pd.to_datetime(combined_df['time']) <= end_date]
            
            return combined_df.sort_values('time')
            
        except Exception as e:
            logger.error(f"Failed to read from data lake: {e}")
            return pd.DataFrame()
    
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
                    files = list(day_dir.glob("*.parquet"))
                    partitions[year][month][day] = len(files)
        
        return partitions