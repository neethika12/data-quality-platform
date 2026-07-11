import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Dict, Any

class StatisticalTester:
    @staticmethod
    def kolmogorov_smirnov_test(baseline: pd.Series, current: pd.Series) -> Tuple[float, float]:
        """KS test for numerical features."""
        baseline_clean = baseline.dropna().values
        current_clean = current.dropna().values

        if len(baseline_clean) < 2 or len(current_clean) < 2:
            return 0.0, 1.0

        statistic, p_value = stats.ks_2samp(baseline_clean, current_clean)
        return float(statistic), float(p_value)

    @staticmethod
    def chi_squared_test(baseline: pd.Series, current: pd.Series) -> Tuple[float, float]:
        """Chi-squared test for categorical features."""
        baseline_counts = baseline.value_counts()
        current_counts = current.value_counts()

        # Align categories
        all_categories = set(baseline_counts.index) | set(current_counts.index)
        baseline_aligned = pd.Series([baseline_counts.get(cat, 0) for cat in all_categories])
        current_aligned = pd.Series([current_counts.get(cat, 0) for cat in all_categories])

        # Add pseudocount to avoid division by zero
        baseline_aligned = baseline_aligned + 0.5
        current_aligned = current_aligned + 0.5

        if baseline_aligned.sum() == 0 or current_aligned.sum() == 0:
            return 0.0, 1.0

        chi2, p_value = stats.chisquare(current_aligned, baseline_aligned)
        return float(chi2), float(p_value)

    @staticmethod
    def drift_severity_score(p_value: float, test_type: str = "ks") -> float:
        """Convert p-value to drift severity score (0-1)."""
        if p_value >= 0.05:
            return 0.0
        # Transform p-value to severity: log scale
        score = min(1.0, -np.log10(p_value) / 5.0)
        return float(score)

    @staticmethod
    def detect_outliers_iqr(series: pd.Series) -> Tuple[np.ndarray, Dict[str, float]]:
        """Detect outliers using IQR method."""
        clean_series = series.dropna()
        if len(clean_series) < 4:
            return np.array([], dtype=int), {}

        Q1 = clean_series.quantile(0.25)
        Q3 = clean_series.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_indices = np.where(outlier_mask)[0]

        stats_dict = {
            "Q1": float(Q1),
            "Q3": float(Q3),
            "IQR": float(IQR),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound)
        }

        return outlier_indices, stats_dict

    @staticmethod
    def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> np.ndarray:
        """Detect outliers using Z-score method."""
        clean_series = series.dropna()
        if len(clean_series) < 2:
            return np.array([], dtype=int)

        z_scores = np.abs(stats.zscore(clean_series))
        outlier_mask = z_scores > threshold

        outlier_indices = np.where(outlier_mask)[0]
        return outlier_indices

    @staticmethod
    def calculate_distribution_stats(series: pd.Series) -> Dict[str, Any]:
        """Calculate comprehensive distribution statistics."""
        clean_series = series.dropna()

        if len(clean_series) == 0:
            return {}

        stats_dict = {
            "count": int(len(clean_series)),
            "mean": float(clean_series.mean()) if pd.api.types.is_numeric_dtype(clean_series) else None,
            "std": float(clean_series.std()) if pd.api.types.is_numeric_dtype(clean_series) else None,
            "min": float(clean_series.min()) if pd.api.types.is_numeric_dtype(clean_series) else None,
            "max": float(clean_series.max()) if pd.api.types.is_numeric_dtype(clean_series) else None,
            "median": float(clean_series.median()) if pd.api.types.is_numeric_dtype(clean_series) else None,
        }

        # Add quantiles for numerical
        if pd.api.types.is_numeric_dtype(clean_series):
            stats_dict["q25"] = float(clean_series.quantile(0.25))
            stats_dict["q75"] = float(clean_series.quantile(0.75))

        return stats_dict
