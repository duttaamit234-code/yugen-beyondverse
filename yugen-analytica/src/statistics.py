import pandas as pd


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
