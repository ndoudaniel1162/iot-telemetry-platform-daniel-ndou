"""Standalone main entry point that works without Docker."""

import logging
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from ingestion.kafka_simulator import KafkaSimulator
from storage.database_standalone import SQLiteHandler
from storage.data_lake import DataLakeHandler
from quality.validator import DataQualityValidator
from quality.monitor import DataQualityMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/telemetry_platform.log')
    ]
)

logger = logging.getLogger(__name__)

class StandaloneStreamProcessor:
    """Simplified stream processor for standalone mode."""
    
    def __init__(self):
        self.db_handler = SQLiteHandler()
        self.lake_handler = DataLakeHandler()
        self.validator = DataQualityValidator()
    
    def process_batch(self, raw_events):
        """Process a batch of raw telemetry events."""
        from models import parse_telemetry_event
        from ingestion.kafka_simulator import DeadLetterQueue
        
        dlq = DeadLetterQueue()
        processed_events = []
        failed_count = 0
        
        for raw_event in raw_events:
            try:
                # Parse the event
                event = parse_telemetry_event(raw_event)
                
                # Validate the event
                validation_result = self.validator.validate_event(event)
                
                if validation_result.status == "PASS":
                    processed_events.append(event)
                else:
                    logger.warning(f"Event validation failed: {validation_result.message}")
                    dlq.add_failed_event(raw_event, validation_result.message)
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process event: {e}")
                dlq.add_failed_event(raw_event, str(e))
                failed_count += 1
        
        # Store processed events
        if processed_events:
            # Store in SQLite
            db_success = self.db_handler.insert_telemetry_batch(processed_events)
            
            # Store in Data Lake
            lake_success = self.lake_handler.write_telemetry_batch(processed_events)
            
            if not db_success or not lake_success:
                logger.error("Failed to store some events")
        
        success_count = len(processed_events)
        logger.info(f"Processed batch: {success_count} successful, {failed_count} failed")
        
        return success_count, failed_count

class StandaloneDataQualityMonitor:
    """Simplified data quality monitor for standalone mode."""
    
    def __init__(self):
        self.db_handler = SQLiteHandler()
    
    def print_quality_summary(self):
        """Print a formatted data quality summary."""
        try:
            df = self.db_handler.get_telemetry_data(hours=24)
            
            print("\n" + "="*60)
            print("DATA QUALITY REPORT (Standalone Mode)")
            print("="*60)
            
            if df.empty:
                print("No data available")
                return
            
            print(f"Total Records: {len(df):,}")
            print(f"Unique Devices: {df['device_id'].nunique()}")
            print(f"Time Range: {df['time'].min()} to {df['time'].max()}")
            
            # Data completeness
            print(f"\nDATA COMPLETENESS:")
            for col in ['temperature', 'humidity', 'pressure', 'battery_level']:
                if col in df.columns:
                    completeness = df[col].notna().mean() * 100
                    print(f"  {col}: {completeness:.1f}%")
            
            # Device summary
            print(f"\nDEVICE SUMMARY:")
            device_counts = df['device_id'].value_counts()
            for device, count in device_counts.items():
                print(f"  {device}: {count} records")
            
            print("="*60)
            
        except Exception as e:
            print(f"Error generating quality report: {e}")

def setup_directories():
    """Create necessary directories."""
    directories = ['data', 'logs', 'data/lake']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    """Main execution function for standalone mode."""
    logger.info("Starting IoT Telemetry Platform (Standalone Mode)")
    
    # Setup
    setup_directories()
    
    # Generate sample data if it doesn't exist
    sample_file = "data/sample_events.jsonl"
    if not Path(sample_file).exists():
        logger.info("Generating sample telemetry data...")
        simulator = KafkaSimulator()
        simulator.generate_sample_data(count=1000, output_file=sample_file)
    
    # Initialize components
    simulator = KafkaSimulator(data_file=sample_file)
    processor = StandaloneStreamProcessor()
    monitor = StandaloneDataQualityMonitor()
    
    try:
        # Process the data stream
        logger.info("Starting stream processing...")
        event_generator = simulator.consume_events(batch_size=100)
        
        batch_count = 0
        total_success = 0
        total_failed = 0
        
        for batch in event_generator:
            success, failed = processor.process_batch(batch)
            total_success += success
            total_failed += failed
            batch_count += 1
            
            if batch_count >= 5:  # Process 5 batches for demo
                break
        
        logger.info(f"Processing completed: {batch_count} batches, "
                   f"{total_success} successful events, {total_failed} failed events")
        
        # Generate quality report
        logger.info("Generating data quality report...")
        monitor.print_quality_summary()
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise
    
    logger.info("IoT Telemetry Platform completed successfully!")

if __name__ == "__main__":
    main()