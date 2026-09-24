import pandas as pd
import streamlit as st

from src.data_loader import (
    load_dataset,
    validate_dataset,
    get_dataset_summary,
)

from src.statistics import (
    get_numeric_statistics,
    detect_outliers,
    calculate_correlation,
    one_sample_t_test,
    two_sample_t_test,
    one_way_anova,
    two_way_anova,
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

        numeric_columns = get_numeric_columns(df)


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


        if len(numeric_columns) == 0:

            st.info(
                "A numerical column is required "
                "for two-sample testing."
            )

        else:

            possible_group_columns = [
                column
                for column in df.columns
                if df[column].nunique(dropna=True) >= 2
            ]


            if not possible_group_columns:

                st.info(
                    "No suitable grouping column was found."
                )

            else:

                group_column = st.selectbox(
                    "Select the grouping column",
                    possible_group_columns,
                    key="group_column"
                )


                group_values = (
                    df[group_column]
                    .dropna()
                    .unique()
                    .tolist()
                )


                if len(group_values) < 2:

                    st.info(
                        "The selected grouping column "
                        "must contain at least two groups."
                    )

                else:

                    value_column = st.selectbox(
                        "Select the numerical variable",
                        numeric_columns,
                        key="two_sample_value"
                    )


                    group1 = st.selectbox(
                        "Select Group 1",
                        group_values,
                        key="group1"
                    )


                    remaining_groups = [
                        value
                        for value in group_values
                        if value != group1
                    ]


                    group2 = st.selectbox(
                        "Select Group 2",
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
                        "Run Two-Sample t-Test"
                    ):

                        two_sample_result = two_sample_t_test(
                            df,
                            value_column,
                            group_column,
                            group1,
                            group2
                        )


                        if two_sample_result is None:

                            st.error(
                                "Each selected group must have "
                                "at least two valid numerical observations."
                            )

                        else:

                            result_col1, result_col2 = st.columns(2)


                            with result_col1:

                                st.metric(
                                    f"{group1} Mean",
                                    f"{two_sample_result['Group 1 Mean']:.4f}"
                                )

                                st.metric(
                                    f"{group1} Sample Size",
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
                                    f"{group2} Mean",
                                    f"{two_sample_result['Group 2 Mean']:.4f}"
                                )

                                st.metric(
                                    f"{group2} Sample Size",
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


                            if (
                                two_sample_result["P-Value"]
                                < two_sample_alpha
                            ):

                                st.warning(
                                    f"Reject the null hypothesis at "
                                    f"α = {two_sample_alpha}. "
                                    "The sample provides evidence "
                                    "that the two population means differ."
                                )

                            else:

                                st.success(
                                    f"Fail to reject the null hypothesis "
                                    f"at α = {two_sample_alpha}. "
                                    "The sample does not provide sufficient "
                                    "evidence that the two population means differ."
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
                if df[column].nunique(dropna=True) >= 3
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


                        if anova_result["P-Value"] < anova_alpha:

                            st.warning(
                                f"Reject the null hypothesis at "
                                f"α = {anova_alpha}. "
                                "The sample provides evidence that "
                                "at least one population mean differs."
                            )

                        else:

                            st.success(
                                f"Fail to reject the null hypothesis "
                                f"at α = {anova_alpha}. "
                                "The sample does not provide sufficient "
                                "evidence that the population means differ."
                            )


                        st.caption(
                            "ANOVA tests whether all group means are equal. "
                            "A significant result indicates that at least "
                            "one mean differs, but does not identify which "
                            "groups differ."
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

                        display_table = anova_table.rename(
                            columns={
                                "Source": "Effect",
                                "Sum of Squares": "Sum of Squares",
                                "Degrees of Freedom": "df",
                                "F-Statistic": "F",
                                "P-Value": "p-value",
                            }
                        ).copy()

                        display_table["Effect"] = display_table["Effect"].apply(
                            format_anova_source
                        )

                        display_table["df"] = display_table["df"].map(
                            lambda value: f"{value:.0f}"
                            if pd.notna(value) else ""
                        )

                        display_table["F"] = display_table["F"].map(
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
                                ["Effect", "Sum of Squares", "df", "F", "p-value"]
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
