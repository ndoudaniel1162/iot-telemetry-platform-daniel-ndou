"""Stream processing engine for IoT telemetry data."""

import logging
from typing import List, Tuple
from ..models import ProcessedTelemetryEvent, parse_telemetry_event
from ..storage.database import TimescaleDBHandler
from ..storage.data_lake import DataLakeHandler
from ..quality.validator import DataQualityValidator
from ..ingestion.kafka_simulator import DeadLetterQueue

logger = logging.getLogger(__name__)

class StreamProcessor:
    """Main stream processing engine."""
    
    def __init__(self):
        self.db_handler = TimescaleDBHandler()
        self.lake_handler = DataLakeHandler()
        self.validator = DataQualityValidator()
        self.dlq = DeadLetterQueue()
    
    def process_batch(self, raw_events: List[str]) -> Tuple[int, int]:
        """Process a batch of raw telemetry events."""
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
                    self.dlq.add_failed_event(raw_event, validation_result.message)
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process event: {e}")
                self.dlq.add_failed_event(raw_event, str(e))
                failed_count += 1
        
        # Store processed events
        if processed_events:
            # Store in TimescaleDB
            db_success = self.db_handler.insert_telemetry_batch(processed_events)
            
            # Store in Data Lake
            lake_success = self.lake_handler.write_telemetry_batch(processed_events)
            
            if not db_success or not lake_success:
                logger.error("Failed to store some events")
        
        success_count = len(processed_events)
        logger.info(f"Processed batch: {success_count} successful, {failed_count} failed")
        
        return success_count, failed_count
    
    def process_stream(self, event_generator, max_batches: int = None):
        """Process continuous stream of events."""
        batch_count = 0
        total_success = 0
        total_failed = 0
        
        try:
            for batch in event_generator:
                success, failed = self.process_batch(batch)
                total_success += success
                total_failed += failed
                batch_count += 1
                
                if max_batches and batch_count >= max_batches:
                    break
                    
        except KeyboardInterrupt:
            logger.info("Stream processing interrupted by user")
        except Exception as e:
            logger.error(f"Stream processing error: {e}")
        
        logger.info(f"Stream processing completed: {batch_count} batches, "
                   f"{total_success} successful events, {total_failed} failed events")