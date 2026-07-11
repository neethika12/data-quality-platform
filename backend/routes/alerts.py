from fastapi import APIRouter, HTTPException
from typing import Optional
from backend.database import Database

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("")
def list_alerts(dataset_id: Optional[str] = None, severity: Optional[str] = None,
                limit: int = 100):
    """Get all alerts with optional filtering."""
    alerts = Database.list_alerts(dataset_id, severity)
    return {
        "count": len(alerts),
        "alerts": alerts[:limit]
    }

@router.get("/{alert_id}")
def get_alert(alert_id: str):
    """Get alert details by ID."""
    alert = Database.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return dict(alert)

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    """Mark alert as acknowledged."""
    alert = Database.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    Database.acknowledge_alert(alert_id)

    return {
        "alert_id": alert_id,
        "status": "ACKNOWLEDGED",
        "message": "Alert acknowledged"
    }

@router.get("/dataset/{dataset_id}/summary")
def get_alert_summary(dataset_id: str):
    """Get alert summary for dataset."""
    alerts = Database.list_alerts(dataset_id)

    critical = [a for a in alerts if a["severity"] == "CRITICAL"]
    warning = [a for a in alerts if a["severity"] == "WARNING"]
    info = [a for a in alerts if a["severity"] == "INFO"]

    return {
        "dataset_id": dataset_id,
        "critical_count": len(critical),
        "warning_count": len(warning),
        "info_count": len(info),
        "total_count": len(alerts),
        "recent_critical": critical[:5],
        "recent_warning": warning[:5]
    }
