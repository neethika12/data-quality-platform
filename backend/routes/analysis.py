from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
from backend.services.quality_checker import QualityChecker
from backend.database import Database
from backend.utils.file_handlers import FileHandler
import os

router = APIRouter(prefix="/api", tags=["analysis"])

@router.post("/datasets/{dataset_id}/analyze")
def analyze_dataset(dataset_id: str, last_update_timestamp: Optional[str] = None):
    """Run quality analysis on a dataset."""
    try:
        # Get dataset
        dataset = Database.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Find dataset file
        from backend.config import settings
        file_matches = [f for f in os.listdir(settings.UPLOAD_DIR) if dataset_id in f]
        if not file_matches:
            raise HTTPException(status_code=404, detail="Dataset file not found")

        file_path = os.path.join(settings.UPLOAD_DIR, file_matches[0])

        # Read dataset
        df = FileHandler.read_file(file_path)

        # Parse timestamp if provided
        ts = None
        if last_update_timestamp:
            try:
                ts = datetime.fromisoformat(last_update_timestamp)
            except:
                ts = None

        # Run quality check
        checker = QualityChecker()
        result = checker.run_full_check(dataset_id, df, ts)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/datasets/{dataset_id}/re-analyze")
def reanalyze_dataset(dataset_id: str):
    """Re-analyze dataset with updated thresholds."""
    return analyze_dataset(dataset_id)
