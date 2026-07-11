import json
from datetime import datetime
from typing import Dict, List, Optional
import os

class ReportGenerator:
    """Generate summary reports from quality analysis results."""

    @staticmethod
    def generate_text_report(dataset_id: str, result: Dict, alert_summary: Optional[Dict] = None) -> str:
        """Generate a text-based report."""
        report = []
        report.append("=" * 80)
        report.append("DATA QUALITY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Header
        report.append(f"Dataset ID: {dataset_id}")
        report.append(f"Analysis Time: {result.get('timestamp', 'N/A')}")
        report.append("")

        # Overall Score
        quality_score = result.get("overall_quality_score", 0.0)
        report.append(f"OVERALL QUALITY SCORE: {quality_score:.1%}")
        report.append(f"Status: {'✅ PASS' if quality_score >= 0.80 else '⚠️ WARNING' if quality_score >= 0.60 else '❌ CRITICAL'}")
        report.append("")

        # Completeness
        report.append("COMPLETENESS ANALYSIS")
        report.append("-" * 40)
        completeness = result.get("completeness", {})
        completeness_score = completeness.get("completeness_score", 0.0)
        record_count = completeness.get("record_count", {})
        freshness = completeness.get("freshness", {})

        report.append(f"  Completeness Score: {completeness_score:.1%}")
        report.append(f"  Record Count: {record_count.get('current_count', 0):,}")
        report.append(f"  Status: {record_count.get('status', 'UNKNOWN')}")
        report.append(f"  Data Freshness: {freshness.get('hours_since_update', 0):.1f} hours")
        report.append(f"  Freshness Status: {freshness.get('status', 'UNKNOWN')}")
        report.append("")

        # Schema Changes
        report.append("SCHEMA VALIDATION")
        report.append("-" * 40)
        schema = result.get("schema_validation", {})
        changes = schema.get("changes", [])
        report.append(f"  Changes Detected: {len(changes)}")
        report.append(f"  Breaking Changes: {'YES ⚠️' if schema.get('is_breaking') else 'NO ✅'}")

        if changes:
            report.append("  ")
            report.append("  Change Details:")
            for change in changes:
                report.append(f"    - {change['type']}: {change['column']}")
                if change.get('old') and change.get('new'):
                    report.append(f"      {change['old']} → {change['new']}")
        report.append("")

        # Drift Analysis
        report.append("DISTRIBUTION DRIFT ANALYSIS")
        report.append("-" * 40)
        drift = result.get("drift_analysis", {})
        drift_score = drift.get("overall_drift_score", 0.0)
        drifted_features = drift.get("drifted_features", [])

        report.append(f"  Overall Drift Score: {drift_score:.2f}")
        report.append(f"  Severity: {drift.get('severity_level', 'INFO')}")
        report.append(f"  Features Analyzed: {drift.get('feature_count', 0)}")
        report.append(f"  Features Drifted: {drift.get('drifted_count', 0)}")

        if drifted_features:
            report.append("  ")
            report.append("  Drifted Features (Top 5):")
            for feature in drifted_features[:5]:
                report.append(f"    - {feature['feature']}")
                report.append(f"      Drift Score: {feature['drift_score']:.3f}")
                report.append(f"      P-Value: {feature['p_value']:.6f}")
                report.append(f"      Test: {feature['test_method']}")
        report.append("")

        # Anomaly Detection
        report.append("ANOMALY DETECTION")
        report.append("-" * 40)
        anomalies = result.get("anomaly_detection", {})
        anomaly_score = anomalies.get("anomaly_score", 0.0)
        total_anomalies = anomalies.get("total_anomalies", 0)

        report.append(f"  Total Anomalies: {total_anomalies}")
        report.append(f"  Anomaly Score: {anomaly_score:.3f}")

        null_analysis = anomalies.get("null_analysis", {})
        high_null_cols = [c for c, info in null_analysis.items() if info.get("status") in ["WARNING", "CRITICAL"]]
        if high_null_cols:
            report.append(f"  Columns with High Null Rate: {len(high_null_cols)}")
            for col in high_null_cols[:5]:
                null_rate = null_analysis[col]["null_rate"]
                report.append(f"    - {col}: {null_rate:.1%}")

        outliers = anomalies.get("outliers", {})
        if outliers:
            report.append(f"  Columns with Outliers: {len(outliers)}")
            for col in list(outliers.keys())[:5]:
                count = outliers[col]["outlier_count"]
                report.append(f"    - {col}: {count} outliers")
        report.append("")

        # Alerts Summary
        if alert_summary:
            report.append("ALERTS SUMMARY")
            report.append("-" * 40)
            report.append(f"  Critical: {alert_summary.get('critical_count', 0)} 🔴")
            report.append(f"  Warnings: {alert_summary.get('warning_count', 0)} 🟡")
            report.append(f"  Info: {alert_summary.get('info_count', 0)} 🔵")
            report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        recommendations = ReportGenerator._generate_recommendations(result)
        for rec in recommendations:
            report.append(f"  • {rec}")
        report.append("")

        report.append("=" * 80)
        report.append(f"Report Generated: {datetime.utcnow().isoformat()}")
        report.append("=" * 80)

        return "\n".join(report)

    @staticmethod
    def generate_json_report(dataset_id: str, result: Dict, alert_summary: Optional[Dict] = None) -> Dict:
        """Generate JSON report."""
        return {
            "dataset_id": dataset_id,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_quality_score": result.get("overall_quality_score", 0.0),
            "completeness": result.get("completeness", {}),
            "schema_validation": result.get("schema_validation", {}),
            "drift_analysis": result.get("drift_analysis", {}),
            "anomaly_detection": result.get("anomaly_detection", {}),
            "alerts": alert_summary or {},
            "recommendations": ReportGenerator._generate_recommendations(result)
        }

    @staticmethod
    def export_report(dataset_id: str, result: Dict, format: str = "json",
                     alert_summary: Optional[Dict] = None) -> str:
        """Export report to file."""
        from backend.config import settings

        os.makedirs(os.path.join(settings.UPLOAD_DIR, "reports"), exist_ok=True)

        if format == "json":
            report_data = ReportGenerator.generate_json_report(dataset_id, result, alert_summary)
            filename = os.path.join(settings.UPLOAD_DIR, "reports", f"report_{dataset_id}.json")
            with open(filename, "w") as f:
                json.dump(report_data, f, indent=2)

        elif format == "txt":
            report_text = ReportGenerator.generate_text_report(dataset_id, result, alert_summary)
            filename = os.path.join(settings.UPLOAD_DIR, "reports", f"report_{dataset_id}.txt")
            with open(filename, "w") as f:
                f.write(report_text)

        return filename

    @staticmethod
    def _generate_recommendations(result: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Quality score
        quality_score = result.get("overall_quality_score", 0.0)
        if quality_score < 0.7:
            recommendations.append("Quality score is low. Investigate null rates and distribution changes.")

        # Completeness
        completeness = result.get("completeness", {})
        freshness = completeness.get("freshness", {})
        if freshness.get("status") == "CRITICAL":
            recommendations.append("Data is stale. Check upstream data pipeline for failures.")

        record_info = completeness.get("record_count", {})
        if record_info.get("status") == "CRITICAL":
            recommendations.append("Record count dropped significantly. Investigate data loss.")

        # Schema changes
        schema = result.get("schema_validation", {})
        if schema.get("is_breaking"):
            recommendations.append("Breaking schema changes detected. Update downstream consumers.")

        # Drift
        drift = result.get("drift_analysis", {})
        if drift.get("severity_level") == "CRITICAL":
            drifted_features = drift.get("drifted_features", [])
            feature_names = [f["feature"] for f in drifted_features[:3]]
            recommendations.append(f"Significant drift detected in: {', '.join(feature_names)}. Update baseline or investigate source.")

        # Anomalies
        anomalies = result.get("anomaly_detection", {})
        null_analysis = anomalies.get("null_analysis", {})
        high_null = [c for c, info in null_analysis.items() if info.get("null_rate", 0) > 0.1]
        if high_null:
            recommendations.append(f"High null rates in: {', '.join(high_null[:3])}. Investigate data source.")

        if not recommendations:
            recommendations.append("Data quality looks good! Continue monitoring for changes.")

        return recommendations
