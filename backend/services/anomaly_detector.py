import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from backend.utils.stats import StatisticalTester
from backend.models import AlertSeverity

class AnomalyDetector:
    def __init__(self, null_rate_warning: float = 0.05, null_rate_critical: float = 0.10):
        self.null_rate_warning = null_rate_warning
        self.null_rate_critical = null_rate_critical
        self.baseline_null_rates = {}

    def fit_baseline(self, df: pd.DataFrame):
        """Store baseline null rates and statistics."""
        for col in df.columns:
            null_rate = df[col].isna().sum() / len(df)
            self.baseline_null_rates[col] = null_rate

    def check_nulls(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Analyze null values per column."""
        null_analysis = {}

        for col in df.columns:
            null_count = int(df[col].isna().sum())
            null_rate = null_count / len(df)

            # Determine status
            status = "OK"
            if null_rate >= self.null_rate_critical:
                status = "CRITICAL"
            elif null_rate >= self.null_rate_warning:
                status = "WARNING"

            null_analysis[col] = {
                "null_count": null_count,
                "null_rate": float(null_rate),
                "status": status
            }

        return null_analysis

    def detect_outliers(self, df: pd.DataFrame, method: str = "iqr") -> Dict[str, Dict]:
        """Detect outliers using IQR or Z-score method."""
        outliers = {}

        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue

            if method == "iqr":
                indices, stats_dict = StatisticalTester.detect_outliers_iqr(df[col])
            elif method == "zscore":
                indices = StatisticalTester.detect_outliers_zscore(df[col])
                stats_dict = {}
            else:
                continue

            if len(indices) > 0:
                outliers[col] = {
                    "outlier_count": int(len(indices)),
                    "method": method,
                    "indices": indices.tolist()[:100],  # Limit to first 100
                    "percentage": float(len(indices) / len(df) * 100),
                    "stats": stats_dict
                }

        return outliers

    def check_domain_rules(self, df: pd.DataFrame, rules: Optional[List[Dict]] = None) -> Dict[str, Dict]:
        """Check for domain-specific rule violations."""
        violations = {}

        if not rules:
            # Default rules
            rules = []

        for rule in rules:
            rule_type = rule.get("rule_type")
            column = rule.get("column")
            rule_name = rule.get("name")

            if column not in df.columns:
                continue

            col = df[column]
            violation_count = 0

            if rule_type == "negative_values" and pd.api.types.is_numeric_dtype(col):
                violation_count = (col < 0).sum()

            elif rule_type == "future_dates":
                try:
                    col_dt = pd.to_datetime(col, errors='coerce')
                    violation_count = (col_dt > pd.Timestamp.now()).sum()
                except:
                    pass

            elif rule_type == "null_values":
                violation_count = col.isna().sum()

            elif rule_type == "custom" and "validator" in rule:
                violation_count = rule["validator"](col)

            if violation_count > 0:
                violations[rule_name or f"{rule_type}_{column}"] = {
                    "count": int(violation_count),
                    "percentage": float(violation_count / len(df) * 100),
                    "severity": rule.get("severity", "WARNING")
                }

        return violations

    def detect_anomalies(self, df: pd.DataFrame, baseline_df: Optional[pd.DataFrame] = None) -> Dict:
        """Comprehensive anomaly detection."""
        null_analysis = self.check_nulls(df)
        outliers = self.detect_outliers(df)

        # Count total anomalies
        total_anomalies = 0
        total_anomalies += sum(a["null_count"] for a in null_analysis.values())
        total_anomalies += sum(o["outlier_count"] for o in outliers.values())

        # Calculate anomaly score
        anomaly_score = min(1.0, total_anomalies / (len(df) * len(df.columns)))

        return {
            "null_analysis": {
                col: {
                    "null_count": v["null_count"],
                    "null_rate": v["null_rate"],
                    "status": v["status"]
                }
                for col, v in null_analysis.items()
            },
            "outliers": outliers,
            "domain_violations": self.check_domain_rules(df),
            "total_anomalies": total_anomalies,
            "anomaly_score": float(anomaly_score),
            "timestamp": datetime.utcnow().isoformat()
        }

    def detect_sudden_spikes(self, historical_null_rates: List[Dict]) -> List[Dict]:
        """Detect sudden spikes in null rates."""
        spikes = []

        if len(historical_null_rates) < 2:
            return spikes

        for column in historical_null_rates[0].keys():
            rates = [h.get(column, 0) for h in historical_null_rates]

            if len(rates) < 2:
                continue

            current_rate = rates[-1]
            previous_rate = rates[-2]
            increase = abs(current_rate - previous_rate)

            if increase > 0.05:  # 5% change threshold
                spikes.append({
                    "column": column,
                    "previous_rate": float(previous_rate),
                    "current_rate": float(current_rate),
                    "increase": float(increase),
                    "severity": AlertSeverity.WARNING.value if increase < 0.15 else AlertSeverity.CRITICAL.value
                })

        return spikes
