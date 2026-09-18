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
