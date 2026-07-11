from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import json
import csv
import os
from datetime import datetime
from backend.database import Database
from backend.config import settings

router = APIRouter(prefix="/api", tags=["export"])

@router.get("/datasets/{dataset_id}/export")
def export_quality_results(dataset_id: str, format: str = "json"):
    """Export quality check results."""
    result = Database.get_latest_quality_result(dataset_id)
    if not result:
        raise HTTPException(status_code=404, detail="No results found for dataset")

    dataset = Database.get_dataset(dataset_id)

    if format == "json":
        return export_as_json(result, dataset)
    elif format == "csv":
        return export_as_csv(result, dataset)
    else:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")

def export_as_json(result, dataset):
    """Export as JSON."""
    export_data = {
        "dataset": {
            "id": dataset["id"],
            "name": dataset["name"],
            "row_count": dataset["row_count"],
            "column_count": dataset["column_count"]
        },
        "quality_check": {
            "timestamp": result["created_at"],
            "overall_quality_score": result["overall_quality_score"],
            "schema_validation": json.loads(result["schema_validation"]),
            "drift_analysis": json.loads(result["drift_analysis"]),
            "anomaly_detection": json.loads(result["anomaly_detection"]),
            "completeness": json.loads(result["completeness"])
        }
    }

    return export_data

def export_as_csv(result, dataset):
    """Export as CSV."""
    # Create CSV in memory
    export_path = os.path.join(settings.UPLOAD_DIR, f"export_{dataset['id']}.csv")

    with open(export_path, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(["Dataset Report", ""])
        writer.writerow([""])

        # Dataset Info
        writer.writerow(["Dataset Name", dataset["name"]])
        writer.writerow(["Dataset ID", dataset["id"]])
        writer.writerow(["Row Count", dataset["row_count"]])
        writer.writerow(["Column Count", dataset["column_count"]])
        writer.writerow([""])

        # Quality Score
        writer.writerow(["Quality Metrics", ""])
        writer.writerow(["Overall Quality Score", result["overall_quality_score"]])
        writer.writerow(["Analysis Time", result["created_at"]])
        writer.writerow([""])

        # Alerts
        alerts = Database.list_alerts(dataset["id"])
        writer.writerow(["Alerts Summary", ""])
        critical = len([a for a in alerts if a["severity"] == "CRITICAL"])
        warning = len([a for a in alerts if a["severity"] == "WARNING"])
        writer.writerow(["Critical Alerts", critical])
        writer.writerow(["Warning Alerts", warning])

    return {"file_path": export_path, "format": "csv"}

@router.get("/health")
def health_check():
    """System health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
