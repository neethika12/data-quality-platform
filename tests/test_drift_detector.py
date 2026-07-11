import pytest
import pandas as pd
import numpy as np
from backend.services.drift_detector import DriftDetector

@pytest.fixture
def baseline_df():
    np.random.seed(42)
    return pd.DataFrame({
        'age': np.random.normal(30, 10, 1000),
        'income': np.random.normal(50000, 15000, 1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000)
    })

@pytest.fixture
def no_drift_df(baseline_df):
    return baseline_df.copy()

@pytest.fixture
def drift_df(baseline_df):
    np.random.seed(43)
    return pd.DataFrame({
        'age': np.random.normal(50, 10, 1000),  # Different mean
        'income': np.random.normal(50000, 15000, 1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000)
    })

def test_drift_detector_fit_baseline(baseline_df):
    detector = DriftDetector()
    detector.fit_baseline(baseline_df)
    assert detector.baseline_stats is not None
    assert len(detector.baseline_stats) == 3

def test_no_drift_detection(baseline_df, no_drift_df):
    detector = DriftDetector()
    detector.fit_baseline(baseline_df)
    result = detector.detect_drift(no_drift_df)

    assert result["overall_drift_score"] < 0.3
    assert result["severity_level"] == "INFO"

def test_drift_detection(baseline_df, drift_df):
    detector = DriftDetector()
    detector.fit_baseline(baseline_df)
    result = detector.detect_drift(drift_df)

    assert result["overall_drift_score"] > 0.0
    assert len(result["drifted_features"]) > 0

def test_drift_score_range(baseline_df):
    detector = DriftDetector()
    detector.fit_baseline(baseline_df)

    # Create data with known drift
    np.random.seed(100)
    test_df = pd.DataFrame({
        'age': np.random.normal(80, 10, 1000),  # Very different
        'income': np.random.normal(50000, 15000, 1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000)
    })

    result = detector.detect_drift(test_df)
    assert 0 <= result["overall_drift_score"] <= 1.0

def test_drift_severity_classification(baseline_df):
    detector = DriftDetector()
    detector.fit_baseline(baseline_df)

    np.random.seed(101)
    extreme_drift = pd.DataFrame({
        'age': np.random.normal(100, 5, 1000),
        'income': np.random.normal(100000, 30000, 1000),
        'category': np.random.choice(['D', 'E', 'F'], 1000)  # Different categories
    })

    result = detector.detect_drift(extreme_drift)
    assert result["severity_level"] in ["INFO", "WARNING", "CRITICAL"]
