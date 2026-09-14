from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
import uuid
import os
import shutil
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

VERSIONS_DIR = os.path.join(settings.UPLOAD_DIR, "versions")


@router.post("/{dataset_id}/versions")
async def upload_dataset_version(dataset_id: str, file: UploadFile = File(...)):
    """Upload another snapshot of data for an existing dataset. Every version is kept
    (not replaced) so several files can each be checked against the same fixed baseline."""
    dataset = Database.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        os.makedirs(VERSIONS_DIR, exist_ok=True)
        version_id = str(uuid.uuid4())
        file_path = os.path.join(VERSIONS_DIR, f"{version_id}_{file.filename}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        is_valid, message = FileHandler.validate_file(file_path)
        if not is_valid:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=message)

        df = FileHandler.read_file(file_path)

        Database.add_dataset_version(version_id, dataset_id, file.filename, file_path, len(df), len(df.columns))
        # Keep a lightweight "most recent version" pointer on the dataset for convenience/default selection
        Database.update_current_file(dataset_id, file.filename, len(df), len(df.columns))

        return {
            "version_id": version_id,
            "dataset_id": dataset_id,
            "filename": file.filename,
            "row_count": len(df),
            "column_count": len(df.columns),
            "message": "New version uploaded. Run a check to compare it against the baseline."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Kept for backward compatibility with older clients — same behavior as /versions
@router.post("/{dataset_id}/upload-version")
async def upload_new_version_legacy(dataset_id: str, file: UploadFile = File(...)):
    return await upload_dataset_version(dataset_id, file)


@router.get("/{dataset_id}/versions")
def list_dataset_versions(dataset_id: str):
    """List every version uploaded for this dataset (most recent first)."""
    dataset = Database.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    versions = Database.list_dataset_versions(dataset_id)
    return {"count": len(versions), "versions": versions}


@router.delete("/{dataset_id}/versions/{version_id}")
def delete_dataset_version(dataset_id: str, version_id: str):
    """Delete a single uploaded version (not the baseline)."""
    version = Database.get_dataset_version(version_id)
    if not version or version["dataset_id"] != dataset_id:
        raise HTTPException(status_code=404, detail="Version not found")

    if os.path.exists(version["file_path"]):
        os.remove(version["file_path"])
    Database.delete_dataset_version(version_id)

    return {"message": f"Version {version_id} deleted"}


@router.post("/{dataset_id}/versions/{version_id}/promote")
def promote_version_to_baseline(dataset_id: str, version_id: str):
    """Make an uploaded version the new baseline. The old baseline is archived into
    this dataset's baseline history (never shared with other datasets/projects) so
    it's never lost, and every future check compares against the new baseline."""
    dataset = Database.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    version = Database.get_dataset_version(version_id)
    if not version or version["dataset_id"] != dataset_id:
        raise HTTPException(status_code=404, detail="Version not found")

    try:
        df = FileHandler.read_file(version["file_path"])
        new_baseline_schema = SchemaValidator.extract_schema(df)
        new_baseline_stats = {col: StatisticalTester.calculate_distribution_stats(df[col]) for col in df.columns}
        new_baseline_data = FileHandler.dataframe_to_baseline_sample(df)

        Database.promote_version_to_baseline(
            dataset_id, new_baseline_schema, new_baseline_stats, new_baseline_data,
            version["filename"], len(df), len(df.columns)
        )

        # Swap the physical baseline file so a plain "check baseline against itself" still works
        old_baseline_files = [f for f in os.listdir(settings.UPLOAD_DIR)
                             if f.startswith(f"{dataset_id}_") and os.path.isfile(os.path.join(settings.UPLOAD_DIR, f))]
        for f in old_baseline_files:
            os.remove(os.path.join(settings.UPLOAD_DIR, f))
        new_baseline_path = os.path.join(settings.UPLOAD_DIR, f"{dataset_id}_{version['filename']}")
        shutil.copy(version["file_path"], new_baseline_path)

        # The promoted version is now the baseline, not something to check against it anymore
        Database.delete_dataset_version(version_id)

        return {
            "dataset_id": dataset_id,
            "new_baseline_filename": version["filename"],
            "message": "Baseline updated. The old baseline was archived to this project's baseline history."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}/baseline-history")
def get_baseline_history(dataset_id: str):
    """List every baseline this dataset has ever had (most recently replaced first).
    Scoped strictly to this one dataset — never mixed with any other project's history."""
    dataset = Database.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    history = Database.list_baseline_history(dataset_id)
    return {"count": len(history), "history": history}

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
        "last_analyzed": dataset["last_analyzed"],
        "baseline_filename": dataset["baseline_filename"],
        "baseline_established_at": dataset["baseline_established_at"],
        "current_filename": dataset["current_filename"],
        "current_file_uploaded_at": dataset["current_file_uploaded_at"],
        "has_new_version": dataset["current_filename"] != dataset["baseline_filename"]
    }

@router.get("")
def list_datasets(limit: int = 50):
    """List all datasets."""
    datasets = Database.list_datasets()[:limit]
    for d in datasets:
        d["has_new_version"] = d.get("current_filename") != d.get("baseline_filename")
    return {
        "count": len(datasets),
        "datasets": datasets
    }

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str):
    """Delete a dataset."""
    dataset = Database.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Clean up the baseline file
    files = [f for f in os.listdir(settings.UPLOAD_DIR) if dataset_id in f]
    for f in files:
        path = os.path.join(settings.UPLOAD_DIR, f)
        if os.path.isfile(path):
            os.remove(path)

    # Clean up every uploaded version's file
    for version in Database.list_dataset_versions(dataset_id):
        if os.path.exists(version["file_path"]):
            os.remove(version["file_path"])

    # Remove the dataset and its history from the database
    Database.delete_dataset(dataset_id)

    return {"message": f"Dataset {dataset_id} deleted"}
