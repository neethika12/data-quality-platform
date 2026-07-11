import pandas as pd
import json
import uuid
from datetime import datetime
from typing import Dict, Optional
from backend.services.schema_validator import SchemaValidator
from backend.services.drift_detector import DriftDetector
from backend.services.anomaly_detector import AnomalyDetector
from backend.services.completeness import CompletenessChecker
from backend.services.alerter import Alerter
from backend.database import Database
from backend.config import settings
from backend.utils.file_handlers import FileHandler

class QualityChecker:
    def __init__(self):
        self.schema_validator = SchemaValidator()
        self.drift_detector = DriftDetector()
        self.anomaly_detector = AnomalyDetector(
            null_rate_warning=settings.NULL_RATE_WARNING,
            null_rate_critical=settings.NULL_RATE_CRITICAL
        )
        self.completeness_checker = CompletenessChecker(
            freshness_warning_hours=settings.FRESHNESS_WARNING_HOURS,
            freshness_critical_hours=settings.FRESHNESS_CRITICAL_HOURS,
            record_drop_warning_percent=settings.RECORD_DROP_WARNING_PERCENT
        )

    def run_full_check(self, dataset_id: str, df: pd.DataFrame,
                       last_update_timestamp: Optional[datetime] = None) -> Dict:
        """Run complete quality check on dataset."""

        # Get baseline from database
        dataset_info = Database.get_dataset(dataset_id)

        if not dataset_info:
            # First upload - establish baseline
            return self._initialize_baseline(dataset_id, df)

        # Parse baseline
        baseline_schema = json.loads(dataset_info.get("baseline_schema") or "{}")
        baseline_data = json.loads(dataset_info.get("baseline_data") or "{}")

        if not baseline_schema:
            # Legacy/edge case: dataset exists but no baseline was ever captured. Establish it now
            # from the current data instead of comparing against nothing.
            return self._initialize_baseline(dataset_id, df)

        # 1. Schema Validation
        schema_result = self.schema_validator.validate_schema(df, baseline_schema)

        # 2. Drift Detection — compare current data against the ORIGINAL baseline sample
        # captured at upload time, so drift reflects real change over time rather than a
        # dataset compared against itself.
        if baseline_data:
            baseline_df = pd.DataFrame(baseline_data)
            self.drift_detector.fit_baseline(baseline_df)
            drift_result = self.drift_detector.detect_drift(df)
        else:
            drift_result = {"drifted_features": [], "overall_drift_score": 0.0,
                           "severity_level": "INFO", "feature_count": len(df.columns),
                           "drifted_count": 0, "timestamp": datetime.utcnow().isoformat()}

        # 3. Anomaly Detection
        self.anomaly_detector.fit_baseline(df)
        anomaly_result = self.anomaly_detector.detect_anomalies(df, baseline_df=None)

        # 4. Completeness Check
        self.completeness_checker.fit_baseline(df, last_update_timestamp)
        completeness_result = self.completeness_checker.check_completeness(
            df, last_update_timestamp
        )

        # 5. Calculate Overall Quality Score
        overall_quality_score = self._calculate_overall_score(
            schema_result, drift_result, anomaly_result, completeness_result
        )

        # 6. Generate Alerts
        alerts = self._generate_all_alerts(
            dataset_id, schema_result, drift_result, anomaly_result, completeness_result
        )

        # Store alerts
        stored_alerts = Alerter.store_alerts(alerts)

        # 7. Store results
        result_id = str(uuid.uuid4())
        Database.store_quality_result(
            result_id, dataset_id, schema_result, drift_result,
            anomaly_result, completeness_result, overall_quality_score
        )

        # Update last analyzed
        Database.update_dataset_analyzed(dataset_id)

        return {
            "result_id": result_id,
            "dataset_id": dataset_id,
            "schema_validation": schema_result,
            "drift_analysis": drift_result,
            "anomaly_detection": anomaly_result,
            "completeness": completeness_result,
            "overall_quality_score": overall_quality_score,
            "alerts": stored_alerts,
            "alert_summary": Alerter.summarize_alerts(stored_alerts),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _initialize_baseline(self, dataset_id: str, df: pd.DataFrame) -> Dict:
        """Initialize baseline for first upload (or for a legacy dataset that never got one)."""
        schema = SchemaValidator.extract_schema(df)
        stats = {}

        for col in df.columns:
            stats[col] = StatisticalTester.calculate_distribution_stats(df[col])

        baseline_data = FileHandler.dataframe_to_baseline_sample(df)

        # Preserve the existing name/description if this dataset row already exists
        existing = Database.get_dataset(dataset_id)
        name = existing["name"] if existing else f"Dataset {dataset_id[:8]}"
        description = existing["description"] if existing else ""

        # Store baseline
        Database.store_dataset(
            dataset_id, name, description,
            len(df), len(df.columns), schema, stats, baseline_data
        )

        return {
            "result_id": None,
            "status": "baseline_initialized",
            "row_count": len(df),
            "column_count": len(df.columns),
            "schema": schema,
            "message": "Baseline established. Run analysis on next upload to detect changes.",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _calculate_overall_score(self, schema_result: Dict, drift_result: Dict,
                                 anomaly_result: Dict, completeness_result: Dict) -> float:
        """Calculate weighted overall quality score."""
        scores = []

        # Schema quality (20% weight)
        schema_score = 1.0 if not schema_result.get("changes") else 0.8
        scores.append(("schema", schema_score, 0.2))

        # Drift quality (25% weight)
        drift_score = 1.0 - drift_result.get("overall_drift_score", 0.0)
        scores.append(("drift", drift_score, 0.25))

        # Anomaly quality (25% weight)
        anomaly_score = 1.0 - anomaly_result.get("anomaly_score", 0.0)
        scores.append(("anomaly", anomaly_score, 0.25))

        # Completeness quality (30% weight)
        completeness_score = completeness_result.get("completeness_score", 1.0)
        scores.append(("completeness", completeness_score, 0.3))

        overall_score = sum(score * weight for _, score, weight in scores)
        return float(min(1.0, max(0.0, overall_score)))

    def _generate_all_alerts(self, dataset_id: str, schema_result: Dict,
                            drift_result: Dict, anomaly_result: Dict,
                            completeness_result: Dict) -> list:
        """Generate all alerts from quality checks."""
        alerts = []

        # Schema alerts
        alerts.extend(Alerter.generate_alerts_from_schema(
            dataset_id, schema_result.get("changes", [])
        ))

        # Drift alerts
        alerts.extend(Alerter.generate_alerts_from_drift(
            dataset_id, drift_result, settings.DRIFT_WARNING_THRESHOLD
        ))

        # Anomaly alerts
        alerts.extend(Alerter.generate_alerts_from_anomalies(
            dataset_id, anomaly_result, settings.NULL_RATE_CRITICAL
        ))

        # Completeness alerts
        alerts.extend(Alerter.generate_alerts_from_completeness(
            dataset_id, completeness_result
        ))

        return alerts


from backend.utils.stats import StatisticalTester
