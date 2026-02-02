"""Migration tools for historical data transformation."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from storage.database import TimescaleDBHandler
from storage.data_lake import DataLakeHandler
from models import ProcessedTelemetryEvent

logger = logging.getLogger(__name__)

class DataMigrator:
    """Handles migration and transformation of historical data."""
    
    def __init__(self):
        self.db_handler = TimescaleDBHandler()
        self.lake_handler = DataLakeHandler()
    
    def migrate_lake_to_timescale(self, start_date: datetime = None, 
                                 end_date: datetime = None,
                                 batch_size: int = 1000) -> Dict[str, Any]:
        """Migrate data from data lake to TimescaleDB."""
        
        migration_stats = {
            "start_time": datetime.utcnow(),
            "records_processed": 0,
            "records_migrated": 0,
            "errors": []
        }
        
        try:
            # Read data from lake
            logger.info("Reading data from data lake...")
            df = self.lake_handler.read_telemetry_data(start_date, end_date)
            
            if df.empty:
                logger.info("No data found in data lake for specified period")
                return migration_stats
            
            logger.info(f"Found {len(df)} records to migrate")
            migration_stats["records_processed"] = len(df)
            
            # Process in batches
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                try:
                    # Convert to ProcessedTelemetryEvent objects
                    events = []
                    for _, row in batch_df.iterrows():
                        event = ProcessedTelemetryEvent(
                            time=pd.to_datetime(row['time']),
                            device_id=row['device_id'],
                            temperature=row.get('temperature'),
                            humidity=row.get('humidity'),
                            pressure=row.get('pressure'),
                            battery_level=row.get('battery_level'),
                            location_lat=row.get('location_lat'),
                            location_lon=row.get('location_lon'),
                            schema_version=row.get('schema_version', 1),
                            ingestion_time=pd.to_datetime(row.get('ingestion_time', datetime.utcnow()))
                        )
                        events.append(event)
                    
                    # Insert batch into TimescaleDB
                    success = self.db_handler.insert_telemetry_batch(events)
                    
                    if success:
                        migration_stats["records_migrated"] += len(events)
                        logger.info(f"Migrated batch {i//batch_size + 1}: {len(events)} records")
                    else:
                        error_msg = f"Failed to migrate batch {i//batch_size + 1}"
                        migration_stats["errors"].append(error_msg)
                        logger.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Error processing batch {i//batch_size + 1}: {e}"
                    migration_stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Migration failed: {e}"
            migration_stats["errors"].append(error_msg)
            logger.error(error_msg)
        
        migration_stats["end_time"] = datetime.utcnow()
        migration_stats["duration_seconds"] = (
            migration_stats["end_time"] - migration_stats["start_time"]
        ).total_seconds()
        
        return migration_stats
    
    def transform_for_analytics(self, device_id: str = None, 
                               hours: int = 24) -> pd.DataFrame:
        """Transform operational data for analytics workloads."""
        
        try:
            # Get data from TimescaleDB
            df = self.db_handler.get_telemetry_data(device_id, hours)
            
            if df.empty:
                return pd.DataFrame()
            
            # Create analytics-friendly transformations
            analytics_df = df.copy()
            
            # Add time-based features
            analytics_df['hour'] = pd.to_datetime(analytics_df['time']).dt.hour
            analytics_df['day_of_week'] = pd.to_datetime(analytics_df['time']).dt.dayofweek
            analytics_df['is_weekend'] = analytics_df['day_of_week'].isin([5, 6])
            
            # Add derived metrics
            if 'temperature' in analytics_df.columns and 'humidity' in analytics_df.columns:
                # Heat index approximation
                analytics_df['heat_index'] = analytics_df.apply(
                    lambda row: self._calculate_heat_index(row['temperature'], row['humidity'])
                    if pd.notna(row['temperature']) and pd.notna(row['humidity']) else None,
                    axis=1
                )
            
            # Add rolling averages
            for col in ['temperature', 'humidity', 'pressure']:
                if col in analytics_df.columns:
                    analytics_df[f'{col}_rolling_1h'] = (
                        analytics_df.groupby('device_id')[col]
                        .rolling(window='1H', on='time', min_periods=1)
                        .mean()
                        .reset_index(level=0, drop=True)
                    )
            
            # Add device health indicators
            if 'battery_level' in analytics_df.columns:
                analytics_df['battery_status'] = pd.cut(
                    analytics_df['battery_level'],
                    bins=[0, 20, 50, 80, 100],
                    labels=['Critical', 'Low', 'Medium', 'High']
                )
            
            return analytics_df
            
        except Exception as e:
            logger.error(f"Failed to transform data for analytics: {e}")
            return pd.DataFrame()
    
    def _calculate_heat_index(self, temp_c: float, humidity: float) -> float:
        """Calculate heat index from temperature (Celsius) and humidity."""
        try:
            # Convert to Fahrenheit for heat index calculation
            temp_f = (temp_c * 9/5) + 32
            
            # Simplified heat index formula
            if temp_f < 80:
                return temp_c  # Return original temperature if too cool
            
            hi = (
                -42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
                - 0.22475541 * temp_f * humidity - 6.83783e-3 * temp_f**2
                - 5.481717e-2 * humidity**2 + 1.22874e-3 * temp_f**2 * humidity
                + 8.5282e-4 * temp_f * humidity**2 - 1.99e-6 * temp_f**2 * humidity**2
            )
            
            # Convert back to Celsius
            return (hi - 32) * 5/9
            
        except:
            return temp_c
    
    def export_analytics_data(self, output_path: str = "data/analytics_export.parquet",
                             device_id: str = None, hours: int = 24):
        """Export transformed analytics data."""
        
        analytics_df = self.transform_for_analytics(device_id, hours)
        
        if not analytics_df.empty:
            analytics_df.to_parquet(output_path, compression='snappy')
            logger.info(f"Exported {len(analytics_df)} analytics records to {output_path}")
        else:
            logger.warning("No data available for analytics export")

def main():
    """Main migration script."""
    migrator = DataMigrator()
    
    # Example: Migrate last 7 days of data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    print("Starting data migration...")
    stats = migrator.migrate_lake_to_timescale(start_date, end_date)
    
    print(f"\nMigration completed:")
    print(f"  Duration: {stats['duration_seconds']:.1f} seconds")
    print(f"  Records processed: {stats['records_processed']}")
    print(f"  Records migrated: {stats['records_migrated']}")
    print(f"  Errors: {len(stats['errors'])}")
    
    if stats['errors']:
        print("\nErrors encountered:")
        for error in stats['errors']:
            print(f"  - {error}")
    
    # Export analytics data
    print("\nExporting analytics data...")
    migrator.export_analytics_data()
    print("Analytics export completed")

if __name__ == "__main__":
    main()