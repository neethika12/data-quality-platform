import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from backend.config import settings

def init_db():
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()

    # Datasets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            row_count INTEGER,
            column_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_analyzed TIMESTAMP,
            baseline_schema TEXT,
            baseline_stats TEXT,
            baseline_data TEXT,
            baseline_filename TEXT,
            current_filename TEXT,
            current_file_uploaded_at TIMESTAMP
        )
    """)

    # Migration: add columns to pre-existing databases that predate them
    cursor.execute("PRAGMA table_info(datasets)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    for col, coltype in [
        ("baseline_data", "TEXT"),
        ("baseline_filename", "TEXT"),
        ("current_filename", "TEXT"),
        ("current_file_uploaded_at", "TIMESTAMP"),
    ]:
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE datasets ADD COLUMN {col} {coltype}")

    # Quality results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_results (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            schema_validation TEXT,
            drift_analysis TEXT,
            anomaly_detection TEXT,
            completeness TEXT,
            overall_quality_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
    """)

    # Alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            metric_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT,
            value REAL,
            threshold REAL,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            acknowledged_at TIMESTAMP,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
    """)

    # Schema history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_history (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            schema_version INTEGER,
            schema_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
    """)

    # Metrics history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics_history (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL,
            metric_type TEXT,
            column_name TEXT,
            value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
    """)

    conn.commit()
    conn.close()

class Database:
    @staticmethod
    def get_connection():
        conn = sqlite3.connect(settings.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def store_dataset(dataset_id: str, name: str, description: str,
                     row_count: int, column_count: int, baseline_schema: Dict, baseline_stats: Dict,
                     baseline_data: Optional[Dict] = None, baseline_filename: Optional[str] = None):
        conn = Database.get_connection()
        cursor = conn.cursor()
        filename = baseline_filename or name
        cursor.execute("""
            INSERT OR REPLACE INTO datasets
            (id, name, description, row_count, column_count, baseline_schema, baseline_stats, baseline_data,
             baseline_filename, current_filename, current_file_uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dataset_id, name, description, row_count, column_count,
              json.dumps(baseline_schema), json.dumps(baseline_stats), json.dumps(baseline_data or {}),
              filename, filename, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()

    @staticmethod
    def update_current_file(dataset_id: str, filename: str, row_count: int, column_count: int):
        """Record that a new 'current' file version was uploaded for this dataset, without touching the baseline."""
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE datasets SET current_filename = ?, current_file_uploaded_at = ?,
                                row_count = ?, column_count = ?
            WHERE id = ?
        """, (filename, datetime.utcnow().isoformat(), row_count, column_count, dataset_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_dataset(dataset_id: str):
        """Delete a dataset row and everything associated with it."""
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quality_results WHERE dataset_id = ?", (dataset_id,))
        cursor.execute("DELETE FROM alerts WHERE dataset_id = ?", (dataset_id,))
        cursor.execute("DELETE FROM schema_history WHERE dataset_id = ?", (dataset_id,))
        cursor.execute("DELETE FROM metrics_history WHERE dataset_id = ?", (dataset_id,))
        cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        conn.commit()
        conn.close()


    @staticmethod
    def get_dataset(dataset_id: str) -> Optional[Dict]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    @staticmethod
    def list_datasets() -> List[Dict]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def update_dataset_analyzed(dataset_id: str):
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE datasets SET last_analyzed = ? WHERE id = ?
        """, (datetime.utcnow().isoformat(), dataset_id))
        conn.commit()
        conn.close()

    @staticmethod
    def store_quality_result(result_id: str, dataset_id: str, schema_validation: Dict,
                            drift_analysis: Dict, anomaly_detection: Dict,
                            completeness: Dict, overall_score: float):
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quality_results
            (id, dataset_id, schema_validation, drift_analysis, anomaly_detection, completeness, overall_quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (result_id, dataset_id, json.dumps(schema_validation), json.dumps(drift_analysis),
              json.dumps(anomaly_detection), json.dumps(completeness), overall_score))
        conn.commit()
        conn.close()

    @staticmethod
    def get_quality_result(result_id: str) -> Optional[Dict]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quality_results WHERE id = ?", (result_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    @staticmethod
    def get_latest_quality_result(dataset_id: str) -> Optional[Dict]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM quality_results WHERE dataset_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (dataset_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    @staticmethod
    def store_alert(alert_id: str, dataset_id: str, metric_type: str, severity: str,
                   message: str, value: float, threshold: float):
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts
            (id, dataset_id, metric_type, severity, message, value, threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (alert_id, dataset_id, metric_type, severity, message, value, threshold))
        conn.commit()
        conn.close()

    @staticmethod
    def get_alert(alert_id: str) -> Optional[Dict]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    @staticmethod
    def list_alerts(dataset_id: Optional[str] = None, severity: Optional[str] = None) -> List[Dict]:
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM alerts WHERE 1=1"
        params = []

        if dataset_id:
            query += " AND dataset_id = ?"
            params.append(dataset_id)
        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def acknowledge_alert(alert_id: str):
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts SET status = 'ACKNOWLEDGED', acknowledged_at = ? WHERE id = ?
        """, (datetime.utcnow().isoformat(), alert_id))
        conn.commit()
        conn.close()

    @staticmethod
    def store_metric_history(metric_id: str, dataset_id: str, metric_type: str,
                            column_name: Optional[str], value: float):
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metrics_history
            (id, dataset_id, metric_type, column_name, value)
            VALUES (?, ?, ?, ?, ?)
        """, (metric_id, dataset_id, metric_type, column_name, value))
        conn.commit()
        conn.close()

    @staticmethod
    def get_metric_history(dataset_id: str, metric_type: str,
                          column_name: Optional[str] = None, limit: int = 100) -> List[Dict]:
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM metrics_history WHERE dataset_id = ? AND metric_type = ?"
        params = [dataset_id, metric_type]

        if column_name:
            query += " AND column_name = ?"
            params.append(column_name)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
