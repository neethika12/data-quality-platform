from fastapi import APIRouter, File, UploadFile, HTTPException
import os
import uuid
from datetime import datetime
from backend.utils.file_handlers import FileHandler
from backend.services.schema_validator import SchemaValidator
from backend.services.drift_detector import DriftDetector
from backend.services.anomaly_detector import AnomalyDetector
from backend.config import settings

router = APIRouter(prefix="/api/compare", tags=["comparison"])


async def _save_temp(file: UploadFile) -> str:
    tmp_dir = os.path.join(settings.UPLOAD_DIR, "compare_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, f"{uuid.uuid4()}_{file.filename}")
    with open(path, "wb") as f:
        f.write(await file.read())
    return path


@router.post("")
async def compare_two_files(file_a: UploadFile = File(...), file_b: UploadFile = File(...)):
    """Directly compare two independent files against each other — no persisted baseline,
    no tracked dataset. File A is treated as the reference, File B as what's being checked."""
    path_a = path_b = None
    try:
        path_a = await _save_temp(file_a)
        path_b = await _save_temp(file_b)

        is_valid, message = FileHandler.validate_file(path_a)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"File A: {message}")
        is_valid, message = FileHandler.validate_file(path_b)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"File B: {message}")

        df_a = FileHandler.read_file(path_a)
        df_b = FileHandler.read_file(path_b)

        # Schema diff: A's schema is the reference, B is checked against it
        schema_a = SchemaValidator.extract_schema(df_a)
        schema_result = SchemaValidator.validate_schema(df_b, schema_a)

        # Real statistical drift: fit on A, detect drift in B
        drift_detector = DriftDetector()
        drift_detector.fit_baseline(df_a)
        drift_result = drift_detector.detect_drift(df_b)

        # Anomalies in B (missing values / outliers), for context
        anomaly_detector = AnomalyDetector()
        anomaly_result = anomaly_detector.detect_anomalies(df_b)

        # Simple row-count comparison
        row_diff = len(df_b) - len(df_a)
        row_diff_percent = (row_diff / len(df_a) * 100) if len(df_a) > 0 else 0.0

        schema_score = 1.0 if not schema_result.get("changes") else 0.8
        drift_score = 1.0 - drift_result.get("overall_drift_score", 0.0)
        anomaly_score = 1.0 - anomaly_result.get("anomaly_score", 0.0)
        overall_score = float(min(1.0, max(0.0,
            schema_score * 0.3 + drift_score * 0.4 + anomaly_score * 0.3
        )))

        return {
            "overall_similarity_score": overall_score,
            "file_a": {"filename": file_a.filename, "row_count": len(df_a), "column_count": len(df_a.columns)},
            "file_b": {"filename": file_b.filename, "row_count": len(df_b), "column_count": len(df_b.columns)},
            "schema_validation": schema_result,
            "drift_analysis": drift_result,
            "anomaly_detection": anomaly_result,
            "row_count_diff": row_diff,
            "row_count_diff_percent": row_diff_percent,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in (path_a, path_b):
            if p and os.path.exists(p):
                os.remove(p)
