from fastapi import APIRouter, HTTPException
from typing import Optional
import json
from backend.database import Database

router = APIRouter(prefix="/api", tags=["results"])

@router.get("/results/{result_id}")
def get_result(result_id: str):
    """Get quality check result by ID."""
    result = Database.get_quality_result(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    # Parse JSON fields
    return {
        "id": result["id"],
        "dataset_id": result["dataset_id"],
        "schema_validation": json.loads(result["schema_validation"]),
        "drift_analysis": json.loads(result["drift_analysis"]),
        "anomaly_detection": json.loads(result["anomaly_detection"]),
        "completeness": json.loads(result["completeness"]),
        "overall_quality_score": result["overall_quality_score"],
        "created_at": result["created_at"]
    }

@router.get("/datasets/{dataset_id}/latest-result")
def get_latest_result(dataset_id: str, version_id: Optional[str] = None):
    """Get latest quality result for dataset. Pass version_id to get the result for a
    specific uploaded version; omit it to get the baseline-against-itself result."""
    result = Database.get_latest_quality_result(dataset_id, version_id=version_id)
    if not result:
        raise HTTPException(status_code=404, detail="No results found for dataset")

    # Parse JSON fields
    return {
        "id": result["id"],
        "dataset_id": result["dataset_id"],
        "version_id": result["version_id"],
        "schema_validation": json.loads(result["schema_validation"]),
        "drift_analysis": json.loads(result["drift_analysis"]),
        "anomaly_detection": json.loads(result["anomaly_detection"]),
        "completeness": json.loads(result["completeness"]),
        "overall_quality_score": result["overall_quality_score"],
        "created_at": result["created_at"]
    }

@router.get("/datasets/{dataset_id}/metric-history")
def get_metric_history(dataset_id: str, metric_type: Optional[str] = None,
                       column_name: Optional[str] = None, limit: int = 100):
    """Get historical metric data for trend analysis."""
    metrics = Database.get_metric_history(dataset_id, metric_type or "quality_score",
                                          column_name, limit)

    return {
        "dataset_id": dataset_id,
        "metric_type": metric_type or "quality_score",
        "count": len(metrics),
        "metrics": metrics
    }
