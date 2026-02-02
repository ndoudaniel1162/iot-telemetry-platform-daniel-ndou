# IoT Telemetry Data Engineering Platform

## Overview
This project implements a streaming data ingestion platform for high-volume IoT telemetry data with schema evolution, data quality monitoring, and dual storage architecture (time-series + data lake).

## Architecture

### High-Level Design
```
IoT Devices → Kafka → Stream Processor → [TimescaleDB + Data Lake (Parquet)]
                                      ↓
                              Data Quality Monitor
                                      ↓
                              BI/ML Analytics Layer
```

### Key Components
1. **Kafka Ingestion**: Simulated Kafka consumer for IoT events
2. **Stream Processor**: Handles schema evolution and data transformation
3. **Dual Storage**: TimescaleDB for operational queries + Parquet files for analytics
4. **Data Quality**: Validation, monitoring, and alerting
5. **Migration Tools**: Historical data transformation and loading

## Quick Start

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- PostgreSQL (TimescaleDB extension)

### Setup
```bash
# Clone and setup
git clone <repository>
cd iot-telemetry-platform

# Install dependencies
pip install -r requirements.txt

# Start infrastructure
docker-compose up -d

# Run the pipeline
python src/main.py
```

## Project Structure
```
├── src/
│   ├── ingestion/          # Kafka simulation and ingestion
│   ├── processing/         # Stream processing and transformation
│   ├── storage/           # Database and file storage handlers
│   ├── quality/           # Data quality monitoring
│   └── migration/         # Historical data migration tools
├── config/                # Configuration files
├── data/                 # Sample data and outputs
├── tests/                # Unit tests
└── docker-compose.yml    # Infrastructure setup
```

## Running the Solution

1. **Start Infrastructure**: `docker-compose up -d`
2. **Initialize Database**: `python src/setup_db.py`
3. **Run Pipeline**: `python src/main.py`
4. **Check Data Quality**: `python src/quality/monitor.py`
5. **Run Migration**: `python src/migration/migrate.py`

## Key Design Decisions

### Topic Design & Partitioning
- Partition by device_id for ordered processing per device
- Separate topics for different device types if needed
- Retention policy based on operational vs analytical needs

### Schema Evolution
- Avro schema registry simulation with backward compatibility
- Graceful handling of missing/new fields
- Version tracking in metadata

### Error Handling
- Dead letter queue for failed records
- Retry mechanism with exponential backoff
- Comprehensive logging and alerting

### Performance Considerations
- Batch processing for efficiency
- Parallel processing where possible
- Optimized storage formats (Parquet with compression)

## Trade-offs Made

1. **Simplicity vs Production Scale**: Used file-based simulation instead of full Kafka setup
2. **Storage**: PostgreSQL with TimescaleDB extension vs dedicated time-series DB
3. **Schema Registry**: Simulated vs full Confluent Schema Registry
4. **Monitoring**: Basic logging vs comprehensive observability stack

## Future Improvements

1. **Production Infrastructure**: Full Kafka cluster, Schema Registry, monitoring stack
2. **Advanced Analytics**: Real-time aggregations, anomaly detection
3. **Scalability**: Kubernetes deployment, auto-scaling
4. **Security**: Encryption, authentication, authorization
5. **Testing**: Integration tests, performance testing
6. **Observability**: Metrics, tracing, alerting

## Testing
```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/
```