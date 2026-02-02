# IoT Telemetry Data Engineering Platform

## Overview
This project implements a streaming data ingestion platform for high-volume IoT telemetry data with schema evolution, data quality monitoring, and dual storage architecture (SQLite database + JSON data lake).

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git

### Setup & Run
```bash
# Clone the repository
git clone https://github.com/ndoudaniel1162/iot-telemetry-platform-daniel-ndou.git
cd iot-telemetry-platform-daniel-ndou

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements_simple.txt

# Run the platform
python src/main_simple.py
```

## Expected Output
```
INFO - Starting IoT Telemetry Platform (Simple Mode)
INFO - Generating sample telemetry data...
Generated 500 sample events in data/sample_events.jsonl
INFO - Starting stream processing...
INFO - Inserted 50 telemetry records
INFO - Wrote 50 events to data lake (JSON format)
INFO - Processed batch: 50 successful, 0 failed
...
INFO - Processing completed: 3 batches, 150 successful events, 0 failed events

==================================================
DATA QUALITY REPORT (Simple Mode)
==================================================
Total Records: 150
Unique Devices: 5

Device Summary:
  device_001: 30 records
  device_002: 30 records
  device_003: 30 records
  device_004: 30 records
  device_005: 30 records
==================================================

INFO - IoT Telemetry Platform completed successfully!
```

## Architecture

### High-Level Design
```
IoT Devices → Kafka Simulation → Stream Processor → [SQLite + JSON Data Lake]
                                                  ↓
                                          Data Quality Monitor
                                                  ↓
                                          BI/ML Analytics Layer
```

### Key Components
1. **Data Ingestion**: Kafka simulation with IoT events
2. **Stream Processing**: Schema evolution and data transformation
3. **Dual Storage**: SQLite for operational queries + JSON files for analytics
4. **Data Quality**: Validation, monitoring, and alerting
5. **Migration Tools**: Historical data transformation and loading

## How to Run
```bash
# Simple setup - no Docker required
python src/main_simple.py
```

This demonstrates all technical assessment requirements with minimal dependencies.

## Project Structure
```
├── src/
│   ├── main_simple.py          # Main entry point
│   ├── models.py               # Data models and schema evolution
│   ├── ingestion/              # Kafka simulation and data generation
│   │   └── kafka_simulator.py
│   ├── processing/             # Stream processing engine
│   │   └── stream_processor.py
│   ├── storage/                # Database and data lake handlers
│   │   ├── database_simple.py  # SQLite handler
│   │   └── data_lake_simple.py # JSON data lake
│   ├── quality/                # Data validation and monitoring
│   │   ├── validator.py        # Data quality validation
│   │   └── monitor.py          # Quality monitoring
│   └── migration/              # Data migration tools
│       └── migrate.py
├── tests/                      # Unit tests
│   ├── test_models.py
│   └── test_validator.py
├── requirements_simple.txt     # Dependencies
├── README.md                   # This file
└── architecture.md             # Architecture design
```

## Key Features Implemented

✅ **Schema Evolution**: Graceful handling of V1 and V2 telemetry events  
✅ **Dual Storage**: SQLite for operational queries + JSON files for analytics  
✅ **Data Quality**: Comprehensive validation with configurable thresholds  
✅ **Error Handling**: Dead letter queue and retry mechanisms  
✅ **Monitoring**: Quality reports and alerting system  
✅ **Migration Tools**: Historical data processing and transformation  
✅ **Testing**: Unit tests for critical components  
✅ **Documentation**: Architecture design and operational guides  

## Data Flow

1. **Sample Data Generation**: Creates realistic IoT telemetry events
2. **Stream Processing**: Validates and transforms events in batches
3. **Dual Storage**: Stores in both SQLite database and JSON data lake
4. **Quality Monitoring**: Tracks data quality metrics and generates reports
5. **Error Handling**: Failed events go to dead letter queue for review

## Verification

After running, check the created files:
```bash
# Database file
dir iot_telemetry.db

# Data lake structure (partitioned by date)
dir data\lake

# Sample data
dir data\sample_events.jsonl
```

## Key Design Decisions

### Storage Architecture
- **SQLite**: Lightweight, serverless database for operational queries
- **JSON Files**: Simple, readable format for analytics data lake
- **Date Partitioning**: Efficient organization for time-series analytics

### Schema Evolution
- Backward compatible schema changes (V1 → V2)
- Automatic version detection based on field presence
- Graceful handling of missing/new fields

### Error Handling
- Dead letter queue for failed records
- Comprehensive validation with configurable rules
- Retry mechanisms and detailed logging

### Performance Considerations
- Batch processing for efficiency (50 events per batch)
- Partitioned storage for scalable analytics
- Minimal dependencies for fast startup

## Trade-offs Made

1. **Simplicity vs Production Scale**: SQLite + JSON vs TimescaleDB + Parquet
2. **Dependencies**: Minimal packages vs full analytics stack
3. **Storage**: File-based vs distributed storage systems
4. **Monitoring**: Basic logging vs comprehensive observability

## Future Improvements

1. **Production Infrastructure**: TimescaleDB, Kafka cluster, monitoring
2. **Advanced Analytics**: Real-time aggregations, anomaly detection
3. **Scalability**: Kubernetes deployment, auto-scaling
4. **Security**: Encryption, authentication, authorization
5. **Testing**: Integration tests, performance testing

## Testing
```bash
# Run unit tests
python -m pytest tests/ -v
```

## Technical Assessment Requirements Met

✅ **Part 1: Architecture Design** - Complete architecture documentation
✅ **Part 2: Implementation** - Full working pipeline with schema evolution
✅ **Part 3: Data Quality** - Comprehensive validation and monitoring
✅ **Part 4: Migration** - Historical data transformation tools
✅ **Part 5: Documentation** - Complete setup and design documentation

## Author
Daniel Ndou - Senior Data Engineer Technical Assessment

## License
Open Source - Educational/Assessment Purpose