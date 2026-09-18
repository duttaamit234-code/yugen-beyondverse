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


    except Exception as e:

        st.error(
            f"Unable to process the dataset: {e}"
                    )
