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


def chi_square_goodness_of_fit(df, column):
    """Perform a chi-square goodness-of-fit test for equal category frequencies."""

    observed_series = df[column].dropna()

    if observed_series.empty:
        return None

    observed = observed_series.value_counts(sort=False)
    expected_value = observed.sum() / len(observed)
    expected = pd.Series(
        expected_value,
        index=observed.index
    )

    if len(observed) < 2 or (expected <= 0).any():
        return None

    chi_square_statistic, p_value = stats.chisquare(
        f_obs=observed.values,
        f_exp=expected.values
    )

    degrees_of_freedom = len(observed) - 1

    return {
        "Categories": observed.index.tolist(),
        "Observed": observed.values.tolist(),
        "Expected": expected.values.tolist(),
        "Chi-Square": chi_square_statistic,
        "P-Value": p_value,
        "Degrees of Freedom": degrees_of_freedom,
    }


def chi_square_independence(df, factor1, factor2):
    """Perform Pearson's chi-square test of independence."""

    data = df[[factor1, factor2]].dropna()

    if (
        data.empty
        or data[factor1].nunique() < 2
        or data[factor2].nunique() < 2
    ):
        return None

    contingency_table = pd.crosstab(
        data[factor1],
        data[factor2]
    )

    if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        return None

    chi_square_statistic, p_value, degrees_of_freedom, expected = (
        stats.chi2_contingency(
            contingency_table,
            correction=False
        )
    )

    expected_table = pd.DataFrame(
        expected,
        index=contingency_table.index,
        columns=contingency_table.columns
    )

    return {
        "Observed Table": contingency_table,
        "Expected Table": expected_table,
        "Chi-Square": chi_square_statistic,
        "P-Value": p_value,
        "Degrees of Freedom": degrees_of_freedom,
        "Observations": int(contingency_table.to_numpy().sum()),
    }


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

def two_sample_t_test_wide(df, value_column_1, value_column_2):
    """Perform Welch's two-sample t-test on two separate numerical columns."""

    group1 = pd.to_numeric(df[value_column_1], errors="coerce").dropna()
    group2 = pd.to_numeric(df[value_column_2], errors="coerce").dropna()

    if len(group1) < 2 or len(group2) < 2:
        return None

    t_statistic, p_value = stats.ttest_ind(
        group1,
        group2,
        equal_var=False
    )

    mean_difference = group1.mean() - group2.mean()

    variance_1 = group1.var(ddof=1)
    variance_2 = group2.var(ddof=1)

    standard_error = (
        (variance_1 / len(group1)) +
        (variance_2 / len(group2))
    ) ** 0.5

    if standard_error == 0:
        degrees_of_freedom = float("inf")
    else:
        numerator = (
            (variance_1 / len(group1)) +
            (variance_2 / len(group2))
        ) ** 2

        denominator = (
            ((variance_1 / len(group1)) ** 2) / (len(group1) - 1)
            + ((variance_2 / len(group2)) ** 2) / (len(group2) - 1)
        )

        degrees_of_freedom = numerator / denominator

    return {
        "Group 1 Mean": group1.mean(),
        "Group 2 Mean": group2.mean(),
        "Group 1 Size": len(group1),
        "Group 2 Size": len(group2),
        "Mean Difference": mean_difference,
        "T-Statistic": t_statistic,
        "P-Value": p_value,
        "Degrees of Freedom": degrees_of_freedom,
    }

def calculate_confidence_intervals(df, alpha=0.05):
    """Calculate t-based confidence intervals for numerical column means."""

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        return pd.DataFrame()

    results = []

    for column in numeric_df.columns:

        data = pd.to_numeric(
            numeric_df[column],
            errors="coerce"
        ).dropna()

        n = len(data)

        if n < 2:
            continue

        mean = data.mean()
        standard_deviation = data.std(ddof=1)
        standard_error = standard_deviation / (n ** 0.5)
        degrees_of_freedom = n - 1

        t_critical = stats.t.ppf(
            1 - (alpha / 2),
            degrees_of_freedom
        )

        margin_of_error = t_critical * standard_error

        results.append({
            "Variable": column,
            "Sample Size": n,
            "Mean": mean,
            "Standard Deviation": standard_deviation,
            "Standard Error": standard_error,
            "t-Critical": t_critical,
            "Lower Limit": mean - margin_of_error,
            "Upper Limit": mean + margin_of_error,
        })

    return pd.DataFrame(results)

def simple_linear_regression(df, x_column, y_column):
    """Perform simple linear regression between two numerical variables."""

    data = df[[x_column, y_column]].apply(
        pd.to_numeric,
        errors="coerce"
    ).dropna()

    if len(data) < 3 or data[x_column].nunique() < 2:
        return None

    result = stats.linregress(
        data[x_column],
        data[y_column]
    )

    r_squared = result.rvalue ** 2

    return {
        "X Variable": x_column,
        "Y Variable": y_column,
        "Observations": len(data),
        "Slope": result.slope,
        "Intercept": result.intercept,
        "R": result.rvalue,
        "R-Squared": r_squared,
        "Standard Error": result.stderr,
        "Slope P-Value": result.pvalue,
        "Equation": (
            f"Y = {result.intercept:.4f} "
            f"+ ({result.slope:.4f})X"
        ),
    }

def wilcoxon_signed_rank_test(df, column, hypothesized_median=0.0):
    """Perform a two-sided one-sample Wilcoxon signed-rank test."""

    data = pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()

    differences = data - hypothesized_median
    differences = differences[differences != 0]

    if len(differences) < 2:
        return None

    result = stats.wilcoxon(
        differences,
        alternative="two-sided",
        method="auto"
    )

    return {
        "Sample Size": len(differences),
        "Sample Median": data.median(),
        "Hypothesized Median": hypothesized_median,
        "W-Statistic": result.statistic,
        "P-Value": result.pvalue,
    }


def mann_whitney_u_test(df, column_1, column_2):
    """Perform a two-sided Mann-Whitney U test on two numerical columns."""

    group1 = pd.to_numeric(
        df[column_1],
        errors="coerce"
    ).dropna()

    group2 = pd.to_numeric(
        df[column_2],
        errors="coerce"
    ).dropna()

    if len(group1) < 2 or len(group2) < 2:
        return None

    result = stats.mannwhitneyu(
        group1,
        group2,
        alternative="two-sided"
    )

    return {
        "Group 1 Size": len(group1),
        "Group 2 Size": len(group2),
        "Group 1 Median": group1.median(),
        "Group 2 Median": group2.median(),
        "U-Statistic": result.statistic,
        "P-Value": result.pvalue,
    }
