# IoT Telemetry Data Engineering Platform

## Architecture Design Document

**Author:** Daniel Ndou\
**Role:** Senior Data Engineer -- Technical Assessment

------------------------------------------------------------------------

# 1. Overview

This document describes the architecture of a lightweight IoT telemetry
data ingestion and processing platform designed to demonstrate:

-   Streaming-style data ingestion
-   Schema evolution handling
-   Dual storage architecture (SQLite + JSON Data Lake)
-   Data quality validation and monitoring
-   Error handling and batch processing
-   Migration capability for historical data

The system simulates high-volume IoT telemetry ingestion while remaining
dependency-light and easy to execute locally.

------------------------------------------------------------------------

# 2. High-Level Architecture

    IoT Devices → Kafka Simulation (JSONL) → Stream Processor → [SQLite + JSON Data Lake]
                                                            ↓
                                                     Data Quality Monitor

------------------------------------------------------------------------

# 3. Architecture Components

## 3.1 Data Ingestion Layer

Instead of deploying a real Kafka cluster, the system simulates
streaming ingestion using:

-   JSONL (JSON Lines) event files
-   Programmatically generated telemetry data
-   Batch-based processing to mimic consumer behavior

### Telemetry Event Structure

Each event contains:

-   device_id\
-   timestamp\
-   temperature\
-   humidity\
-   Optional fields (Schema V2):
    -   battery_level\
    -   firmware_version

------------------------------------------------------------------------

## 3.2 Stream Processing Layer

Responsible for:

-   Batch ingestion (default: 50 events per batch)
-   Schema evolution detection
-   Data transformation
-   Validation enforcement
-   Error isolation

### Schema Evolution Strategy

Supports:

-   **V1 Schema**: Base telemetry fields\
-   **V2 Schema**: Additional optional fields

Design principles:

-   Backward compatibility maintained\
-   Optional fields handled gracefully\
-   Automatic version detection\
-   Default values applied where necessary

------------------------------------------------------------------------

# 4. Dual Storage Architecture

## 4.1 SQLite (Operational Store)

Purpose:

-   Fast structured queries\
-   Device-level aggregations\
-   Operational monitoring

Characteristics:

-   File-based database (`iot_telemetry.db`)\
-   Indexed on `device_id` and `timestamp`\
-   Lightweight and portable

Example query:

``` sql
SELECT device_id, COUNT(*) 
FROM telemetry 
GROUP BY device_id;
```

------------------------------------------------------------------------

## 4.2 JSON Data Lake (Analytical Store)

Purpose:

-   Historical storage\
-   Analytical workloads\
-   ML feature engineering

Structure example:

    data/
     └── lake/
         └── YYYY-MM-DD/
             └── telemetry_batch_X.json

Rationale:

-   Minimal dependencies\
-   Human-readable\
-   Demonstrates partitioned data lake principles

------------------------------------------------------------------------

# 5. Data Quality Layer

Validation rules:

-   Required field checks\
-   Value range validation
    -   Temperature (-50°C to 100°C)\
    -   Humidity (0--100%)\
-   Timestamp validation

Outputs include:

-   Total records processed\
-   Unique devices\
-   Per-device counts\
-   Failed record count

------------------------------------------------------------------------

# 6. Error Handling Strategy

Error categories:

1.  Schema validation errors\
2.  Missing required fields\
3.  Out-of-range telemetry values

Handling approach:

-   Failed events isolated\
-   Logged with contextual detail\
-   Batch continues processing

------------------------------------------------------------------------

# 7. Trade-offs and Design Decisions

  Decision                 Rationale
  ------------------------ ---------------------------------
  SQLite over PostgreSQL   Zero external dependencies
  JSON over Parquet        Simplicity and readability
  Batch processing         Reduced overhead
  Kafka simulation         Avoid infrastructure complexity

------------------------------------------------------------------------

# 8. Production Upgrade Path

  Current            Production Upgrade
  ------------------ --------------------------------------
  Kafka Simulation   Real Kafka Cluster
  SQLite             PostgreSQL / TimescaleDB
  JSON               Parquet on S3
  Local processing   Distributed processing (Spark/Flink)

------------------------------------------------------------------------

# 9. Conclusion

This platform demonstrates:

-   Stream-style telemetry ingestion\
-   Schema evolution handling\
-   Dual storage design\
-   Data quality validation\
-   Error handling and resilience

The implementation balances architectural best practices with simplicity
and portability while remaining extensible for production-scale
evolution.
