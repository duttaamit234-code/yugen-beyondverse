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


def one_way_anova(df, value_column, group_column):
    """Perform a one-way ANOVA across three or more independent groups."""

    groups = []

    for group in df[group_column].dropna().unique():
        data = df[
            df[group_column] == group
        ][value_column].dropna()

        if len(data) >= 2:
            groups.append(data)

    if len(groups) < 3:
        return None

    f_statistic, p_value = stats.f_oneway(*groups)

    group_labels = []
    group_sizes = []
    group_means = []

    for group in df[group_column].dropna().unique():
        data = df[
            df[group_column] == group
        ][value_column].dropna()

        if len(data) >= 2:
            group_labels.append(group)
            group_sizes.append(len(data))
            group_means.append(data.mean())

    total_n = sum(group_sizes)
    number_of_groups = len(group_sizes)

    between_df = number_of_groups - 1
    within_df = total_n - number_of_groups

    return {
        "Group Labels": group_labels,
        "Group Sizes": group_sizes,
        "Group Means": group_means,
        "Number of Groups": number_of_groups,
        "Total Sample Size": total_n,
        "F-Statistic": f_statistic,
        "P-Value": p_value,
        "Between-Group DF": between_df,
        "Within-Group DF": within_df,
    }



def f_critical_value(alpha, numerator_df, denominator_df):
    """Calculate the upper-tail F critical (tabulated) value."""
    
    if (
        alpha <= 0
        or alpha >= 1
        or numerator_df <= 0
        or denominator_df <= 0
    ):
        return None

    return stats.f.ppf(
        1 - alpha,
        numerator_df,
        denominator_df
    )


def two_way_anova(df, value_column, factor1, factor2):
    """Perform a two-way ANOVA with main effects and interaction."""

    data = df[[value_column, factor1, factor2]].dropna().copy()

    if (
        data.empty
        or data[value_column].nunique() < 2
        or data[factor1].nunique() < 2
        or data[factor2].nunique() < 2
    ):
        return None

    try:
        from statsmodels.formula.api import ols
        from statsmodels.stats.anova import anova_lm

        formula = (
            f'Q("{value_column}") ~ '
            f'C(Q("{factor1}")) * C(Q("{factor2}"))'
        )

        model = ols(formula, data=data).fit()
        anova_table = anova_lm(model, typ=2)

        results = []

        for source in anova_table.index:
            results.append({
                "Source": source,
                "Sum of Squares": anova_table.loc[source, "sum_sq"],
                "Degrees of Freedom": anova_table.loc[source, "df"],
                "F-Statistic": anova_table.loc[source, "F"],
                "P-Value": anova_table.loc[source, "PR(>F)"],
            })

        return {
            "ANOVA Table": pd.DataFrame(results),
            "Observations": len(data),
            "Factor 1": factor1,
            "Factor 2": factor2,
            "Response": value_column,
        }

    except Exception:
        return None


def two_sample_t_test(
    df,
    value_column,
    group_column,
    group1,
    group2
):
    """Perform a two-sided Welch's independent two-sample t-test."""

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

    n1 = len(group1_data)
    n2 = len(group2_data)

    variance1 = group1_data.var(ddof=1)
    variance2 = group2_data.var(ddof=1)

    numerator = (
        (variance1 / n1) +
        (variance2 / n2)
    ) ** 2

    denominator = (
        ((variance1 / n1) ** 2) / (n1 - 1)
        +
        ((variance2 / n2) ** 2) / (n2 - 1)
    )

    degrees_of_freedom = (
        numerator / denominator
    )

    return {
        "Group 1": group1,
        "Group 2": group2,
        "Group 1 Size": n1,
        "Group 2 Size": n2,
        "Group 1 Mean": group1_data.mean(),
        "Group 2 Mean": group2_data.mean(),
        "Mean Difference": (
            group1_data.mean() -
            group2_data.mean()
        ),
        "T-Statistic": t_statistic,
        "P-Value": p_value,
        "Degrees of Freedom": degrees_of_freedom,
        }
