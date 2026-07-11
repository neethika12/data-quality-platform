from fastapi import APIRouter, HTTPException
from typing import Optional
import json
from backend.services.report_generator import ReportGenerator
from backend.database import Database

router = APIRouter(prefix="/api", tags=["reports"])

@router.get("/datasets/{dataset_id}/report")
def get_report(dataset_id: str, format: str = "json"):
    """Get quality report for dataset."""
    try:
        result = Database.get_latest_quality_result(dataset_id)
        if not result:
            raise HTTPException(status_code=404, detail="No analysis results found")

        # Parse JSON fields
        parsed_result = {
            "overall_quality_score": result["overall_quality_score"],
            "schema_validation": json.loads(result["schema_validation"]),
            "drift_analysis": json.loads(result["drift_analysis"]),
            "anomaly_detection": json.loads(result["anomaly_detection"]),
            "completeness": json.loads(result["completeness"]),
        }

        # Get alert summary
        alerts = Database.list_alerts(dataset_id)
        alert_summary = {
            "critical_count": len([a for a in alerts if a["severity"] == "CRITICAL"]),
            "warning_count": len([a for a in alerts if a["severity"] == "WARNING"]),
            "info_count": len([a for a in alerts if a["severity"] == "INFO"]),
            "total_count": len(alerts)
        }

        if format == "json":
            return ReportGenerator.generate_json_report(dataset_id, parsed_result, alert_summary)
        elif format == "text":
            return {
                "format": "text",
                "content": ReportGenerator.generate_text_report(dataset_id, parsed_result, alert_summary)
            }
        else:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'text'")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/datasets/{dataset_id}/report/export")
def export_report(dataset_id: str, format: str = "json"):
    """Export report to file."""
    try:
        result = Database.get_latest_quality_result(dataset_id)
        if not result:
            raise HTTPException(status_code=404, detail="No analysis results found")

        # Parse JSON fields
        parsed_result = {
            "overall_quality_score": result["overall_quality_score"],
            "schema_validation": json.loads(result["schema_validation"]),
            "drift_analysis": json.loads(result["drift_analysis"]),
            "anomaly_detection": json.loads(result["anomaly_detection"]),
            "completeness": json.loads(result["completeness"]),
        }

        # Get alert summary
        alerts = Database.list_alerts(dataset_id)
        alert_summary = {
            "critical_count": len([a for a in alerts if a["severity"] == "CRITICAL"]),
            "warning_count": len([a for a in alerts if a["severity"] == "WARNING"]),
            "info_count": len([a for a in alerts if a["severity"] == "INFO"]),
        }

        filename = ReportGenerator.export_report(dataset_id, parsed_result, format, alert_summary)

        return {
            "filename": filename,
            "format": format,
            "message": "Report exported successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
