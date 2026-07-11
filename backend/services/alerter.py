import uuid
from datetime import datetime
from typing import List, Dict, Optional
from backend.models import AlertSeverity, AlertStatus
from backend.database import Database

class Alerter:
    SEVERITY_PRIORITY = {
        AlertSeverity.CRITICAL.value: 3,
        AlertSeverity.WARNING.value: 2,
        AlertSeverity.INFO.value: 1
    }

    @staticmethod
    def generate_alerts_from_schema(dataset_id: str, schema_changes: List[Dict]) -> List[Dict]:
        """Generate alerts from schema changes."""
        alerts = []

        for change in schema_changes:
            if change["type"] == "MISSING_COLUMN":
                alerts.append({
                    "dataset_id": dataset_id,
                    "metric_type": "schema_missing_column",
                    "severity": AlertSeverity.CRITICAL.value,
                    "message": f"Column '{change['column']}' is missing (was {change['old']})",
                    "value": 1.0,
                    "threshold": 0.0
                })
            elif change["type"] == "NEW_COLUMN":
                alerts.append({
                    "dataset_id": dataset_id,
                    "metric_type": "schema_new_column",
                    "severity": AlertSeverity.INFO.value,
                    "message": f"New column '{change['column']}' detected ({change['new']})",
                    "value": 1.0,
                    "threshold": 0.0
                })
            elif change["type"] == "TYPE_CHANGE":
                alerts.append({
                    "dataset_id": dataset_id,
                    "metric_type": "schema_type_change",
                    "severity": change["severity"],
                    "message": f"Type change in '{change['column']}': {change['old']} → {change['new']}",
                    "value": 1.0,
                    "threshold": 0.0
                })

        return alerts

    @staticmethod
    def generate_alerts_from_drift(dataset_id: str, drift_analysis: Dict,
                                   drift_warning_threshold: float = 0.3) -> List[Dict]:
        """Generate alerts from drift analysis."""
        alerts = []

        overall_drift = drift_analysis.get("overall_drift_score", 0.0)

        if overall_drift > drift_warning_threshold:
            severity = drift_analysis.get("severity_level", AlertSeverity.WARNING.value)
            drifted_count = drift_analysis.get("drifted_count", 0)

            alerts.append({
                "dataset_id": dataset_id,
                "metric_type": "distribution_drift",
                "severity": severity,
                "message": f"{drifted_count} features showing distribution drift (score: {overall_drift:.2f})",
                "value": overall_drift,
                "threshold": drift_warning_threshold
            })

            # Per-feature drift alerts for critical drifts
            for feature in drift_analysis.get("drifted_features", []):
                if feature["drift_score"] > 0.7:
                    alerts.append({
                        "dataset_id": dataset_id,
                        "metric_type": "feature_drift",
                        "severity": AlertSeverity.WARNING.value,
                        "message": f"High drift in feature '{feature['feature']}': {feature['interpretation']}",
                        "value": feature["drift_score"],
                        "threshold": 0.7
                    })

        return alerts

    @staticmethod
    def generate_alerts_from_anomalies(dataset_id: str, anomaly_detection: Dict,
                                       null_rate_critical: float = 0.10) -> List[Dict]:
        """Generate alerts from anomaly detection."""
        alerts = []

        # High null rate alerts
        for col, null_info in anomaly_detection.get("null_analysis", {}).items():
            if null_info["status"] == "CRITICAL":
                alerts.append({
                    "dataset_id": dataset_id,
                    "metric_type": "high_null_rate",
                    "severity": AlertSeverity.CRITICAL.value,
                    "message": f"Critical null rate in '{col}': {null_info['null_rate']:.1%}",
                    "value": null_info["null_rate"],
                    "threshold": null_rate_critical
                })
            elif null_info["status"] == "WARNING":
                alerts.append({
                    "dataset_id": dataset_id,
                    "metric_type": "high_null_rate",
                    "severity": AlertSeverity.WARNING.value,
                    "message": f"High null rate in '{col}': {null_info['null_rate']:.1%}",
                    "value": null_info["null_rate"],
                    "threshold": 0.05
                })

        # Outlier alerts
        if anomaly_detection.get("outliers"):
            outlier_count = sum(o["outlier_count"] for o in anomaly_detection["outliers"].values())
            if outlier_count > 0:
                alerts.append({
                    "dataset_id": dataset_id,
                    "metric_type": "outliers_detected",
                    "severity": AlertSeverity.INFO.value,
                    "message": f"{outlier_count} outliers detected across columns",
                    "value": float(outlier_count),
                    "threshold": 0.0
                })

        # Domain violation alerts
        for violation_name, violation_info in anomaly_detection.get("domain_violations", {}).items():
            alerts.append({
                "dataset_id": dataset_id,
                "metric_type": "domain_violation",
                "severity": violation_info.get("severity", AlertSeverity.WARNING.value),
                "message": f"Domain violation '{violation_name}': {violation_info['count']} occurrences",
                "value": float(violation_info["count"]),
                "threshold": 0.0
            })

        return alerts

    @staticmethod
    def generate_alerts_from_completeness(dataset_id: str, completeness: Dict) -> List[Dict]:
        """Generate alerts from completeness checks."""
        alerts = []

        # Record count alert
        record_info = completeness.get("record_count", {})
        if record_info.get("status") == "CRITICAL":
            alerts.append({
                "dataset_id": dataset_id,
                "metric_type": "record_count_drop",
                "severity": AlertSeverity.CRITICAL.value,
                "message": f"Critical record count drop: {record_info['dropped']} records ({record_info['dropped_percent']:.1%})",
                "value": record_info["dropped_percent"],
                "threshold": 0.10
            })
        elif record_info.get("status") == "WARNING":
            alerts.append({
                "dataset_id": dataset_id,
                "metric_type": "record_count_drop",
                "severity": AlertSeverity.WARNING.value,
                "message": f"Record count dropped by {record_info['dropped_percent']:.1%}",
                "value": record_info["dropped_percent"],
                "threshold": 0.05
            })

        # Freshness alert
        freshness = completeness.get("freshness", {})
        if freshness.get("status") == "CRITICAL":
            alerts.append({
                "dataset_id": dataset_id,
                "metric_type": "data_freshness",
                "severity": AlertSeverity.CRITICAL.value,
                "message": f"Data is stale: {freshness['hours_since_update']:.1f} hours since last update",
                "value": freshness["hours_since_update"],
                "threshold": 48.0
            })
        elif freshness.get("status") == "WARNING":
            alerts.append({
                "dataset_id": dataset_id,
                "metric_type": "data_freshness",
                "severity": AlertSeverity.WARNING.value,
                "message": f"Data is aging: {freshness['hours_since_update']:.1f} hours since last update",
                "value": freshness["hours_since_update"],
                "threshold": 24.0
            })

        return alerts

    @staticmethod
    def store_alerts(alerts: List[Dict]):
        """Store alerts in database."""
        stored_alerts = []
        for alert in alerts:
            alert_id = str(uuid.uuid4())
            Database.store_alert(
                alert_id=alert_id,
                dataset_id=alert["dataset_id"],
                metric_type=alert["metric_type"],
                severity=alert["severity"],
                message=alert["message"],
                value=alert["value"],
                threshold=alert["threshold"]
            )
            alert["id"] = alert_id
            stored_alerts.append(alert)

        return stored_alerts

    @staticmethod
    def deduplicate_alerts(alerts: List[Dict], existing_alerts: List[Dict]) -> List[Dict]:
        """Remove duplicate alerts that were already triggered."""
        new_alerts = []

        for alert in alerts:
            # Check if similar alert exists with ACTIVE status
            duplicate = any(
                e.get("metric_type") == alert["metric_type"] and
                e.get("status") == "ACTIVE"
                for e in existing_alerts
            )
            if not duplicate:
                new_alerts.append(alert)

        return new_alerts

    @staticmethod
    def summarize_alerts(alerts: List[Dict]) -> Dict:
        """Summarize alerts by severity."""
        summary = {
            AlertSeverity.CRITICAL.value: [],
            AlertSeverity.WARNING.value: [],
            AlertSeverity.INFO.value: []
        }

        for alert in alerts:
            severity = alert.get("severity", AlertSeverity.INFO.value)
            if severity in summary:
                summary[severity].append(alert)

        return {
            "critical_count": len(summary[AlertSeverity.CRITICAL.value]),
            "warning_count": len(summary[AlertSeverity.WARNING.value]),
            "info_count": len(summary[AlertSeverity.INFO.value]),
            "total_count": len(alerts),
            "critical_alerts": summary[AlertSeverity.CRITICAL.value],
            "warning_alerts": summary[AlertSeverity.WARNING.value],
            "info_alerts": summary[AlertSeverity.INFO.value]
        }
