import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
from backend.models import SchemaChange, AlertSeverity

class SchemaValidator:
    @staticmethod
    def extract_schema(df: pd.DataFrame) -> Dict[str, str]:
        """Extract schema from dataframe."""
        schema = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema[col] = dtype
        return schema

    @staticmethod
    def extract_schema_detailed(df: pd.DataFrame) -> Dict[str, Dict]:
        """Extract detailed schema with nullability."""
        schema = {}
        for col in df.columns:
            schema[col] = {
                "dtype": str(df[col].dtype),
                "nullable": df[col].isna().any(),
                "null_count": int(df[col].isna().sum())
            }
        return schema

    @staticmethod
    def compare_schemas(baseline_schema: Dict[str, str],
                       current_schema: Dict[str, str]) -> Tuple[List[SchemaChange], bool]:
        """Compare baseline and current schemas."""
        changes = []
        is_breaking = False

        baseline_cols = set(baseline_schema.keys())
        current_cols = set(current_schema.keys())

        # Detect missing columns
        missing_cols = baseline_cols - current_cols
        for col in missing_cols:
            changes.append(SchemaChange(
                change_type="MISSING_COLUMN",
                column=col,
                old_value=baseline_schema[col],
                new_value=None,
                severity=AlertSeverity.CRITICAL
            ))
            is_breaking = True

        # Detect new columns
        new_cols = current_cols - baseline_cols
        for col in new_cols:
            changes.append(SchemaChange(
                change_type="NEW_COLUMN",
                column=col,
                old_value=None,
                new_value=current_schema[col],
                severity=AlertSeverity.INFO
            ))

        # Detect type changes
        for col in baseline_cols & current_cols:
            if baseline_schema[col] != current_schema[col]:
                severity = AlertSeverity.WARNING
                if baseline_schema[col].startswith('int') and not current_schema[col].startswith('int'):
                    severity = AlertSeverity.CRITICAL
                    is_breaking = True

                changes.append(SchemaChange(
                    change_type="TYPE_CHANGE",
                    column=col,
                    old_value=baseline_schema[col],
                    new_value=current_schema[col],
                    severity=severity
                ))

        return changes, is_breaking

    @staticmethod
    def schema_change_severity(old_schema: Dict, new_schema: Dict) -> float:
        """Score schema change severity (0-1)."""
        changes, is_breaking = SchemaValidator.compare_schemas(old_schema, new_schema)

        if not changes:
            return 0.0

        if is_breaking:
            return 1.0

        # Count warnings
        warning_count = sum(1 for c in changes if c.severity == AlertSeverity.WARNING)
        info_count = sum(1 for c in changes if c.severity == AlertSeverity.INFO)

        severity = (warning_count * 0.3 + info_count * 0.05) / (len(changes) or 1)
        return min(1.0, severity)

    @staticmethod
    def validate_schema(new_df: pd.DataFrame,
                       baseline_schema: Dict[str, str]) -> Dict:
        """Validate new dataframe against baseline schema."""
        current_schema = SchemaValidator.extract_schema(new_df)
        changes, is_breaking = SchemaValidator.compare_schemas(baseline_schema, current_schema)

        return {
            "is_breaking": is_breaking,
            "changes": [
                {
                    "type": c.change_type,
                    "column": c.column,
                    "old": c.old_value,
                    "new": c.new_value,
                    "severity": c.severity.value
                }
                for c in changes
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "change_count": len(changes)
        }
