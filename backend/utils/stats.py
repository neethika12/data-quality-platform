import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

class StatisticalTester:
    @staticmethod
    def kolmogorov_smirnov_test(baseline: pd.Series, current: pd.Series) -> Tuple[float, float]:
        """KS test for numerical features (simplified without scipy)."""
        baseline_clean = np.array(baseline.dropna().values, dtype=float)
        current_clean = np.array(current.dropna().values, dtype=float)

        if len(baseline_clean) < 2 or len(current_clean) < 2:
            return 0.0, 1.0

        # Compare means and standard deviations as proxy for distribution change
        baseline_mean = np.mean(baseline_clean)
        baseline_std = np.std(baseline_clean)
        current_mean = np.mean(current_clean)
        current_std = np.std(current_clean)

        # Normalized difference in means
        if baseline_std > 0:
            mean_diff = float(abs(current_mean - baseline_mean) / baseline_std)
        else:
            mean_diff = 0.0

        # Approximate KS statistic
        ks_stat = float(min(1.0, mean_diff / 3.0))

        # Approximate p-value: smaller difference = higher p-value
        p_value = float(np.exp(-max(0.01, mean_diff ** 2)))

        return ks_stat, p_value

    @staticmethod
    def chi_squared_test(baseline: pd.Series, current: pd.Series) -> Tuple[float, float]:
        """Chi-squared test for categorical features (simplified)."""
        baseline_counts = baseline.value_counts()
        current_counts = current.value_counts()

        # Align categories
        all_categories = set(baseline_counts.index) | set(current_counts.index)
        baseline_aligned = np.array([float(baseline_counts.get(cat, 0)) for cat in all_categories], dtype=np.float64)
        current_aligned = np.array([float(current_counts.get(cat, 0)) for cat in all_categories], dtype=np.float64)

        # Add pseudocount to avoid division by zero
        baseline_aligned = baseline_aligned + 0.5
        current_aligned = current_aligned + 0.5

        baseline_sum = float(baseline_aligned.sum())
        current_sum = float(current_aligned.sum())

        if baseline_sum == 0 or current_sum == 0:
            return 0.0, 1.0

        # Normalize to proportions
        baseline_prop = baseline_aligned / baseline_sum
        current_prop = current_aligned / current_sum

        # Chi-squared statistic
        chi2_array = (current_prop - baseline_prop) ** 2 / (baseline_prop + 1e-10)
        chi2 = float(np.sum(chi2_array))

        # Approximate p-value
        p_value = float(np.exp(-chi2))

        return chi2, p_value

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
        # Skip non-numeric and boolean types
        if pd.api.types.is_bool_dtype(series) or not pd.api.types.is_numeric_dtype(series):
            return np.array([], dtype=int), {}

        clean_series = series.dropna()
        if len(clean_series) < 4:
            return np.array([], dtype=int), {}

        try:
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
        except:
            return np.array([], dtype=int), {}

    @staticmethod
    def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> np.ndarray:
        """Detect outliers using Z-score method."""
        clean_series = series.dropna()
        if len(clean_series) < 2:
            return np.array([], dtype=int)

        # Calculate z-scores manually
        mean = np.mean(clean_series)
        std = np.std(clean_series)

        if std == 0:
            return np.array([], dtype=int)

        z_scores = np.abs((clean_series - mean) / std)
        outlier_mask = z_scores > threshold

        outlier_indices = np.where(outlier_mask)[0]
        return outlier_indices

    @staticmethod
    def calculate_distribution_stats(series: pd.Series) -> Dict[str, Any]:
        """Calculate comprehensive distribution statistics."""
        clean_series = series.dropna()

        if len(clean_series) == 0:
            return {}

        # Check if numeric (but not boolean)
        is_numeric = pd.api.types.is_numeric_dtype(clean_series) and not pd.api.types.is_bool_dtype(clean_series)

        stats_dict = {
            "count": int(len(clean_series)),
            "mean": float(clean_series.mean()) if is_numeric else None,
            "std": float(clean_series.std()) if is_numeric else None,
            "min": float(clean_series.min()) if is_numeric else None,
            "max": float(clean_series.max()) if is_numeric else None,
            "median": float(clean_series.median()) if is_numeric else None,
        }

        # Add quantiles only for true numeric (not boolean, not categorical)
        if is_numeric:
            try:
                stats_dict["q25"] = float(clean_series.quantile(0.25))
                stats_dict["q75"] = float(clean_series.quantile(0.75))
            except:
                pass

        return stats_dict
