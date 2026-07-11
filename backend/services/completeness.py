import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
from backend.models import AlertSeverity

class CompletenessChecker:
    def __init__(self, freshness_warning_hours: int = 24, freshness_critical_hours: int = 48,
                 record_drop_warning_percent: float = 0.10):
        self.freshness_warning_hours = freshness_warning_hours
        self.freshness_critical_hours = freshness_critical_hours
        self.record_drop_warning_percent = record_drop_warning_percent
        self.baseline_record_count = None
        self.baseline_timestamp = None

    def fit_baseline(self, df: pd.DataFrame, timestamp: Optional[datetime] = None):
        """Store baseline record count and timestamp."""
        self.baseline_record_count = len(df)
        self.baseline_timestamp = timestamp or datetime.utcnow()

    def check_record_count(self, df: pd.DataFrame) -> Dict:
        """Check if record count dropped unexpectedly."""
        current_count = len(df)
        dropped = 0
        dropped_percent = 0.0
        status = "OK"

        if self.baseline_record_count and self.baseline_record_count > 0:
            dropped = self.baseline_record_count - current_count
            dropped_percent = dropped / self.baseline_record_count

            if dropped_percent > self.record_drop_warning_percent:
                status = "CRITICAL"
            elif dropped_percent > 0.05:
                status = "WARNING"

        return {
            "current_count": current_count,
            "baseline_count": self.baseline_record_count or current_count,
            "dropped": int(dropped),
            "dropped_percent": float(dropped_percent),
            "status": status
        }

    def check_freshness(self, last_update_timestamp: Optional[datetime] = None) -> Dict:
        """Check data freshness (time since last update)."""
        if last_update_timestamp is None:
            return {
                "hours_since_update": 0,
                "status": "UNKNOWN",
                "severity": AlertSeverity.INFO.value
            }

        now = datetime.utcnow()
        time_diff = now - last_update_timestamp
        hours_since = time_diff.total_seconds() / 3600

        if hours_since > self.freshness_critical_hours:
            status = "CRITICAL"
            severity = AlertSeverity.CRITICAL.value
        elif hours_since > self.freshness_warning_hours:
            status = "WARNING"
            severity = AlertSeverity.WARNING.value
        else:
            status = "OK"
            severity = AlertSeverity.INFO.value

        return {
            "hours_since_update": float(hours_since),
            "last_update": last_update_timestamp.isoformat(),
            "status": status,
            "severity": severity
        }

    def calculate_completeness_score(self, df: pd.DataFrame) -> float:
        """Calculate overall completeness score (0-1)."""
        total_cells = len(df) * len(df.columns)
        null_cells = df.isna().sum().sum()
        completeness = (total_cells - null_cells) / total_cells if total_cells > 0 else 1.0
        return float(completeness)

    def check_coverage(self, df: pd.DataFrame, expected_records: Optional[int] = None) -> Dict:
        """Check data coverage metrics."""
        actual_records = len(df)
        coverage_percent = 100.0

        if expected_records:
            coverage_percent = (actual_records / expected_records) * 100

        return {
            "expected_records": expected_records,
            "actual_records": actual_records,
            "coverage_percent": float(coverage_percent)
        }

    def check_completeness(self, df: pd.DataFrame,
                          last_update_timestamp: Optional[datetime] = None,
                          expected_records: Optional[int] = None) -> Dict:
        """Comprehensive completeness check."""
        completeness_score = self.calculate_completeness_score(df)
        record_count = self.check_record_count(df)
        freshness = self.check_freshness(last_update_timestamp)
        coverage = self.check_coverage(df, expected_records)

        # Overall status
        statuses = [record_count["status"], freshness["status"]]
        if "CRITICAL" in statuses:
            overall_status = "CRITICAL"
        elif "WARNING" in statuses:
            overall_status = "WARNING"
        else:
            overall_status = "OK"

        return {
            "completeness_score": completeness_score,
            "record_count": record_count,
            "freshness": freshness,
            "coverage": coverage,
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat()
        }
