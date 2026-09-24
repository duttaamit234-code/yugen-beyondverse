import pandas as pd
import streamlit as st

# StatsYuri web build: keep the statistical modules synchronized with this app.
from scipy import stats

from src.data_loader import (
    load_dataset,
    validate_dataset,
    get_dataset_summary,
)

from src.statistics import (
    get_numeric_statistics,
    calculate_confidence_intervals,
    detect_outliers,
    calculate_correlation,
    one_sample_t_test,
    two_sample_t_test,
    two_sample_t_test_wide,
    one_way_anova,
    two_way_anova,
    chi_square_goodness_of_fit,
    chi_square_independence,
)

from src.visualization import (
    get_numeric_columns,
    create_histogram,
    create_box_plot,
    create_correlation_heatmap,
)


st.set_page_config(
    page_title="StatsYuri",
    page_icon="📊",
    layout="wide",
)


st.title("StatsYuri")
st.subheader("Statistical Analysis Platform")

st.write(
    "Upload a dataset to begin exploring and analyzing your data."
)


uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx", "xls"],
)


if uploaded_file is not None:

    try:
        df = load_dataset(uploaded_file)

        st.success("Dataset uploaded successfully.")


        st.subheader("Dataset Preview")

        st.dataframe(
            df,
            use_container_width=True
        )


        st.subheader("Dataset Validation")

        validation = validate_dataset(df)

        if validation["valid"]:
            st.success(
                "Dataset passed basic validation."
            )
        else:
            st.warning(
                "Dataset has some issues."
            )


        if validation["missing_values"] > 0:
            st.info(
                f"Missing values detected: "
                f"{validation['missing_values']}"
            )
        else:
            st.success(
                "No missing values detected."
            )


        st.subheader("Dataset Summary")

        summary = get_dataset_summary(df)


        col1, col2, col3 = st.columns(3)


        with col1:
            st.metric(
                "Rows",
                summary["rows"]
            )


        with col2:
            st.metric(
                "Columns",
                summary["columns"]
            )


        with col3:
            st.metric(
                "Missing Values",
                summary["missing_values"]
            )


        numeric_columns = get_numeric_columns(df)


        st.subheader("Descriptive Statistics")

        statistics = get_numeric_statistics(df)


        if statistics.empty:

            st.info(
                "No numerical columns were found "
                "in this dataset."
            )

        else:

            st.dataframe(
                statistics,
                use_container_width=True
            )


        st.subheader("Confidence Intervals")

        st.write(
            "Calculate t-based confidence intervals for the means "
            "of numerical variables."
        )

        if not numeric_columns:

            st.info(
                "No numerical columns are available "
                "for confidence interval estimation."
            )

        else:

            confidence_level = st.selectbox(
                "Confidence Level",
                [0.90, 0.95, 0.99],
                index=1,
                format_func=lambda value: f"{value * 100:.0f}%",
                key="confidence_level"
            )

            confidence_alpha = 1 - confidence_level

            confidence_results = calculate_confidence_intervals(
                df,
                confidence_alpha
            )

            if confidence_results.empty:

                st.info(
                    "At least two valid observations are required "
                    "for confidence interval estimation."
                )

            else:

                st.dataframe(
                    confidence_results.style.format({
                        "Mean": "{:.4f}",
                        "Standard Deviation": "{:.4f}",
                        "Standard Error": "{:.4f}",
                        "t-Critical": "{:.4f}",
                        "Lower Limit": "{:.4f}",
                        "Upper Limit": "{:.4f}",
                    }),
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    "The interval estimates the population mean using "
                    "the t-distribution."
                )


        st.subheader("Outlier Detection")

        outlier_results = detect_outliers(df)


        if outlier_results.empty:

            st.info(
                "No numerical columns are available "
                "for outlier detection."
            )

        else:

            st.dataframe(
                outlier_results,
                use_container_width=True,
                hide_index=True
            )


            total_outliers = int(
                outlier_results["Outlier Count"].sum()
            )


            if total_outliers == 0:

                st.success(
                    "No potential outliers were detected "
                    "using the 1.5 × IQR rule."
                )

            else:

                st.warning(
                    f"{total_outliers} potential outlier(s) "
                    "were detected using the 1.5 × IQR rule."
                )


        st.subheader("Data Visualization")

        if not numeric_columns:

            st.info(
                "No numerical columns are available "
                "for visualization."
            )

        else:

            selected_column = st.selectbox(
                "Select a numerical column",
                numeric_columns
            )


            st.write("### Histogram")

            histogram = create_histogram(
                df,
                selected_column
            )

            st.pyplot(
                histogram,
                use_container_width=True
            )


            st.write("### Box Plot")

            box_plot = create_box_plot(
                df,
                selected_column
            )

            st.pyplot(
                box_plot,
                use_container_width=True
            )


        st.subheader("Correlation Analysis")

        correlation_matrix = calculate_correlation(df)


        if correlation_matrix.empty:

            st.info(
                "At least two numerical columns "
                "are required for correlation analysis."
            )

        else:

            st.write(
                "Pearson correlation coefficients "
                "between numerical variables."
            )


            st.dataframe(
                correlation_matrix,
                use_container_width=True
            )


            st.write("### Correlation Heatmap")


            heatmap = create_correlation_heatmap(
                correlation_matrix
            )


            st.pyplot(
                heatmap,
                use_container_width=True
            )


        st.subheader("Hypothesis Testing")

        st.write(
            "One-Sample t-Test: test whether the "
            "population mean differs from a specified value."
        )


        if not numeric_columns:

            st.info(
                "No numerical columns are available "
                "for hypothesis testing."
            )

        else:

            test_column = st.selectbox(
                "Select a numerical column for the t-test",
                numeric_columns,
                key="ttest_column"
            )


            hypothesized_mean = st.number_input(
                "Hypothesized Mean",
                value=0.0,
                step=1.0
            )


            significance_level = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1
            )


            if st.button("Run One-Sample t-Test"):

                test_result = one_sample_t_test(
                    df,
                    test_column,
                    hypothesized_mean
                )


                if test_result is None:

                    st.error(
                        "At least two valid observations "
                        "are required for the t-test."
                    )

                else:

                    result_col1, result_col2 = st.columns(2)


                    with result_col1:

                        st.metric(
                            "Sample Mean",
                            f"{test_result['Sample Mean']:.4f}"
                        )

                        st.metric(
                            "T-Statistic",
                            f"{test_result['T-Statistic']:.4f}"
                        )

                        st.metric(
                            "Degrees of Freedom",
                            test_result["Degrees of Freedom"]
                        )


                    with result_col2:

                        st.metric(
                            "Hypothesized Mean",
                            f"{test_result['Hypothesized Mean']:.4f}"
                        )

                        st.metric(
                            "P-Value",
                            f"{test_result['P-Value']:.6f}"
                        )

                        st.metric(
                            "Sample Size",
                            test_result["Sample Size"]
                        )

                        t_critical = stats.t.ppf(
                            1 - (significance_level / 2),
                            test_result["Degrees of Freedom"]
                        )

                        t_decision = (
                            "Significant"
                            if abs(test_result["T-Statistic"]) > t_critical
                            else "Not Significant"
                        )

                        st.write("### t-Test Comparison")

                        t_comparison = pd.DataFrame({
                            "t-Calculated": [
                                test_result["T-Statistic"]
                            ],
                            "t-Tabulated": [
                                t_critical
                            ],
                            "df": [
                                test_result["Degrees of Freedom"]
                            ],
                            "α": [
                                significance_level
                            ],
                            "Decision": [
                                t_decision
                            ],
                        })

                        st.dataframe(
                            t_comparison.style.format({
                                "t-Calculated": "{:.4f}",
                                "t-Tabulated": "{:.4f}",
                                "α": "{:.2f}",
                            }),
                            use_container_width=True,
                            hide_index=True
                        )

                        if abs(test_result["T-Statistic"]) > t_critical:
                            st.warning(
                                f"|t-calculated| ({abs(test_result['T-Statistic']):.4f}) "
                                f"> t-tabulated ({t_critical:.4f}). "
                                "Reject the null hypothesis."
                            )
                        else:
                            st.success(
                                f"|t-calculated| ({abs(test_result['T-Statistic']):.4f}) "
                                f"≤ t-tabulated ({t_critical:.4f}). "
                                "Fail to reject the null hypothesis."
                            )


                    if test_result["P-Value"] < significance_level:

                        st.warning(
                            f"Reject the null hypothesis at "
                            f"α = {significance_level}. "
                            "The sample provides evidence that "
                            "the population mean differs from "
                            "the hypothesized mean."
                        )

                    else:

                        st.success(
                            f"Fail to reject the null hypothesis "
                            f"at α = {significance_level}. "
                            "The sample does not provide sufficient "
                            "evidence that the population mean differs "
                            "from the hypothesized mean."
                        )


        st.subheader("Two-Sample t-Test")

        st.write(
            "Compare the means of two independent groups "
            "using Welch's two-sample t-test."
        )

        if len(numeric_columns) < 2:

            st.info(
                "At least two numerical columns are required "
                "for two-sample testing."
            )

        else:

            # Automatically detect the dataset structure.
            # A categorical column is treated as a grouping variable only
            # when every category has at least two observations.
            grouping_candidates = []

            for column in df.columns:

                if pd.api.types.is_numeric_dtype(df[column]):
                    continue

                counts = df[column].dropna().value_counts()

                if (
                    len(counts) >= 2
                    and (counts >= 2).all()
                ):
                    grouping_candidates.append(column)

            if grouping_candidates:

                # Prefer a two-level grouping variable when available.
                two_level_candidates = [
                    column
                    for column in grouping_candidates
                    if df[column].dropna().nunique() == 2
                ]

                if two_level_candidates:
                    default_group_column = two_level_candidates[0]
                else:
                    default_group_column = grouping_candidates[0]

                st.caption(
                    f"Detected grouped data using '{default_group_column}' "
                    "as the grouping structure."
                )

                group_column = st.selectbox(
                    "Grouping column",
                    grouping_candidates,
                    index=grouping_candidates.index(default_group_column),
                    key="group_column"
                )

                group_values = (
                    df[group_column]
                    .dropna()
                    .unique()
                    .tolist()
                )

                value_column = st.selectbox(
                    "Numerical variable",
                    numeric_columns,
                    key="two_sample_value"
                )

                group1 = st.selectbox(
                    "Group 1",
                    group_values,
                    key="group1"
                )

                remaining_groups = [
                    value
                    for value in group_values
                    if value != group1
                ]

                group2 = st.selectbox(
                    "Group 2",
                    remaining_groups,
                    key="group2"
                )

                two_sample_alpha = st.selectbox(
                    "Significance Level (α)",
                    [0.01, 0.05, 0.10],
                    index=1,
                    key="two_sample_alpha"
                )

                if st.button(
                    "Run Two-Sample t-Test",
                    key="run_two_sample_grouped"
                ):

                    two_sample_result = two_sample_t_test(
                        df,
                        value_column,
                        group_column,
                        group1,
                        group2
                    )

            else:

                st.caption(
                    "Detected two-sample data as separate numerical columns."
                )

                col1, col2 = st.columns(2)

                with col1:
                    wide_group1 = st.selectbox(
                        "Numerical Group 1",
                        numeric_columns,
                        key="wide_group1"
                    )

                remaining_numeric = [
                    column
                    for column in numeric_columns
                    if column != wide_group1
                ]

                with col2:
                    wide_group2 = st.selectbox(
                        "Numerical Group 2",
                        remaining_numeric,
                        key="wide_group2"
                    )

                two_sample_alpha = st.selectbox(
                    "Significance Level (α)",
                    [0.01, 0.05, 0.10],
                    index=1,
                    key="wide_two_sample_alpha"
                )

                if st.button(
                    "Run Two-Sample t-Test",
                    key="run_two_sample_wide"
                ):

                    two_sample_result = two_sample_t_test_wide(
                        df,
                        wide_group1,
                        wide_group2
                    )

            if "two_sample_result" in locals() and two_sample_result is not None:

                result_col1, result_col2 = st.columns(2)

                with result_col1:
                    st.metric(
                        "Group 1 Mean",
                        f"{two_sample_result['Group 1 Mean']:.4f}"
                    )
                    st.metric(
                        "Group 1 Sample Size",
                        two_sample_result["Group 1 Size"]
                    )
                    st.metric(
                        "Mean Difference",
                        f"{two_sample_result['Mean Difference']:.4f}"
                    )
                    st.metric(
                        "T-Statistic",
                        f"{two_sample_result['T-Statistic']:.4f}"
                    )

                with result_col2:
                    st.metric(
                        "Group 2 Mean",
                        f"{two_sample_result['Group 2 Mean']:.4f}"
                    )
                    st.metric(
                        "Group 2 Sample Size",
                        two_sample_result["Group 2 Size"]
                    )
                    st.metric(
                        "P-Value",
                        f"{two_sample_result['P-Value']:.6f}"
                    )
                    st.metric(
                        "Degrees of Freedom",
                        f"{two_sample_result['Degrees of Freedom']:.4f}"
                    )

                t_critical = stats.t.ppf(
                    1 - (two_sample_alpha / 2),
                    two_sample_result["Degrees of Freedom"]
                )

                t_decision = (
                    "Significant"
                    if abs(two_sample_result["T-Statistic"]) > t_critical
                    else "Not Significant"
                )

                st.write("### t-Test Comparison")

                t_comparison = pd.DataFrame({
                    "t-Calculated": [two_sample_result["T-Statistic"]],
                    "t-Tabulated": [t_critical],
                    "df": [two_sample_result["Degrees of Freedom"]],
                    "α": [two_sample_alpha],
                    "Decision": [t_decision],
                })

                st.dataframe(
                    t_comparison.style.format({
                        "t-Calculated": "{:.4f}",
                        "t-Tabulated": "{:.4f}",
                        "df": "{:.4f}",
                        "α": "{:.2f}",
                    }),
                    use_container_width=True,
                    hide_index=True
                )

                if abs(two_sample_result["T-Statistic"]) > t_critical:
                    st.warning(
                        f"|t-calculated| ({abs(two_sample_result['T-Statistic']):.4f}) "
                        f"> t-tabulated ({t_critical:.4f}). "
                        "Reject the null hypothesis."
                    )
                else:
                    st.success(
                        f"|t-calculated| ({abs(two_sample_result['T-Statistic']):.4f}) "
                        f"≤ t-tabulated ({t_critical:.4f}). "
                        "Fail to reject the null hypothesis."
                    )

            elif "two_sample_result" in locals():

                st.error(
                    "Each selected group must have at least two "
                    "valid numerical observations."
                )


        st.subheader("One-Way ANOVA")

        st.write(
            "Compare the means of three or more independent groups "
            "using one-way analysis of variance (ANOVA)."
        )


        if len(numeric_columns) == 0:

            st.info(
                "A numerical column is required for ANOVA."
            )

        else:

            anova_group_columns = [
                column
                for column in df.columns
                if not pd.api.types.is_numeric_dtype(df[column])
                and df[column].nunique(dropna=True) >= 3
            ]


            if not anova_group_columns:

                st.info(
                    "No grouping column with at least three groups "
                    "was found."
                )

            else:

                anova_group_column = st.selectbox(
                    "Select the ANOVA grouping column",
                    anova_group_columns,
                    key="anova_group_column"
                )

                anova_value_column = st.selectbox(
                    "Select the ANOVA numerical variable",
                    numeric_columns,
                    key="anova_value_column"
                )

                anova_alpha = st.selectbox(
                    "ANOVA Significance Level (α)",
                    [0.01, 0.05, 0.10],
                    index=1,
                    key="anova_alpha"
                )


                if st.button("Run One-Way ANOVA"):

                    anova_result = one_way_anova(
                        df,
                        anova_value_column,
                        anova_group_column
                    )


                    if anova_result is None:

                        st.error(
                            "At least three groups with two or more "
                            "valid observations each are required."
                        )

                    else:

                        st.write("### Group Summary")

                        group_summary = {
                            "Group": anova_result["Group Labels"],
                            "Sample Size": anova_result["Group Sizes"],
                            "Mean": anova_result["Group Means"],
                        }

                        st.dataframe(
                            group_summary,
                            use_container_width=True,
                            hide_index=True
                        )


                        result_col1, result_col2 = st.columns(2)


                        with result_col1:

                            st.metric(
                                "F-Statistic",
                                f"{anova_result['F-Statistic']:.4f}"
                            )

                            st.metric(
                                "Between-Group DF",
                                anova_result["Between-Group DF"]
                            )

                            st.metric(
                                "Within-Group DF",
                                anova_result["Within-Group DF"]
                            )


                        with result_col2:

                            st.metric(
                                "P-Value",
                                f"{anova_result['P-Value']:.6f}"
                            )

                            st.metric(
                                "Number of Groups",
                                anova_result["Number of Groups"]
                            )

                            st.metric(
                                "Total Sample Size",
                                anova_result["Total Sample Size"]
                            )


                        f_tabulated = stats.f.ppf(
                            1 - anova_alpha,
                            anova_result["Between-Group DF"],
                            anova_result["Within-Group DF"]
                        )

                        st.write("### F-Test Comparison")

                        f_comparison = pd.DataFrame({
                            "F-Calculated": [
                                anova_result["F-Statistic"]
                            ],
                            "F-Tabulated": [
                                f_tabulated
                            ],
                            "Significance Level (α)": [
                                anova_alpha
                            ],
                            "Decision": [
                                "Significant"
                                if anova_result["F-Statistic"] > f_tabulated
                                else "Not Significant"
                            ],
                        })

                        st.dataframe(
                            f_comparison.style.format({
                                "F-Calculated": "{:.4f}",
                                "F-Tabulated": "{:.4f}",
                                "Significance Level (α)": "{:.2f}",
                            }),
                            use_container_width=True,
                            hide_index=True
                        )

                        if anova_result["F-Statistic"] > f_tabulated:

                            st.warning(
                                f"F-calculated ({anova_result['F-Statistic']:.4f}) "
                                f"> F-tabulated ({f_tabulated:.4f}) at "
                                f"α = {anova_alpha}. Reject the null hypothesis."
                            )

                        else:

                            st.success(
                                f"F-calculated ({anova_result['F-Statistic']:.4f}) "
                                f"≤ F-tabulated ({f_tabulated:.4f}) at "
                                f"α = {anova_alpha}. Fail to reject the null hypothesis."
                            )


                        st.caption(
                            "ANOVA tests whether all group means are equal. "
                            "A significant result indicates that at least "
                            "one mean differs, but does not identify which "
                            "groups differ."
                        )



        st.subheader("Chi-Square Critical Value Calculator")

        st.write(
            "Calculate the χ² tabulated (critical) value from "
            "degrees of freedom and significance level."
        )

        critical_col1, critical_col2 = st.columns(2)

        with critical_col1:
            chi_critical_df = st.number_input(
                "Degrees of Freedom",
                min_value=1,
                value=1,
                step=1,
                key="chi_critical_df"
            )

        with critical_col2:
            chi_critical_alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.025, 0.05, 0.10],
                index=2,
                key="chi_critical_alpha"
            )

        chi_critical_value = stats.chi2.ppf(
            1 - chi_critical_alpha,
            chi_critical_df
        )

        chi_critical_result = pd.DataFrame({
            "df": [chi_critical_df],
            "α": [chi_critical_alpha],
            "χ²-Tabulated": [chi_critical_value],
        })

        st.dataframe(
            chi_critical_result.style.format({
                "α": "{:.3f}",
                "χ²-Tabulated": "{:.4f}",
            }),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "This value is the same type of critical value found "
            "in a printed χ² distribution table."
        )


        st.subheader("Chi-Square Tests")

        st.write(
            "Perform chi-square goodness-of-fit and test-of-independence "
            "procedures using calculated and tabulated chi-square values."
        )

        categorical_columns = [
            column
            for column in df.columns
            if column not in numeric_columns
            and df[column].nunique(dropna=True) >= 2
        ]

        if not categorical_columns:

            st.info(
                "At least one categorical column with two or more "
                "categories is required for chi-square testing."
            )

        else:

            st.write("### Chi-Square Goodness-of-Fit")

            st.caption(
                "Tests whether the observed category frequencies are "
                "consistent with equal expected frequencies."
            )

            chi_gof_column = st.selectbox(
                "Select a categorical variable",
                categorical_columns,
                key="chi_gof_column"
            )

            chi_gof_alpha = st.selectbox(
                "Goodness-of-Fit Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="chi_gof_alpha"
            )

            if st.button("Run Chi-Square Goodness-of-Fit"):

                chi_gof_result = chi_square_goodness_of_fit(
                    df,
                    chi_gof_column
                )

                if chi_gof_result is None:

                    st.error(
                        "At least two categories with valid observations "
                        "are required."
                    )

                else:

                    gof_summary = pd.DataFrame({
                        "Category": chi_gof_result["Categories"],
                        "Observed": chi_gof_result["Observed"],
                        "Expected": chi_gof_result["Expected"],
                    })

                    st.dataframe(
                        gof_summary.style.format({
                            "Expected": "{:.2f}"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    gof_f_tabulated = stats.chi2.ppf(
                        1 - chi_gof_alpha,
                        chi_gof_result["Degrees of Freedom"]
                    )

                    gof_decision = (
                        "Significant"
                        if chi_gof_result["Chi-Square"] > gof_f_tabulated
                        else "Not Significant"
                    )

                    gof_result_table = pd.DataFrame({
                        "χ²-Calculated": [
                            chi_gof_result["Chi-Square"]
                        ],
                        "χ²-Tabulated": [
                            gof_f_tabulated
                        ],
                        "df": [
                            chi_gof_result["Degrees of Freedom"]
                        ],
                        "p-value": [
                            chi_gof_result["P-Value"]
                        ],
                        "Decision": [
                            gof_decision
                        ],
                    })

                    st.dataframe(
                        gof_result_table.style.format({
                            "χ²-Calculated": "{:.4f}",
                            "χ²-Tabulated": "{:.4f}",
                            "p-value": lambda value:
                                "<0.000001"
                                if value < 0.000001
                                else f"{value:.6f}",
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    if gof_decision == "Significant":
                        st.warning(
                            f"χ²-calculated ({chi_gof_result['Chi-Square']:.4f}) "
                            f"> χ²-tabulated ({gof_f_tabulated:.4f}). "
                            "Reject the null hypothesis."
                        )
                    else:
                        st.success(
                            f"χ²-calculated ({chi_gof_result['Chi-Square']:.4f}) "
                            f"≤ χ²-tabulated ({gof_f_tabulated:.4f}). "
                            "Fail to reject the null hypothesis."
                        )

            st.write("### Chi-Square Test of Independence")

            st.caption(
                "Tests whether two categorical variables are statistically independent."
            )

            if len(categorical_columns) < 2:

                st.info(
                    "At least two categorical columns are required "
                    "for a test of independence."
                )

            else:

                chi_ind_factor1 = st.selectbox(
                    "Select Variable 1",
                    categorical_columns,
                    key="chi_ind_factor1"
                )

                remaining_chi_columns = [
                    column
                    for column in categorical_columns
                    if column != chi_ind_factor1
                ]

                chi_ind_factor2 = st.selectbox(
                    "Select Variable 2",
                    remaining_chi_columns,
                    key="chi_ind_factor2"
                )

                chi_ind_alpha = st.selectbox(
                    "Independence Test Significance Level (α)",
                    [0.01, 0.05, 0.10],
                    index=1,
                    key="chi_ind_alpha"
                )

                if st.button("Run Chi-Square Test of Independence"):

                    chi_ind_result = chi_square_independence(
                        df,
                        chi_ind_factor1,
                        chi_ind_factor2
                    )

                    if chi_ind_result is None:

                        st.error(
                            "The selected variables must each contain "
                            "at least two valid categories."
                        )

                    else:

                        st.write("#### Observed Frequencies")

                        st.dataframe(
                            chi_ind_result["Observed Table"],
                            use_container_width=True
                        )

                        st.write("#### Expected Frequencies")

                        st.dataframe(
                            chi_ind_result["Expected Table"].style.format(
                                "{:.2f}"
                            ),
                            use_container_width=True
                        )

                        chi_ind_tabulated = stats.chi2.ppf(
                            1 - chi_ind_alpha,
                            chi_ind_result["Degrees of Freedom"]
                        )

                        chi_ind_decision = (
                            "Significant"
                            if chi_ind_result["Chi-Square"] > chi_ind_tabulated
                            else "Not Significant"
                        )

                        chi_ind_result_table = pd.DataFrame({
                            "χ²-Calculated": [
                                chi_ind_result["Chi-Square"]
                            ],
                            "χ²-Tabulated": [
                                chi_ind_tabulated
                            ],
                            "df": [
                                chi_ind_result["Degrees of Freedom"]
                            ],
                            "p-value": [
                                chi_ind_result["P-Value"]
                            ],
                            "Decision": [
                                chi_ind_decision
                            ],
                        })

                        st.dataframe(
                            chi_ind_result_table.style.format({
                                "χ²-Calculated": "{:.4f}",
                                "χ²-Tabulated": "{:.4f}",
                                "p-value": lambda value:
                                    "<0.000001"
                                    if value < 0.000001
                                    else f"{value:.6f}",
                            }),
                            use_container_width=True,
                            hide_index=True
                        )

                        if chi_ind_decision == "Significant":
                            st.warning(
                                f"χ²-calculated ({chi_ind_result['Chi-Square']:.4f}) "
                                f"> χ²-tabulated ({chi_ind_tabulated:.4f}). "
                                "Reject the null hypothesis of independence."
                            )
                        else:
                            st.success(
                                f"χ²-calculated ({chi_ind_result['Chi-Square']:.4f}) "
                                f"≤ χ²-tabulated ({chi_ind_tabulated:.4f}). "
                                "Fail to reject the null hypothesis of independence."
                            )

                        st.metric(
                            "Observations Used",
                            chi_ind_result["Observations"]
                        )


        st.subheader("Two-Way ANOVA")

        st.write(
            "Analyze the effects of two categorical factors on a "
            "numerical response, including their interaction."
        )

        if len(numeric_columns) == 0:

            st.info(
                "A numerical response column is required for two-way ANOVA."
            )

        else:

            factor_columns = [
                column
                for column in df.columns
                if df[column].nunique(dropna=True) >= 2
                and column not in numeric_columns
            ]

            if len(factor_columns) < 2:

                st.info(
                    "At least two categorical grouping columns with "
                    "two or more levels each are required."
                )

            else:

                two_way_factor1 = st.selectbox(
                    "Select Factor 1",
                    factor_columns,
                    key="two_way_factor1"
                )

                remaining_factor_columns = [
                    column
                    for column in factor_columns
                    if column != two_way_factor1
                ]

                two_way_factor2 = st.selectbox(
                    "Select Factor 2",
                    remaining_factor_columns,
                    key="two_way_factor2"
                )

                two_way_value = st.selectbox(
                    "Select the numerical response",
                    numeric_columns,
                    key="two_way_value"
                )

                two_way_alpha = st.selectbox(
                    "Two-Way ANOVA Significance Level (α)",
                    [0.01, 0.05, 0.10],
                    index=1,
                    key="two_way_alpha"
                )

                if st.button("Run Two-Way ANOVA"):

                    two_way_result = two_way_anova(
                        df,
                        two_way_value,
                        two_way_factor1,
                        two_way_factor2
                    )

                    if two_way_result is None:

                        st.error(
                            "The selected data could not be used for "
                            "two-way ANOVA. Check that both factors have "
                            "at least two levels and that valid numerical "
                            "observations are available."
                        )

                    else:

                        st.write("### Two-Way ANOVA Results")

                        anova_table = two_way_result["ANOVA Table"].copy()

                        def format_anova_source(source):
                            if source.startswith("C(Q("):
                                parts = source.replace("C(Q(\"", "").replace("\"))", "")
                                if ":C(Q(\"" in parts:
                                    parts = parts.replace(":C(Q(\"", " × ").replace("\"))", "")
                                return parts
                            return source

                        residual_df = anova_table.loc[
                            anova_table["Source"] == "Residual",
                            "Degrees of Freedom"
                        ].iloc[0]

                        display_table = anova_table.rename(
                            columns={
                                "Source": "Effect",
                                "Sum of Squares": "Sum of Squares",
                                "Degrees of Freedom": "df",
                                "F-Statistic": "Fcal",
                                "P-Value": "p-value",
                            }
                        ).copy()

                        display_table["Effect"] = display_table["Effect"].apply(
                            format_anova_source
                        )

                        display_table["Ftab"] = display_table.apply(
                            lambda row: stats.f.ppf(
                                1 - two_way_alpha,
                                row["df"],
                                residual_df
                            )
                            if pd.notna(row["Fcal"])
                            else float("nan"),
                            axis=1
                        )

                        display_table["Decision"] = display_table.apply(
                            lambda row: (
                                "Significant"
                                if pd.notna(row["Fcal"])
                                and row["Fcal"] > row["Ftab"]
                                else "Not Significant"
                                if pd.notna(row["Fcal"])
                                else "—"
                            ),
                            axis=1
                        )

                        display_table["df"] = display_table["df"].map(
                            lambda value: f"{value:.0f}"
                            if pd.notna(value) else ""
                        )

                        display_table["Fcal"] = display_table["Fcal"].map(
                            lambda value: f"{value:.4f}"
                            if pd.notna(value) else "—"
                        )

                        display_table["Ftab"] = display_table["Ftab"].map(
                            lambda value: f"{value:.4f}"
                            if pd.notna(value) else "—"
                        )

                        display_table["p-value"] = display_table["p-value"].map(
                            lambda value: "<0.000001"
                            if pd.notna(value) and value < 0.000001
                            else f"{value:.6f}"
                            if pd.notna(value)
                            else "—"
                        )

                        st.dataframe(
                            display_table[
                                [
                                    "Effect",
                                    "Sum of Squares",
                                    "df",
                                    "Fcal",
                                    "Ftab",
                                    "p-value",
                                    "Decision",
                                ]
                            ],
                            use_container_width=True,
                            hide_index=True
                        )

                        st.metric(
                            "Observations Used",
                            two_way_result["Observations"]
                        )

                        st.caption(
                            f"Significance level: α = {two_way_alpha}. "
                            "The interaction tests whether the effect of one "
                            "factor depends on the level of the other factor."
                        )

                        for _, row in anova_table.iterrows():

                            source = format_anova_source(row["Source"])
                            p_value = row["P-Value"]

                            if pd.isna(p_value):
                                continue

                            if p_value < two_way_alpha:
                                st.info(
                                    f"**{source}** is significant "
                                    f"(p = {p_value:.6f})."
                                )
                            else:
                                st.info(
                                    f"**{source}** is not significant "
                                    f"(p = {p_value:.6f})."
                                )


    except Exception as e:

        st.error(
            f"Unable to process the dataset: {e}"
                    )
