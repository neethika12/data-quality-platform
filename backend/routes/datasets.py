from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
import uuid
import os
from backend.models import DatasetResponse
from backend.database import Database
from backend.utils.file_handlers import FileHandler
from backend.services.schema_validator import SchemaValidator
from backend.utils.stats import StatisticalTester
from backend.config import settings

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a CSV or Parquet file."""
    try:
        # Generate dataset ID
        dataset_id = str(uuid.uuid4())

        # Save uploaded file
        file_path = os.path.join(settings.UPLOAD_DIR, f"{dataset_id}_{file.filename}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Validate file
        is_valid, message = FileHandler.validate_file(file_path)
        if not is_valid:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=message)

        # Read file
        df = FileHandler.read_file(file_path)

        # Establish the baseline immediately: schema + a raw data sample for drift comparison later
        baseline_schema = SchemaValidator.extract_schema(df)
        baseline_stats = {col: StatisticalTester.calculate_distribution_stats(df[col]) for col in df.columns}
        baseline_data = FileHandler.dataframe_to_baseline_sample(df)

        # Store dataset info
        Database.store_dataset(
            dataset_id, file.filename, f"Uploaded dataset",
            len(df), len(df.columns), baseline_schema, baseline_stats, baseline_data
        )

        return {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "file_path": file_path,
            "message": "Dataset uploaded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/upload-version")
async def upload_new_version(dataset_id: str, file: UploadFile = File(...)):
    """Upload a new snapshot of data for an existing dataset, keeping the original baseline
    so the next check can measure real drift/changes against it."""
    dataset = Database.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        # Remove the old file(s) for this dataset
        old_files = [f for f in os.listdir(settings.UPLOAD_DIR) if f.startswith(f"{dataset_id}_")]
        for f in old_files:
            os.remove(os.path.join(settings.UPLOAD_DIR, f))

        # Save the new file under the same dataset_id
        file_path = os.path.join(settings.UPLOAD_DIR, f"{dataset_id}_{file.filename}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        is_valid, message = FileHandler.validate_file(file_path)
        if not is_valid:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=message)

        df = FileHandler.read_file(file_path)

        # Update row/column counts only — baseline stays as the original reference point
        Database.update_dataset_file_info(dataset_id, len(df), len(df.columns))

        return {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "row_count": len(df),
            "column_count": len(df.columns),
            "message": "New data uploaded. Run a check to compare it against the original baseline."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_id}")
def get_dataset(dataset_id: str):
    """Get dataset information."""
    dataset = Database.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return {
        "id": dataset["id"],
        "name": dataset["name"],
        "description": dataset["description"],
        "row_count": dataset["row_count"],
        "column_count": dataset["column_count"],
        "created_at": dataset["created_at"],
        "last_analyzed": dataset["last_analyzed"]
    }

@router.get("")
def list_datasets(limit: int = 50):
    """List all datasets."""
    datasets = Database.list_datasets()
    return {
        "count": len(datasets),
        "datasets": datasets[:limit]
    }

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str):
    """Delete a dataset."""
    dataset = Database.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Clean up file
    files = [f for f in os.listdir(settings.UPLOAD_DIR) if dataset_id in f]
    for f in files:
        os.remove(os.path.join(settings.UPLOAD_DIR, f))

    # Remove the dataset and its history from the database
    Database.delete_dataset(dataset_id)

    return {"message": f"Dataset {dataset_id} deleted"}
