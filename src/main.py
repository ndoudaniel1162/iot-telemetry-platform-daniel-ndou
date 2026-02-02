"""Main entry point for the IoT telemetry platform."""

import logging
import sys
from pathlib import Path
from ingestion.kafka_simulator import KafkaSimulator
from processing.stream_processor import StreamProcessor
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

def setup_directories():
    """Create necessary directories."""
    directories = ['data', 'logs', 'data/lake']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    """Main execution function."""
    logger.info("Starting IoT Telemetry Platform")
    
    # Setup
    setup_directories()
    
    # Generate sample data if it doesn't exist
    sample_file = "data/sample_events.jsonl"
    if not Path(sample_file).exists():
        logger.info("Generating sample telemetry data...")
        simulator = KafkaSimulator()
        simulator.generate_sample_data(count=5000, output_file=sample_file)
    
    # Initialize components
    simulator = KafkaSimulator(data_file=sample_file)
    processor = StreamProcessor()
    monitor = DataQualityMonitor()
    
    try:
        # Process the data stream
        logger.info("Starting stream processing...")
        event_generator = simulator.consume_events(batch_size=100)
        processor.process_stream(event_generator, max_batches=10)
        
        # Generate quality report
        logger.info("Generating data quality report...")
        monitor.print_quality_summary()
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise
    
    logger.info("IoT Telemetry Platform completed")

if __name__ == "__main__":
    main()