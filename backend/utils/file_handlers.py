import pandas as pd
import os
from typing import Optional
from backend.config import settings

class FileHandler:
    ALLOWED_EXTENSIONS = {'.csv', '.parquet', '.xlsx', '.xls'}
    MAX_FILE_SIZE_MB = 500

    @staticmethod
    def validate_file(file_path: str) -> tuple[bool, str]:
        """Validate file exists and is allowed format."""
        if not os.path.exists(file_path):
            return False, "File not found"

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in FileHandler.ALLOWED_EXTENSIONS:
            return False, f"File type {ext} not supported. Use: {', '.join(FileHandler.ALLOWED_EXTENSIONS)}"

        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > FileHandler.MAX_FILE_SIZE_MB:
            return False, f"File too large ({size_mb:.1f}MB > {FileHandler.MAX_FILE_SIZE_MB}MB)"

        return True, "Valid"

    @staticmethod
    def read_file(file_path: str, sample_rows: Optional[int] = None) -> pd.DataFrame:
        """Read CSV, Parquet, or Excel file."""
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext == '.parquet':
                df = pd.read_parquet(file_path)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {ext}")

            if sample_rows and len(df) > sample_rows:
                df = df.head(sample_rows)

            return df

        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")

    @staticmethod
    def save_file(df: pd.DataFrame, file_path: str, format: str = 'csv') -> str:
        """Save dataframe to file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            if format == 'csv':
                df.to_csv(file_path, index=False)
            elif format == 'parquet':
                df.to_parquet(file_path, index=False)
            elif format == 'json':
                df.to_json(file_path, orient='records', indent=2)

            return file_path

        except Exception as e:
            raise Exception(f"Error saving file: {str(e)}")

    @staticmethod
    def get_sample_data_path() -> str:
        """Get path to sample dataset."""
        return os.path.join(os.path.dirname(__file__), "../data/sample_data.csv")

    @staticmethod
    def dataframe_to_baseline_sample(df: pd.DataFrame, max_rows: int = 5000) -> dict:
        """Convert a dataframe to a JSON-safe, column-oriented sample for storing as a drift baseline."""
        sample = df.head(max_rows)
        safe = {}
        for col in sample.columns:
            series = sample[col]
            if pd.api.types.is_datetime64_any_dtype(series):
                values = series.astype(str).tolist()
            else:
                values = series.tolist()
            # Replace NaN/NaT and numpy scalar types with plain JSON-safe values
            safe[col] = [
                None if (v is None or (isinstance(v, float) and pd.isna(v))) else
                (v.item() if hasattr(v, "item") else v)
                for v in values
            ]
        return safe
