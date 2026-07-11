import pytest
import pandas as pd
import numpy as np
from backend.services.anomaly_detector import AnomalyDetector

@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        'age': [25, 30, 35, 40, 45, 50, 55, 60, 65, 70] * 10,
        'price': np.random.normal(100, 20, 100),
        'category': np.random.choice(['A', 'B', 'C'], 100),
        'is_active': [True, False] * 50
    })

@pytest.fixture
def df_with_nulls():
    return pd.DataFrame({
        'col1': [1, 2, None, 4, 5, None] * 5,
        'col2': ['a', 'b', None, 'd'] * 15
    })

@pytest.fixture
def df_with_outliers():
    np.random.seed(42)
    df = pd.DataFrame({
        'value': np.random.normal(50, 10, 100)
    })
    # Add outliers
    df.loc[0, 'value'] = 200  # Extreme high
    df.loc[1, 'value'] = -150  # Extreme low
    return df

def test_null_detection(df_with_nulls):
    detector = AnomalyDetector()
    result = detector.check_nulls(df_with_nulls)

    assert 'col1' in result
    assert result['col1']['null_count'] == 10
    assert result['col1']['null_rate'] > 0.3

def test_null_status_warning():
    detector = AnomalyDetector(null_rate_warning=0.1, null_rate_critical=0.2)
    df = pd.DataFrame({
        'col': [1, None, 3, None, 5, None, 7, None, 9, 10]  # 40% null
    })
    result = detector.check_nulls(df)
    assert result['col']['status'] == 'CRITICAL'

def test_outlier_detection_iqr(df_with_outliers):
    detector = AnomalyDetector()
    result = detector.detect_outliers(df_with_outliers)

    assert 'value' in result
    assert result['value']['outlier_count'] >= 2
    assert result['value']['method'] == 'iqr'

def test_skip_boolean_columns(sample_df):
    detector = AnomalyDetector()
    result = detector.detect_outliers(sample_df)

    # Boolean column should be skipped
    assert 'is_active' not in result

def test_anomaly_score_calculation(sample_df):
    detector = AnomalyDetector()
    detector.fit_baseline(sample_df)
    result = detector.detect_anomalies(sample_df)

    assert 0 <= result['anomaly_score'] <= 1.0
    assert result['total_anomalies'] >= 0

def test_detect_anomalies_complete(sample_df):
    detector = AnomalyDetector()
    detector.fit_baseline(sample_df)
    result = detector.detect_anomalies(sample_df)

    # Check structure
    assert 'null_analysis' in result
    assert 'outliers' in result
    assert 'domain_violations' in result
    assert 'total_anomalies' in result
    assert 'anomaly_score' in result
    assert 'timestamp' in result

def test_empty_dataframe():
    detector = AnomalyDetector()
    df = pd.DataFrame({'col': []})

    result = detector.detect_anomalies(df)
    assert result['total_anomalies'] == 0
    assert result['anomaly_score'] == 0.0

def test_domain_rules():
    detector = AnomalyDetector()
    df = pd.DataFrame({
        'price': [10, -5, 20, -15],
        'date': pd.to_datetime(['2020-01-01', '2030-01-01', '2020-06-01', '2025-12-31'])
    })

    rules = [
        {'name': 'negative_prices', 'column': 'price', 'rule_type': 'negative_values'},
        {'name': 'future_dates', 'column': 'date', 'rule_type': 'future_dates'}
    ]

    result = detector.check_domain_rules(df, rules)
    assert 'negative_prices' in result
    assert result['negative_prices']['count'] == 2

def test_baseline_fitting(sample_df):
    detector = AnomalyDetector()
    detector.fit_baseline(sample_df)

    assert len(detector.baseline_null_rates) == len(sample_df.columns)

def test_sudden_spike_detection():
    detector = AnomalyDetector()

    # Simulate historical null rates
    historical = [
        {'col1': 0.01, 'col2': 0.02},  # Normal
        {'col1': 0.02, 'col2': 0.03},  # Stable
        {'col1': 0.25, 'col2': 0.03}   # Spike in col1
    ]

    spikes = detector.detect_sudden_spikes(historical)
    assert len(spikes) > 0
    assert spikes[0]['column'] == 'col1'
    assert spikes[0]['severity'] == 'CRITICAL'

def test_mixed_data_types(sample_df):
    detector = AnomalyDetector()
    result = detector.detect_anomalies(sample_df)

    # Should handle mixed types gracefully
    assert result['total_anomalies'] >= 0
    assert not pd.isna(result['anomaly_score'])
