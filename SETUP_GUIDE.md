# Personal Laptop Setup Guide - IoT Telemetry Platform

## Quick Reference Commands

### Initial Setup (One-time)
```bash
# 1. Clone repository
git clone https://github.com/ndoudaniel1162/iot-telemetry-platform-daniel-ndou.git
cd iot-telemetry-platform-daniel-ndou

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start infrastructure
docker-compose up -d

# 5. Initialize database (wait 30 seconds after step 4)
python src/setup_db.py
```

### Running the Platform

#### Option 1: Standalone Mode (No Docker Required)
```bash
# Activate virtual environment (if not already active)
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Run standalone version (uses SQLite)
python src/main_standalone.py
```

#### Option 2: Full Docker Mode
```bash
# Activate virtual environment (if not already active)
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start Docker services
docker-compose up -d

# Initialize database (wait 30 seconds after starting Docker)
python src/setup_db.py

# Run main pipeline
python src/main.py
```

### Additional Operations
```bash
# Data quality monitoring
python src/quality/monitor.py

# Data migration
python src/migration/migrate.py

# Run tests
python -m pytest tests/ -v
```

### Stopping Everything
```bash
# Stop Docker services
docker-compose down

# Deactivate virtual environment
deactivate
```

## Expected Output

### Standalone Mode Output
When you run `python src/main_standalone.py`, you should see:

```
INFO - Starting IoT Telemetry Platform (Standalone Mode)
INFO - Generating sample telemetry data...
INFO - Generated 1000 sample events in data/sample_events.jsonl
INFO - Starting stream processing...
INFO - Inserted 100 telemetry records
INFO - Wrote 100 events to data lake
INFO - Processed batch: 100 successful, 0 failed
...
INFO - Processing completed: 5 batches, 500 successful events, 0 failed events
INFO - Generating data quality report...

============================================================
DATA QUALITY REPORT (Standalone Mode)
============================================================
Total Records: 500
Unique Devices: 5
Time Range: 2024-01-01 11:00:00 to 2024-01-01 12:00:00

DATA COMPLETENESS:
  temperature: 100.0%
  humidity: 100.0%
  pressure: 100.0%
  battery_level: 100.0%

DEVICE SUMMARY:
  device_001: 100 records
  device_002: 100 records
  device_003: 100 records
  device_004: 100 records
  device_005: 100 records
============================================================
```

### Full Docker Mode Output

When you run `python src/main.py`, you should see:

```
INFO - Starting IoT Telemetry Platform
INFO - Generating sample telemetry data...
INFO - Generated 5000 sample events in data/sample_events.jsonl
INFO - Starting stream processing...
INFO - Inserted 100 telemetry records
INFO - Wrote 100 events to data lake
INFO - Processed batch: 100 successful, 0 failed
...
INFO - Generating data quality report...

============================================================
DATA QUALITY REPORT
============================================================
Generated: 2024-01-01T12:00:00.000000
Period: Last 24 hours

BASIC METRICS:
  Total Records: 5,000
  Unique Devices: 5
  Time Range: 2024-01-01T11:00:00 to 2024-01-01T12:00:00
  Data Freshness: 0.1 minutes ago

DATA COMPLETENESS:
  temperature: 100.0% (5000 records)
  humidity: 100.0% (5000 records)
  pressure: 100.0% (5000 records)
  battery_level: 100.0% (5000 records)

ALERTS:
  No alerts
============================================================
```

## File Structure After Running

```
iot-telemetry-platform-daniel-ndou/
├── data/
│   ├── lake/                    # Parquet files (partitioned by date)
│   ├── sample_events.jsonl      # Generated sample data
│   └── dead_letter_queue.jsonl  # Failed events (if any)
├── logs/
│   └── telemetry_platform.log   # Application logs
├── src/                         # Source code
├── tests/                       # Unit tests
└── ... (other files)
```

## Verification Steps

1. **Check database data:**
   ```bash
   docker exec -it $(docker-compose ps -q postgres) psql -U postgres -d iot_telemetry -c "SELECT COUNT(*) FROM telemetry;"
   ```

2. **Check data lake files:**
   ```bash
   # Windows:
   dir data\lake /s
   # macOS/Linux:
   find data/lake -name "*.parquet"
   ```

3. **Check logs:**
   ```bash
   # Windows:
   type logs\telemetry_platform.log
   # macOS/Linux:
   cat logs/telemetry_platform.log
   ```

## Common Issues & Solutions

### Issue: "Docker command not found"
**Solution:** Install Docker Desktop and ensure it's running

### Issue: "Python command not found"
**Solution:** Install Python 3.8+ and add to PATH

### Issue: "Permission denied" on Docker
**Solution:** 
- Windows: Run as Administrator
- macOS/Linux: Add user to docker group or use sudo

### Issue: Database connection error
**Solution:** 
```bash
# Wait longer for PostgreSQL to start
docker-compose logs postgres
# Look for "database system is ready to accept connections"
```

### Issue: Port already in use
**Solution:**
```bash
# Stop conflicting services
docker-compose down
# Or change ports in docker-compose.yml
```

## Performance Notes

- **Processing Speed**: ~1000 events/second on typical laptop
- **Memory Usage**: ~200MB for Python process
- **Disk Usage**: ~50MB for 5000 events (including Parquet files)
- **Startup Time**: ~30 seconds for full infrastructure

## Next Steps After Setup

1. **Explore the data:**
   - Connect to database and run queries
   - Examine Parquet files in data lake
   - Review quality reports

2. **Modify configuration:**
   - Edit `src/config.py` for different settings
   - Adjust batch sizes, validation rules, etc.

3. **Add more data:**
   - Increase event count in `src/main.py`
   - Add new device types or sensors
   - Test schema evolution scenarios