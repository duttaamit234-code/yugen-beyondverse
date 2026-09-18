import pandas as pd
from scipy import stats


def get_numeric_statistics(df):
    """Calculate descriptive statistics for numeric columns."""

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        return pd.DataFrame()

    statistics = pd.DataFrame({
        "Count": numeric_df.count(),
        "Mean": numeric_df.mean(),
        "Median": numeric_df.median(),
        "Standard Deviation": numeric_df.std(),
        "Minimum": numeric_df.min(),
        "Q1": numeric_df.quantile(0.25),
        "Q3": numeric_df.quantile(0.75),
        "Maximum": numeric_df.max(),
    })

    statistics["IQR"] = (
        statistics["Q3"] - statistics["Q1"]
    )

    return statistics


def detect_outliers(df):
    """Detect potential outliers using the 1.5 × IQR rule."""

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        return pd.DataFrame()

    results = []

    for column in numeric_df.columns:

        series = numeric_df[column].dropna()

        if series.empty:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outliers = series[
            (series < lower_bound) |
            (series > upper_bound)
        ]

        results.append({
            "Column": column,
            "Q1": q1,
            "Q3": q3,
            "IQR": iqr,
            "Lower Bound": lower_bound,
            "Upper Bound": upper_bound,
            "Outlier Count": len(outliers),
        })

    return pd.DataFrame(results)


def calculate_correlation(df):
    """Calculate the Pearson correlation matrix for numeric columns."""

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.shape[1] < 2:
        return pd.DataFrame()

    return numeric_df.corr()


def one_sample_t_test(df, column, hypothesized_mean):
    """Perform a two-sided one-sample t-test."""

    data = df[column].dropna()

    if len(data) < 2:
        return None

    t_statistic, p_value = stats.ttest_1samp(
        data,
        popmean=hypothesized_mean
    )

    return {
        "Sample Size": len(data),
        "Sample Mean": data.mean(),
        "Hypothesized Mean": hypothesized_mean,
        "T-Statistic": t_statistic,
        "P-Value": p_value,
        "Degrees of Freedom": len(data) - 1,
    }


def two_sample_t_test(df, value_column, group_column, group1, group2):
    """Perform a two-sided Welch's two-sample t-test."""

    group1_data = df[
        df[group_column] == group1
    ][value_column].dropna()

    group2_data = df[
        df[group_column] == group2
    ][value_column].dropna()

    if len(group1_data) < 2 or len(group2_data) < 2:
        return None

    t_statistic, p_value = stats.ttest_ind(
        group1_data,
        group2_data,
        equal_var=False
    )

    return {
        "Group 1": group1,
        "Group 2": group2,
        "Group 1 Size": len(group1_data),
        "Group 2 Size": len(group2_data),
        "Group 1 Mean": group1_data.mean(),
        "Group 2 Mean": group2_data.mean(),
        "Mean Difference": (
            group1_data.mean() - group2_data.mean()
        ),
        "T-Statistic": t_statistic,
        "P-Value": p_value,
        "Degrees of Freedom": (
            len(group1_data) + len(group2_data) - 2
        ),
    }
