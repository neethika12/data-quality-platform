from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./data_quality.db"
    DB_PATH: str = "./data_quality.db"

    # File storage
    UPLOAD_DIR: str = "./uploads"

    # Thresholds (defaults)
    DRIFT_WARNING_THRESHOLD: float = 0.3
    DRIFT_CRITICAL_THRESHOLD: float = 0.7
    NULL_RATE_WARNING: float = 0.05
    NULL_RATE_CRITICAL: float = 0.10
    FRESHNESS_WARNING_HOURS: int = 24
    FRESHNESS_CRITICAL_HOURS: int = 48
    RECORD_DROP_WARNING_PERCENT: float = 0.10

    # API
    API_TITLE: str = "Data Quality Monitoring Platform"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Performance
    SAMPLE_SIZE_FOR_STATS: int = 10000

    class Config:
        env_file = ".env"

settings = Settings()

# Create upload directory if not exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
