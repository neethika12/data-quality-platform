import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
from backend.utils.stats import StatisticalTester
from backend.models import AlertSeverity

class DriftDetector:
    def __init__(self):
        self.baseline_stats = None
        self.baseline_df = None

    def fit_baseline(self, df: pd.DataFrame):
        """Store baseline distribution statistics."""
        self.baseline_df = df.copy()
        self.baseline_stats = {}

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                self.baseline_stats[col] = {
                    "type": "numeric",
                    "stats": StatisticalTester.calculate_distribution_stats(df[col])
                }
            else:
                self.baseline_stats[col] = {
                    "type": "categorical",
                    "stats": StatisticalTester.calculate_distribution_stats(df[col])
                }

    def detect_drift(self, current_df: pd.DataFrame) -> Dict:
        """Detect distribution drift in current data."""
        if self.baseline_df is None:
            raise ValueError("Baseline not fitted. Call fit_baseline first.")

        drifted_features = []
        overall_score = 0.0

        # Find common columns
        common_cols = set(self.baseline_df.columns) & set(current_df.columns)

        for col in common_cols:
            baseline_col = self.baseline_df[col]
            current_col = current_df[col]

            # Skip if no baseline stats
            if col not in self.baseline_stats:
                continue

            col_type = self.baseline_stats[col]["type"]

            if col_type == "numeric" and pd.api.types.is_numeric_dtype(current_col):
                statistic, p_value = StatisticalTester.kolmogorov_smirnov_test(
                    baseline_col, current_col
                )
                drift_score = StatisticalTester.drift_severity_score(p_value, "ks")
                test_method = "Kolmogorov-Smirnov"

            elif col_type == "categorical" or not pd.api.types.is_numeric_dtype(current_col):
                statistic, p_value = StatisticalTester.chi_squared_test(
                    baseline_col, current_col
                )
                drift_score = StatisticalTester.drift_severity_score(p_value, "chi2")
                test_method = "Chi-Squared"

            else:
                continue

            if drift_score > 0.0:
                interpretation = self._interpret_drift(drift_score, p_value)
                drifted_features.append({
                    "feature": col,
                    "drift_score": float(drift_score),
                    "p_value": float(p_value),
                    "test_method": test_method,
                    "interpretation": interpretation
                })

        # Calculate overall drift
        if drifted_features:
            overall_score = np.mean([f["drift_score"] for f in drifted_features])

        severity_level = self._classify_severity(overall_score)

        return {
            "drifted_features": drifted_features,
            "overall_drift_score": float(overall_score),
            "severity_level": severity_level,
            "feature_count": len(common_cols),
            "drifted_count": len(drifted_features),
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def _interpret_drift(drift_score: float, p_value: float) -> str:
        """Generate interpretation of drift."""
        if drift_score < 0.1:
            return "No significant drift detected"
        elif drift_score < 0.3:
            return "Mild drift detected, monitor closely"
        elif drift_score < 0.7:
            return "Moderate drift detected, investigate"
        else:
            return "Severe drift detected, immediate action recommended"

    @staticmethod
    def _classify_severity(drift_score: float) -> str:
        """Classify overall drift severity."""
        if drift_score < 0.3:
            return AlertSeverity.INFO.value
        elif drift_score < 0.7:
            return AlertSeverity.WARNING.value
        else:
            return AlertSeverity.CRITICAL.value

    def get_historical_drift_trends(self, historical_results: List[Dict]) -> Dict:
        """Analyze historical drift trends."""
        if not historical_results:
            return {}

        drift_scores = [r["overall_drift_score"] for r in historical_results if "overall_drift_score" in r]
        timestamps = [r["timestamp"] for r in historical_results if "timestamp" in r]

        if len(drift_scores) < 2:
            return {"trend": "insufficient_data"}

        trend = "increasing" if drift_scores[-1] > drift_scores[0] else "decreasing"

        return {
            "trend": trend,
            "min_drift": float(min(drift_scores)),
            "max_drift": float(max(drift_scores)),
            "current_drift": float(drift_scores[-1]),
            "average_drift": float(np.mean(drift_scores)),
            "data_points": len(drift_scores)
        }
