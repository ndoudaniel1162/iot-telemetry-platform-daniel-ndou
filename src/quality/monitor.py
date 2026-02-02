"""Data quality monitoring and reporting."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd
from storage.database import TimescaleDBHandler
from storage.data_lake import DataLakeHandler

logger = logging.getLogger(__name__)

class DataQualityMonitor:
    """Monitor and report on data quality metrics."""
    
    def __init__(self):
        self.db_handler = TimescaleDBHandler()
        self.lake_handler = DataLakeHandler()
    
    def generate_quality_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive data quality report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "metrics": {}
        }
        
        try:
            # Get telemetry data
            df = self.db_handler.get_telemetry_data(hours=hours)
            
            if df.empty:
                report["metrics"]["message"] = "No data available for the specified period"
                return report
            
            # Basic metrics
            report["metrics"]["total_records"] = len(df)
            report["metrics"]["unique_devices"] = df['device_id'].nunique()
            report["metrics"]["time_range"] = {
                "start": df['time'].min().isoformat() if not df.empty else None,
                "end": df['time'].max().isoformat() if not df.empty else None
            }
            
            # Data completeness
            completeness = {}
            for col in ['temperature', 'humidity', 'pressure', 'battery_level']:
                if col in df.columns:
                    completeness[col] = {
                        "non_null_count": df[col].notna().sum(),
                        "completeness_rate": df[col].notna().mean()
                    }
            report["metrics"]["completeness"] = completeness
            
            # Value ranges and outliers
            ranges = {}
            for col in ['temperature', 'humidity', 'pressure', 'battery_level']:
                if col in df.columns and df[col].notna().any():
                    ranges[col] = {
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "mean": float(df[col].mean()),
                        "std": float(df[col].std())
                    }
            report["metrics"]["value_ranges"] = ranges
            
            # Device-level metrics
            device_metrics = df.groupby('device_id').agg({
                'time': ['count', 'min', 'max'],
                'temperature': 'mean',
                'humidity': 'mean',
                'battery_level': 'mean'
            }).round(2)
            
            report["metrics"]["device_summary"] = device_metrics.to_dict()
            
            # Schema version distribution
            if 'schema_version' in df.columns:
                version_dist = df['schema_version'].value_counts().to_dict()
                report["metrics"]["schema_versions"] = version_dist
            
            # Data freshness
            if not df.empty:
                latest_time = pd.to_datetime(df['time'].max())
                now = datetime.utcnow()
                freshness_minutes = (now - latest_time).total_seconds() / 60
                report["metrics"]["data_freshness_minutes"] = freshness_minutes
            
        except Exception as e:
            logger.error(f"Failed to generate quality report: {e}")
            report["error"] = str(e)
        
        return report
    
    def check_data_quality_alerts(self) -> list:
        """Check for data quality issues that require attention."""
        alerts = []
        
        try:
            # Get recent data
            df = self.db_handler.get_telemetry_data(hours=1)
            
            if df.empty:
                alerts.append({
                    "severity": "WARNING",
                    "message": "No data received in the last hour",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return alerts
            
            # Check for missing devices
            expected_devices = 5  # Based on our sample devices
            active_devices = df['device_id'].nunique()
            if active_devices < expected_devices:
                alerts.append({
                    "severity": "WARNING",
                    "message": f"Only {active_devices} of {expected_devices} devices reporting",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Check for data gaps
            df_sorted = df.sort_values('time')
            time_diffs = df_sorted['time'].diff()
            large_gaps = time_diffs[time_diffs > timedelta(minutes=10)]
            
            if not large_gaps.empty:
                alerts.append({
                    "severity": "WARNING",
                    "message": f"Found {len(large_gaps)} data gaps > 10 minutes",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Check for extreme values
            for col in ['temperature', 'humidity', 'pressure']:
                if col in df.columns:
                    q99 = df[col].quantile(0.99)
                    q01 = df[col].quantile(0.01)
                    outliers = df[(df[col] > q99) | (df[col] < q01)]
                    
                    if len(outliers) > len(df) * 0.05:  # More than 5% outliers
                        alerts.append({
                            "severity": "WARNING",
                            "message": f"High number of {col} outliers: {len(outliers)} records",
                            "timestamp": datetime.utcnow().isoformat()
                        })
        
        except Exception as e:
            alerts.append({
                "severity": "ERROR",
                "message": f"Failed to check data quality: {e}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def print_quality_summary(self):
        """Print a formatted data quality summary."""
        report = self.generate_quality_report()
        alerts = self.check_data_quality_alerts()
        
        print("\n" + "="*60)
        print("DATA QUALITY REPORT")
        print("="*60)
        print(f"Generated: {report['timestamp']}")
        print(f"Period: Last {report['period_hours']} hours")
        
        if "error" in report:
            print(f"ERROR: {report['error']}")
            return
        
        metrics = report.get("metrics", {})
        
        if "message" in metrics:
            print(f"\n{metrics['message']}")
            return
        
        print(f"\nBASIC METRICS:")
        print(f"  Total Records: {metrics.get('total_records', 0):,}")
        print(f"  Unique Devices: {metrics.get('unique_devices', 0)}")
        
        if "time_range" in metrics:
            time_range = metrics["time_range"]
            print(f"  Time Range: {time_range.get('start', 'N/A')} to {time_range.get('end', 'N/A')}")
        
        if "data_freshness_minutes" in metrics:
            freshness = metrics["data_freshness_minutes"]
            print(f"  Data Freshness: {freshness:.1f} minutes ago")
        
        print(f"\nDATA COMPLETENESS:")
        completeness = metrics.get("completeness", {})
        for field, stats in completeness.items():
            rate = stats["completeness_rate"] * 100
            print(f"  {field}: {rate:.1f}% ({stats['non_null_count']} records)")
        
        print(f"\nALERTS:")
        if alerts:
            for alert in alerts:
                print(f"  [{alert['severity']}] {alert['message']}")
        else:
            print("  No alerts")
        
        print("="*60)

if __name__ == "__main__":
    monitor = DataQualityMonitor()
    monitor.print_quality_summary()