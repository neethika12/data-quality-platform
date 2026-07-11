from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

# Dataset Models
class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None

class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    row_count: int
    column_count: int
    created_at: datetime
    last_analyzed: Optional[datetime]

    class Config:
        from_attributes = True

# Schema Models
class SchemaChange(BaseModel):
    change_type: str  # NEW_COLUMN, MISSING_COLUMN, TYPE_CHANGE, NULLABILITY_CHANGE
    column: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    severity: AlertSeverity

class SchemaValidationResult(BaseModel):
    is_breaking: bool
    changes: List[SchemaChange]
    timestamp: datetime

# Drift Models
class DriftFeature(BaseModel):
    feature: str
    drift_score: float = Field(ge=0.0, le=1.0)
    p_value: float
    test_method: str
    interpretation: str

class DriftAnalysisResult(BaseModel):
    drifted_features: List[DriftFeature]
    overall_drift_score: float
    severity_level: AlertSeverity
    timestamp: datetime

# Anomaly Models
class NullAnalysis(BaseModel):
    column: str
    null_count: int
    null_rate: float
    status: str

class OutlierAnalysis(BaseModel):
    column: str
    outlier_count: int
    method: str
    indices: List[int]

class AnomalyDetectionResult(BaseModel):
    null_analysis: Dict[str, NullAnalysis]
    outliers: Dict[str, OutlierAnalysis]
    domain_violations: Dict[str, Any]
    total_anomalies: int
    anomaly_score: float
    timestamp: datetime

# Completeness Models
class CompletenessResult(BaseModel):
    completeness_score: float
    record_count: int
    expected_records: Optional[int]
    freshness_hours: Optional[float]
    freshness_status: str
    timestamp: datetime

# Quality Check Result
class QualityCheckResult(BaseModel):
    dataset_id: str
    schema_validation: SchemaValidationResult
    drift_analysis: DriftAnalysisResult
    anomaly_detection: AnomalyDetectionResult
    completeness: CompletenessResult
    overall_quality_score: float
    timestamp: datetime

# Alert Models
class Alert(BaseModel):
    id: Optional[str] = None
    dataset_id: str
    metric_type: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AlertResponse(Alert):
    pass

# Configuration Models
class ThresholdConfig(BaseModel):
    drift_warning: float = Field(ge=0.0, le=1.0)
    drift_critical: float = Field(ge=0.0, le=1.0)
    null_rate_warning: float = Field(ge=0.0, le=1.0)
    null_rate_critical: float = Field(ge=0.0, le=1.0)
    freshness_warning_hours: int
    freshness_critical_hours: int
    record_drop_warning_percent: float

class DomainRule(BaseModel):
    name: str
    column: str
    rule_type: str  # negative_values, future_dates, invalid_format
    description: Optional[str] = None
    enabled: bool = True

# Export Models
class ExportRequest(BaseModel):
    format: str = Field(pattern="^(json|csv)$")
    include_details: bool = True

class ExportResponse(BaseModel):
    filename: str
    format: str
    size_bytes: int
    created_at: datetime
