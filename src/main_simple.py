"""Ultra-simple main entry point with minimal dependencies."""

import logging
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from ingestion.kafka_simulator import KafkaSimulator
from storage.database_simple import SimpleSQLiteHandler
from storage.data_lake_simple import SimpleDataLakeHandler
from quality.validator import DataQualityValidator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

class SimpleStreamProcessor:
    """Ultra-simple stream processor."""
    
    def __init__(self):
        self.db_handler = SimpleSQLiteHandler()
        self.lake_handler = SimpleDataLakeHandler()
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
            
            # Store in Data Lake (JSON format)
            lake_success = self.lake_handler.write_telemetry_batch(processed_events)
            
            if not db_success or not lake_success:
                logger.error("Failed to store some events")
        
        success_count = len(processed_events)
        logger.info(f"Processed batch: {success_count} successful, {failed_count} failed")
        
        return success_count, failed_count

def setup_directories():
    """Create necessary directories."""
    directories = ['data', 'data/lake']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    """Main execution function."""
    logger.info("Starting IoT Telemetry Platform (Simple Mode)")
    
    # Setup
    setup_directories()
    
    # Generate sample data if it doesn't exist
    sample_file = "data/sample_events.jsonl"
    if not Path(sample_file).exists():
        logger.info("Generating sample telemetry data...")
        simulator = KafkaSimulator()
        simulator.generate_sample_data(count=500, output_file=sample_file)
    
    # Initialize components
    simulator = KafkaSimulator(data_file=sample_file)
    processor = SimpleStreamProcessor()
    
    try:
        # Process the data stream
        logger.info("Starting stream processing...")
        event_generator = simulator.consume_events(batch_size=50)
        
        batch_count = 0
        total_success = 0
        total_failed = 0
        
        for batch in event_generator:
            success, failed = processor.process_batch(batch)
            total_success += success
            total_failed += failed
            batch_count += 1
            
            if batch_count >= 3:  # Process 3 batches for demo
                break
        
        logger.info(f"Processing completed: {batch_count} batches, "
                   f"{total_success} successful events, {total_failed} failed events")
        
        # Simple quality report
        try:
            db_handler = SimpleSQLiteHandler()
            total_records = db_handler.get_telemetry_count()
            unique_devices = db_handler.get_unique_devices()
            device_summary = db_handler.get_device_summary()
            
            print("\n" + "="*50)
            print("DATA QUALITY REPORT (Simple Mode)")
            print("="*50)
            print(f"Total Records: {total_records}")
            print(f"Unique Devices: {unique_devices}")
            
            if device_summary:
                print("\nDevice Summary:")
                for device, count in device_summary.items():
                    print(f"  {device}: {count} records")
            
            print("="*50)
            
        except Exception as e:
            logger.error(f"Failed to generate quality report: {e}")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise
    
    logger.info("IoT Telemetry Platform completed successfully!")

if __name__ == "__main__":
    main()