import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# StatsYuri web build: keep the statistical modules synchronized with this app.
# Assumption diagnostics: Shapiro-Wilk and Levene tests are provided by src.statistics.
# Deployment sync: statistical feature modules are synchronized before app startup.
from scipy import stats

from src.data_loader import (
    load_dataset,
    validate_dataset,
    get_dataset_summary,
)

from src.statistics import (
    get_numeric_statistics,
    calculate_confidence_intervals,
    simple_linear_regression,
    wilcoxon_signed_rank_test,
    mann_whitney_u_test,
    shapiro_wilk_test,
    levene_variance_test,
    detect_outliers,
    calculate_correlation,
    one_sample_t_test,
    two_sample_t_test,
    two_sample_t_test_wide,
    one_way_anova,
    two_way_anova,
    chi_square_goodness_of_fit,
    chi_square_independence,
    cohens_d_independent,
    one_way_eta_squared,
    cramers_v,
    tukey_hsd_posthoc,
    kruskal_wallis_test,
    kruskal_wallis_posthoc,
    regression_diagnostics,
    multiple_linear_regression,
)

from src.visualization import (
    get_numeric_columns,
    create_histogram,
    create_box_plot,
    create_correlation_heatmap,
)

from src.question_engine import interpret_question
from src.ocr_table import extract_table_from_image, extract_tables_from_scanned_pdf
from src.pdf_detector import detect_pdf, extract_pdf_tables

from src.decision_engine import (
    recommend_analyses,
    summarize_recommendations,
    decision_from_result,
    interpret_correlation,
    interpret_effect_size,
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
    type=["csv", "xlsx", "xls", "png", "jpg", "jpeg", "pdf"],
    help="CSV/Excel files are loaded directly. PNG/JPG images are converted into an editable table using OCR before analysis.",
)


if uploaded_file is not None:

    try:
        uploaded_extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

        if uploaded_extension == "pdf":
            pdf_info = detect_pdf(uploaded_file)

            st.write("### PDF Detection")
            st.dataframe(
                pd.DataFrame(pdf_info["Page Details"]),
                use_container_width=True,
                hide_index=True,
            )

            if pdf_info["Document Type"] == "scanned_pdf":
                st.warning(
                    "This PDF appears to be scanned or image-only. "
                    "StatsYuri will render its pages and run OCR."
                )

                scanned_results = extract_tables_from_scanned_pdf(uploaded_file)

                valid_results = [
                    item for item in scanned_results
                    if item["dataframe"] is not None
                ]

                if not valid_results:
                    st.error(
                        "OCR could not extract a reliable table from the scanned PDF."
                    )
                    st.stop()

                st.write("### Scanned PDF OCR Results")

                confidence_table = pd.DataFrame([
                    {
                        "Page": item["page"],
                        "OCR Confidence": f"{item['confidence']:.1f}%",
                    }
                    for item in scanned_results
                ])
                st.dataframe(
                    confidence_table,
                    use_container_width=True,
                    hide_index=True,
                )

                df = pd.concat(
                    [item["dataframe"] for item in valid_results],
                    ignore_index=True,
                )

                st.write("### OCR Table Review")
                st.caption(
                    "Review and correct the OCR table before analysis."
                )

                df = st.data_editor(
                    df.drop(columns=["__PDF_Page"], errors="ignore"),
                    use_container_width=True,
                    num_rows="dynamic",
                    key="scanned_pdf_ocr_editor",
                ).copy()

                st.success(
                    f"OCR extracted usable tables from "
                    f"{len(valid_results)} of {len(scanned_results)} page(s)."
                )

            else:
                pdf_tables = extract_pdf_tables(uploaded_file)

                if not pdf_tables:
                    st.warning(
                        "PDF text was detected, but no reliable table was detected. "
                        "Please convert the relevant table page to PNG/JPG for OCR."
                    )
                    st.stop()

                df = pd.concat(pdf_tables, ignore_index=True)
                df = df.drop(columns=["__PDF_Page", "__PDF_Table"], errors="ignore")

                st.success(
                    f"Detected {len(pdf_tables)} table(s) across "
                    f"{pdf_info['Pages']} page(s)."
                )

                st.write("### PDF Table Review")
                st.caption(
                    "Review the extracted PDF table before statistical analysis."
                )

                df = st.data_editor(
                    df,
                    use_container_width=True,
                    num_rows="dynamic",
                    key="pdf_table_editor",
                ).copy()

        elif uploaded_extension in {"png", "jpg", "jpeg"}:
            st.info(
                "Image detected. StatsYuri is extracting the table with OCR. "
                "Review the extracted table before using statistical analysis."
            )

            df, ocr_confidence = extract_table_from_image(uploaded_file)

            st.success(
                f"OCR table extraction completed. Average OCR confidence: "
                f"{ocr_confidence:.1f}%"
            )

            st.write("### OCR Editable Table Review")
            st.caption(
                "OCR is not guaranteed to be perfect. Correct any cells or "
                "column names here before continuing with analysis."
            )

            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                key="ocr_table_editor",
            )

            df = edited_df.copy()

            if st.checkbox(
                "Use OCR table for analysis",
                value=True,
                key="ocr_confirmed",
            ):
                st.success(
                    "OCR table accepted. The edited table will be used by "
                    "the existing StatsYuri analysis pipeline."
                )
            else:
                st.stop()

        else:
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


        st.subheader("Data Cleaning")

        st.write(
            "Create a cleaned copy of the uploaded dataset without changing "
            "the original upload."
        )

        cleaning_option = st.selectbox(
            "Missing-value handling",
            [
                "Keep missing values",
                "Drop rows with missing values",
                "Fill numerical missing values with the column median",
            ],
            key="cleaning_option"
        )

        remove_duplicates = st.checkbox(
            "Remove duplicate rows",
            value=False,
            key="cleaning_duplicates"
        )

        cleaned_df = df.copy()

        if cleaning_option == "Drop rows with missing values":
            cleaned_df = cleaned_df.dropna()
        elif cleaning_option == "Fill numerical missing values with the column median":
            for column in cleaned_df.select_dtypes(include="number").columns:
                cleaned_df[column] = cleaned_df[column].fillna(
                    cleaned_df[column].median()
                )

        duplicate_count = int(len(cleaned_df) - len(cleaned_df.drop_duplicates()))

        if remove_duplicates:
            cleaned_df = cleaned_df.drop_duplicates()

        cleaning_summary = pd.DataFrame({
            "Metric": [
                "Original rows",
                "Cleaned rows",
                "Rows removed",
                "Original missing values",
                "Cleaned missing values",
                "Duplicate rows removed",
            ],
            "Value": [
                len(df),
                len(cleaned_df),
                len(df) - len(cleaned_df),
                int(df.isna().sum().sum()),
                int(cleaned_df.isna().sum().sum()),
                duplicate_count if remove_duplicates else 0,
            ],
        })

        st.dataframe(
            cleaning_summary,
            use_container_width=True,
            hide_index=True
        )

        st.write("### Cleaned Dataset Preview")
        st.dataframe(
            cleaned_df.head(20),
            use_container_width=True
        )

        st.download_button(
            "Download Cleaned Dataset",
            data=cleaned_df.to_csv(index=False).encode("utf-8"),
            file_name="statsyuri_cleaned_dataset.csv",
            mime="text/csv"
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


        st.subheader("Automatic Analysis")

        st.write(
            "StatsYuri detects common data structures and suggests analyses "
            "without requiring you to manually choose a test. "
            "Recommendations describe statistical structure, not the "
            "research question or study design."
        )

        automatic_alpha = st.selectbox(
            "Automatic Analysis Significance Level (α)",
            [0.01, 0.05, 0.10],
            index=1,
            key="automatic_analysis_alpha"
        )

        recommendations = recommend_analyses(df)
        recommendation_table = summarize_recommendations(recommendations)

        if recommendation_table.empty:
            st.info(
                "No common analysis structure could be identified from the "
                "current dataset."
            )
        else:
            st.write("### Detected Structures and Suggested Analyses")
            st.dataframe(
                recommendation_table,
                use_container_width=True,
                hide_index=True
            )

            st.write("### Automatic Results")

            for index, recommendation in enumerate(recommendations[:6]):
                analysis_name = recommendation["Analysis"]
                variable_text = ", ".join(
                    str(recommendation[key])
                    for key in (
                        "Response",
                        "Grouping",
                        "Variable 1",
                        "Variable 2",
                    )
                    if key in recommendation
                )

                with st.expander(
                    f"{analysis_name}: {variable_text}",
                    expanded=index == 0
                ):
                    result = None

                    if analysis_name == "Welch two-sample t-test":
                        group_column = recommendation["Grouping"]
                        response_column = recommendation["Response"]
                        groups = (
                            df[group_column]
                            .dropna()
                            .unique()
                            .tolist()
                        )

                        if len(groups) == 2:
                            result = two_sample_t_test(
                                df,
                                response_column,
                                group_column,
                                groups[0],
                                groups[1]
                            )

                            if result is not None:
                                decision = decision_from_result(
                                    result["P-Value"],
                                    automatic_alpha,
                                    "Welch two-sample t-test"
                                )

                                table = pd.DataFrame({
                                    "Statistic": [
                                        "Group 1 Mean",
                                        "Group 2 Mean",
                                        "Mean Difference",
                                        "t-Statistic",
                                        "Degrees of Freedom",
                                        "p-value",
                                        "Decision",
                                    ],
                                    "Value": [
                                        result["Group 1 Mean"],
                                        result["Group 2 Mean"],
                                        result["Mean Difference"],
                                        result["T-Statistic"],
                                        result["Degrees of Freedom"],
                                        result["P-Value"],
                                        decision["Decision"],
                                    ],
                                })

                                st.dataframe(
                                    table,
                                    use_container_width=True,
                                    hide_index=True
                                )
                                st.write(
                                    f"**Compare:** {decision['Comparison']}"
                                )
                                st.write(
                                    f"**Interpret:** {decision['Interpretation']}"
                                )

                                effect = cohens_d_independent(
                                    pd.DataFrame({
                                        "Group 1": df.loc[
                                            df[group_column] == groups[0],
                                            response_column
                                        ],
                                        "Group 2": df.loc[
                                            df[group_column] == groups[1],
                                            response_column
                                        ]
                                    }),
                                    "Group 1",
                                    "Group 2"
                                )
                                if effect is not None:
                                    st.caption(
                                        interpret_effect_size(
                                            "Cohen's d",
                                            effect["Cohen's d"]
                                        )
                                    )

                    elif analysis_name == "One-way ANOVA":
                        result = one_way_anova(
                            df,
                            recommendation["Response"],
                            recommendation["Grouping"]
                        )

                        if result is not None:
                            decision = decision_from_result(
                                result["P-Value"],
                                automatic_alpha,
                                "One-way ANOVA"
                            )

                            eta_squared = one_way_eta_squared(result)

                            table = pd.DataFrame({
                                "Statistic": [
                                    "F-Statistic",
                                    "Between-Group DF",
                                    "Within-Group DF",
                                    "p-value",
                                    "Decision",
                                ],
                                "Value": [
                                    result["F-Statistic"],
                                    result["Between-Group DF"],
                                    result["Within-Group DF"],
                                    result["P-Value"],
                                    decision["Decision"],
                                ],
                            })

                            st.dataframe(
                                table,
                                use_container_width=True,
                                hide_index=True
                            )
                            st.write(
                                f"**Compare:** {decision['Comparison']}"
                            )
                            st.write(
                                f"**Interpret:** {decision['Interpretation']}"
                            )

                            if eta_squared is not None:
                                st.caption(
                                    interpret_effect_size(
                                        "Eta squared",
                                        eta_squared
                                    )
                                )

                    elif analysis_name == (
                        "Pearson correlation + simple linear regression"
                    ):
                        variable_1 = recommendation["Variable 1"]
                        variable_2 = recommendation["Variable 2"]
                        correlation_matrix = calculate_correlation(df)
                        r_value = correlation_matrix.loc[
                            variable_1,
                            variable_2
                        ]

                        regression_result = simple_linear_regression(
                            df,
                            variable_1,
                            variable_2
                        )

                        st.write(
                            f"**Correlation:** {interpret_correlation(r_value)}"
                        )

                        if regression_result is not None:
                            decision = decision_from_result(
                                regression_result["Slope P-Value"],
                                automatic_alpha,
                                "Simple linear regression"
                            )

                            table = pd.DataFrame({
                                "Statistic": [
                                    "Pearson r",
                                    "R²",
                                    "Slope",
                                    "Slope p-value",
                                    "Decision",
                                ],
                                "Value": [
                                    r_value,
                                    regression_result["R-Squared"],
                                    regression_result["Slope"],
                                    regression_result["Slope P-Value"],
                                    decision["Decision"],
                                ],
                            })

                            st.dataframe(
                                table,
                                use_container_width=True,
                                hide_index=True
                            )
                            st.write(
                                f"**Compare:** {decision['Comparison']}"
                            )
                            st.write(
                                f"**Interpret:** {decision['Interpretation']}"
                            )

                    elif analysis_name == "Chi-square test of independence":
                        result = chi_square_independence(
                            df,
                            recommendation["Variable 1"],
                            recommendation["Variable 2"]
                        )

                        if result is not None:
                            decision = decision_from_result(
                                result["P-Value"],
                                automatic_alpha,
                                "Chi-square test of independence"
                            )

                            table = pd.DataFrame({
                                "Statistic": [
                                    "Chi-square",
                                    "Degrees of Freedom",
                                    "Observations",
                                    "p-value",
                                    "Decision",
                                ],
                                "Value": [
                                    result["Chi-Square"],
                                    result["Degrees of Freedom"],
                                    result["Observations"],
                                    result["P-Value"],
                                    decision["Decision"],
                                ],
                            })

                            st.dataframe(
                                table,
                                use_container_width=True,
                                hide_index=True
                            )
                            st.write(
                                f"**Compare:** {decision['Comparison']}"
                            )
                            st.write(
                                f"**Interpret:** {decision['Interpretation']}"
                            )

                            cramers = cramers_v(
                                df,
                                recommendation["Variable 1"],
                                recommendation["Variable 2"]
                            )
                            if cramers is not None:
                                st.caption(
                                    interpret_effect_size(
                                        "Cramer's V",
                                        cramers
                                    )
                                )

                    if result is None and analysis_name not in {
                        "Pearson correlation + simple linear regression"
                    }:
                        st.info(
                            "The detected structure did not contain enough "
                            "valid observations to calculate this result."
                        )


        st.subheader("Question-Aware Analysis")

        st.write(
            "Describe what you want to find out in plain language. "
            "StatsYuri will map the question to the current dataset and "
            "show its interpretation before any analysis is run."
        )

        research_question = st.text_input(
            "Research question",
            placeholder="Example: Does fertilizer affect crop yield?",
            key="research_question",
        )

        if research_question.strip():
            question_result = interpret_question(df, research_question)

            status = question_result["status"]
            confidence = question_result["confidence"]

            if status == "ready":
                st.success(
                    f"Question mapped successfully. Confidence: {confidence:.0%}"
                )
            elif status == "ambiguous":
                st.warning(
                    f"More than one interpretation was found. "
                    f"Confidence: {confidence:.0%}"
                )
            else:
                st.info(
                    f"More information is needed to map the question. "
                    f"Confidence: {confidence:.0%}"
                )

            st.write(f"**Detected intent:** {question_result['intent'] or 'Not identified'}")
            st.write(f"**Reason:** {question_result['reason']}")

            if question_result["matched_columns"]:
                matched_table = pd.DataFrame(
                    [
                        {
                            "Column": item["column"],
                            "Match Score": item["score"],
                            "Question Evidence": item["evidence"],
                        }
                        for item in question_result["matched_columns"]
                    ]
                )
                st.write("### Matched Dataset Columns")
                st.dataframe(
                    matched_table,
                    use_container_width=True,
                    hide_index=True,
                )

            if question_result["candidates"]:
                st.write("### Candidate Analysis")
                candidate_table = pd.DataFrame(question_result["candidates"])
                st.dataframe(
                    candidate_table,
                    use_container_width=True,
                    hide_index=True,
                )

                if status == "ready":
                    st.caption(
                        "The question engine identifies the analysis. "
                        "StatsYuri then validates the data, calculates the test, "
                        "compares the result with α, makes the statistical decision, "
                        "and explains the result."
                    )

                    candidate = question_result["candidates"][0]

                    if st.button(
                        "Answer Research Question",
                        key="answer_research_question",
                        type="primary",
                    ):
                        analysis_name = candidate["analysis"]
                        result = None
                        test_name = analysis_name

                        if analysis_name == "Welch two-sample t-test":
                            groups = (
                                df[candidate["grouping"]]
                                .dropna()
                                .unique()
                                .tolist()
                            )
                            if len(groups) == 2:
                                result = two_sample_t_test(
                                    df,
                                    candidate["response"],
                                    candidate["grouping"],
                                    groups[0],
                                    groups[1],
                                )
                                test_name = "Welch two-sample t-test"

                        elif analysis_name == "One-way ANOVA":
                            result = one_way_anova(
                                df,
                                candidate["response"],
                                candidate["grouping"],
                            )
                            test_name = "One-way ANOVA"

                        elif analysis_name == "Chi-square test of independence":
                            result = chi_square_independence(
                                df,
                                candidate["variable_1"],
                                candidate["variable_2"],
                            )
                            test_name = "Chi-square test of independence"

                        elif analysis_name == "Pearson correlation + simple linear regression":
                            x = candidate["variable_1"]
                            y = candidate["variable_2"]
                            pair = df[[x, y]].apply(
                                pd.to_numeric,
                                errors="coerce",
                            ).dropna()

                            if len(pair) >= 3 and pair[x].nunique() > 1 and pair[y].nunique() > 1:
                                correlation, correlation_p = stats.pearsonr(
                                    pair[x],
                                    pair[y],
                                )
                                regression = simple_linear_regression(df, x, y)
                                result = {
                                    "Variable 1": x,
                                    "Variable 2": y,
                                    "Observations": len(pair),
                                    "Pearson r": correlation,
                                    "P-Value": correlation_p,
                                    "Regression": regression,
                                }
                            test_name = "Pearson correlation"

                        elif analysis_name == "Simple linear regression":
                            result = simple_linear_regression(
                                df,
                                candidate["predictor"],
                                candidate["response"],
                            )
                            test_name = "Simple linear regression"

                        if result is None:
                            st.error(
                                "StatsYuri could not execute this analysis on the "
                                "current data. Check the matched columns and sample sizes."
                            )
                        else:
                            st.write("### Answer")

                            result_rows = []
                            for key, value in result.items():
                                if isinstance(value, (list, tuple)):
                                    continue
                                if isinstance(value, dict):
                                    continue
                                result_rows.append({
                                    "Measure": key,
                                    "Value": value,
                                })

                            if result_rows:
                                st.dataframe(
                                    pd.DataFrame(result_rows),
                                    use_container_width=True,
                                    hide_index=True,
                                )

                            p_value = result.get("P-Value")

                            if p_value is not None:
                                decision = decision_from_result(
                                    p_value,
                                    alpha=0.05,
                                    test_name=test_name,
                                )

                                st.write("### Statistical Decision")
                                st.dataframe(
                                    pd.DataFrame([decision]),
                                    use_container_width=True,
                                    hide_index=True,
                                )

                                if p_value < 0.05:
                                    st.success(
                                        "At α = 0.05, the result is statistically significant."
                                    )
                                else:
                                    st.info(
                                        "At α = 0.05, the result is not statistically significant."
                                    )

                                st.caption(
                                    "Interpret the statistical result in the context "
                                    "of the study design. Statistical significance does "
                                    "not by itself establish causation."
                                )

                            if test_name == "Pearson correlation":
                                st.write(
                                    "**Interpretation:** "
                                    + interpret_correlation(
                                        result["Pearson r"]
                                    )
                                )

                            elif test_name == "Simple linear regression":
                                slope = result.get("Slope")
                                r_squared = result.get("R-Squared")
                                if slope is not None and r_squared is not None:
                                    st.write(
                                        f"**Interpretation:** The fitted relationship "
                                        f"has a slope of {slope:.4f} and explains "
                                        f"{r_squared:.2%} of the variation in the response "
                                        f"within this sample."
                                    )

                            elif test_name == "Welch two-sample t-test":
                                st.write(
                                    f"**Interpretation:** The observed mean difference "
                                    f"between {result['Group 1']} and {result['Group 2']} "
                                    f"is {result['Mean Difference']:.4f}."
                                )

                            elif test_name == "One-way ANOVA":
                                means = ", ".join(
                                    f"{group}: {mean:.2f}"
                                    for group, mean in zip(
                                        result["Group Labels"],
                                        result["Group Means"],
                                    )
                                )
                                st.write(
                                    f"**Interpretation:** The observed group means are "
                                    f"{means}. ANOVA tests whether at least one group mean "
                                    f"differs from the others."
                                )

                            elif test_name == "Chi-square test of independence":
                                st.write(
                                    "**Interpretation:** The chi-square test evaluates "
                                    "whether the two categorical variables are statistically "
                                    "independent in this sample."
                                )

                            if result.get("Regression"):
                                st.write("### Regression Result")
                                regression = result["Regression"]
                                regression_rows = [
                                    {"Measure": key, "Value": value}
                                    for key, value in regression.items()
                                    if not isinstance(value, (list, tuple, dict))
                                ]
                                st.dataframe(
                                    pd.DataFrame(regression_rows),
                                    use_container_width=True,
                                    hide_index=True,
                                )

        st.subheader("Assumption Checking")

        st.write(
            "Check common assumptions used by parametric methods. "
            "These diagnostics support, but do not replace, knowledge "
            "of the study design."
        )

        if numeric_columns:

            st.write("### Normality Check")

            normality_column = st.selectbox(
                "Select a numerical variable",
                numeric_columns,
                key="assumption_normality_column"
            )

            normality_alpha = st.selectbox(
                "Normality Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="assumption_normality_alpha"
            )

            normality_result = shapiro_wilk_test(
                df,
                normality_column
            )

            if normality_result is None:
                st.info(
                    "At least 3 valid observations are required "
                    "for the Shapiro-Wilk test."
                )
            else:
                normality_decision = (
                    "Normality rejected"
                    if normality_result["P-Value"] < normality_alpha
                    else "Normality not rejected"
                )

                normality_table = pd.DataFrame({
                    "Variable": [normality_result["Variable"]],
                    "n": [normality_result["Sample Size"]],
                    "W": [normality_result["W-Statistic"]],
                    "p-value": [normality_result["P-Value"]],
                    "Decision": [normality_decision],
                })

                st.dataframe(
                    normality_table.style.format({
                        "W": "{:.4f}",
                        "p-value": lambda value:
                            "<0.000001"
                            if value < 0.000001
                            else f"{value:.6f}",
                    }),
                    use_container_width=True,
                    hide_index=True
                )

                if normality_result["P-Value"] < normality_alpha:
                    st.warning(
                        "The Shapiro-Wilk test provides evidence "
                        "against normality at the selected level."
                    )
                else:
                    st.success(
                        "The Shapiro-Wilk test does not provide "
                        "sufficient evidence to reject normality."
                    )

            st.write("### Equal Variance Check")

            categorical_columns = [
                column
                for column in df.columns
                if not pd.api.types.is_numeric_dtype(df[column])
                and df[column].nunique(dropna=True) >= 2
            ]

            if not categorical_columns:
                st.info(
                    "No suitable categorical grouping variable "
                    "was found for Levene's test."
                )
            else:
                levene_group = st.selectbox(
                    "Grouping variable",
                    categorical_columns,
                    key="assumption_levene_group"
                )

                levene_value = st.selectbox(
                    "Numerical response",
                    numeric_columns,
                    key="assumption_levene_value"
                )

                levene_alpha = st.selectbox(
                    "Equal Variance Significance Level (α)",
                    [0.01, 0.05, 0.10],
                    index=1,
                    key="assumption_levene_alpha"
                )

                levene_result = levene_variance_test(
                    df,
                    levene_value,
                    levene_group
                )

                if levene_result is None:
                    st.info(
                        "At least two groups with at least two valid "
                        "observations each are required."
                    )
                else:
                    levene_decision = (
                        "Unequal variances detected"
                        if levene_result["P-Value"] < levene_alpha
                        else "Equal variance assumption not rejected"
                    )

                    levene_table = pd.DataFrame({
                        "Response": [levene_result["Value Variable"]],
                        "Groups": [levene_result["Groups"]],
                        "Levene F": [levene_result["F-Statistic"]],
                        "p-value": [levene_result["P-Value"]],
                        "Decision": [levene_decision],
                    })

                    st.dataframe(
                        levene_table.style.format({
                            "Levene F": "{:.4f}",
                            "p-value": lambda value:
                                "<0.000001"
                                if value < 0.000001
                                else f"{value:.6f}",
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    if levene_result["P-Value"] < levene_alpha:
                        st.warning(
                            "The equal-variance assumption is not "
                            "supported by Levene's test. Consider a "
                            "method that does not require equal variances, "
                            "where appropriate."
                        )
                    else:
                        st.success(
                            "Levene's test does not provide sufficient "
                            "evidence against equal variances."
                        )

        else:
            st.info(
                "Numerical variables are required for assumption checking."
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


        st.subheader("Analysis Report")

        report_lines = [
            "StatsYuri Analysis Report",
            "=========================",
            "",
            f"Rows: {summary['rows']}",
            f"Columns: {summary['columns']}",
            f"Missing values: {summary['missing_values']}",
            "",
            "Descriptive Statistics",
            "----------------------",
        ]

        report_lines.append(
            statistics.to_string(index=False)
            if not statistics.empty
            else "No numerical variables available."
        )

        report_lines.extend([
            "",
            "Outlier Summary",
            "---------------",
            outlier_results.to_string(index=False)
            if not outlier_results.empty
            else "No numerical variables available.",
            "",
            "Notes",
            "-----",
            "Interpret statistical results together with study design, "
            "assumptions, effect sizes, and practical context.",
        ])

        analysis_report = "\n".join(report_lines)

        st.download_button(
            "Download Analysis Report",
            data=analysis_report.encode("utf-8"),
            file_name="statsyuri_analysis_report.txt",
            mime="text/plain"
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


        st.subheader("Non-Parametric Tests")

        st.write(
            "Perform distribution-free hypothesis tests when the "
            "assumptions of parametric tests may not be appropriate."
        )

        st.write("### Wilcoxon Signed-Rank Test")

        st.caption(
            "One-sample non-parametric test for a hypothesized population median."
        )

        if not numeric_columns:

            st.info(
                "At least one numerical column is required."
            )

        else:

            wilcoxon_column = st.selectbox(
                "Select numerical variable",
                numeric_columns,
                key="wilcoxon_column"
            )

            wilcoxon_median = st.number_input(
                "Hypothesized Median",
                value=0.0,
                step=1.0,
                key="wilcoxon_median"
            )

            wilcoxon_alpha = st.selectbox(
                "Wilcoxon Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="wilcoxon_alpha"
            )

            if st.button(
                "Run Wilcoxon Signed-Rank Test",
                key="run_wilcoxon"
            ):

                wilcoxon_result = wilcoxon_signed_rank_test(
                    df,
                    wilcoxon_column,
                    wilcoxon_median
                )

                if wilcoxon_result is None:

                    st.error(
                        "At least two non-zero valid differences are "
                        "required for the Wilcoxon signed-rank test."
                    )

                else:

                    wilcoxon_result_table = pd.DataFrame({
                        "Statistic": [
                            "Sample Size",
                            "Sample Median",
                            "Hypothesized Median",
                            "W-Statistic",
                            "p-value",
                        ],
                        "Value": [
                            wilcoxon_result["Sample Size"],
                            wilcoxon_result["Sample Median"],
                            wilcoxon_result["Hypothesized Median"],
                            wilcoxon_result["W-Statistic"],
                            wilcoxon_result["P-Value"],
                        ],
                    })

                    st.dataframe(
                        wilcoxon_result_table.style.format({
                            "Value": "{:.6f}"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    if wilcoxon_result["P-Value"] < wilcoxon_alpha:

                        st.warning(
                            f"p = {wilcoxon_result['P-Value']:.6f} < "
                            f"α = {wilcoxon_alpha:.2f}. "
                            "Reject the null hypothesis."
                        )

                        st.write(
                            "### Interpretation"
                        )

                        st.write(
                            "There is statistically significant evidence "
                            "that the population median differs from the "
                            "hypothesized median."
                        )

                    else:

                        st.success(
                            f"p = {wilcoxon_result['P-Value']:.6f} ≥ "
                            f"α = {wilcoxon_alpha:.2f}. "
                            "Fail to reject the null hypothesis."
                        )

                        st.write(
                            "### Interpretation"
                        )

                        st.write(
                            "There is insufficient statistical evidence "
                            "that the population median differs from the "
                            "hypothesized median."
                        )

        st.write("### Mann-Whitney U Test")

        st.caption(
            "Two-sample non-parametric test for comparing two independent groups."
        )

        if len(numeric_columns) < 2:

            st.info(
                "At least two numerical columns are required."
            )

        else:

            mann_col1, mann_col2 = st.columns(2)

            with mann_col1:
                mann_group1 = st.selectbox(
                    "Numerical Group 1",
                    numeric_columns,
                    key="mann_group1"
                )

            remaining_mann_columns = [
                column
                for column in numeric_columns
                if column != mann_group1
            ]

            with mann_col2:
                mann_group2 = st.selectbox(
                    "Numerical Group 2",
                    remaining_mann_columns,
                    key="mann_group2"
                )

            mann_alpha = st.selectbox(
                "Mann-Whitney Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="mann_alpha"
            )

            if st.button(
                "Run Mann-Whitney U Test",
                key="run_mann_whitney"
            ):

                mann_result = mann_whitney_u_test(
                    df,
                    mann_group1,
                    mann_group2
                )

                if mann_result is None:

                    st.error(
                        "Each group must contain at least two valid observations."
                    )

                else:

                    mann_result_table = pd.DataFrame({
                        "Statistic": [
                            "Group 1 Median",
                            "Group 2 Median",
                            "Group 1 Size",
                            "Group 2 Size",
                            "U-Statistic",
                            "p-value",
                        ],
                        "Value": [
                            mann_result["Group 1 Median"],
                            mann_result["Group 2 Median"],
                            mann_result["Group 1 Size"],
                            mann_result["Group 2 Size"],
                            mann_result["U-Statistic"],
                            mann_result["P-Value"],
                        ],
                    })

                    st.dataframe(
                        mann_result_table.style.format({
                            "Value": "{:.6f}"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    if mann_result["P-Value"] < mann_alpha:

                        st.warning(
                            f"p = {mann_result['P-Value']:.6f} < "
                            f"α = {mann_alpha:.2f}. "
                            "Reject the null hypothesis."
                        )

                        st.write("### Interpretation")

                        st.write(
                            "There is statistically significant evidence "
                            "that the two independent groups differ in "
                            "their distributions."
                        )

                    else:

                        st.success(
                            f"p = {mann_result['P-Value']:.6f} ≥ "
                            f"α = {mann_alpha:.2f}. "
                            "Fail to reject the null hypothesis."
                        )

                        st.write("### Interpretation")

                        st.write(
                            "There is insufficient statistical evidence "
                            "that the two independent groups differ in "
                            "their distributions."
                        )


        st.subheader("Kruskal-Wallis Test")

        st.write(
            "Non-parametric comparison of three or more independent groups."
        )

        if not numeric_columns:
            st.info("A numerical response variable is required.")
        else:
            kw_groups = [
                column for column in df.columns
                if not pd.api.types.is_numeric_dtype(df[column])
                and df[column].nunique(dropna=True) >= 3
            ]

            if not kw_groups:
                st.info(
                    "No categorical grouping variable with at least three "
                    "groups was found."
                )
            else:
                kw_group = st.selectbox(
                    "Kruskal-Wallis grouping variable",
                    kw_groups,
                    key="kw_group"
                )
                kw_value = st.selectbox(
                    "Kruskal-Wallis response",
                    numeric_columns,
                    key="kw_value"
                )
                kw_alpha = st.selectbox(
                    "Kruskal-Wallis Significance Level (α)",
                    [0.01, 0.05, 0.10],
                    index=1,
                    key="kw_alpha"
                )

                if st.button("Run Kruskal-Wallis Test"):
                    kw_result = kruskal_wallis_test(
                        df,
                        kw_value,
                        kw_group
                    )

                    if kw_result is None:
                        st.error(
                            "At least three groups with two or more valid "
                            "observations each are required."
                        )
                    else:
                        kw_table = pd.DataFrame({
                            "H-Statistic": [kw_result["H-Statistic"]],
                            "df": [kw_result["Degrees of Freedom"]],
                            "p-value": [kw_result["P-Value"]],
                            "Decision": [
                                "Significant"
                                if kw_result["P-Value"] < kw_alpha
                                else "Not Significant"
                            ],
                        })

                        st.dataframe(
                            kw_table.style.format({
                                "H-Statistic": "{:.4f}",
                                "p-value": lambda value:
                                    "<0.000001"
                                    if value < 0.000001
                                    else f"{value:.6f}",
                            }),
                            use_container_width=True,
                            hide_index=True
                        )

                        if kw_result["P-Value"] < kw_alpha:
                            st.warning(
                                "The group distributions differ significantly "
                                "at the selected significance level."
                            )
                        else:
                            st.success(
                                "There is insufficient evidence of a difference "
                                "among the group distributions."
                            )

                        if kw_result["P-Value"] < kw_alpha:
                            st.write("### Kruskal-Wallis Post-Hoc Comparisons")
                            st.caption(
                                "Pairwise Mann-Whitney U tests with Holm correction "
                                "identify which group pairs differ while controlling "
                                "the family-wise error rate."
                            )

                            kw_posthoc = kruskal_wallis_posthoc(
                                df,
                                kw_value,
                                kw_group,
                                alpha=kw_alpha
                            )

                            if kw_posthoc is not None:
                                st.dataframe(
                                    kw_posthoc.style.format({
                                        "U-Statistic": "{:.4f}",
                                        "Raw p-value": lambda value:
                                            "<0.000001"
                                            if value < 0.000001
                                            else f"{value:.6f}",
                                        "Adjusted p-value": lambda value:
                                            "<0.000001"
                                            if value < 0.000001
                                            else f"{value:.6f}",
                                    }),
                                    use_container_width=True,
                                    hide_index=True
                                )

                                st.info(
                                    "Post-hoc comparisons are interpreted only after "
                                    "the omnibus Kruskal-Wallis test indicates evidence "
                                    "of differences among groups."
                                )


        st.subheader("Regression Analysis")

        st.write(
            "Perform simple linear regression between two numerical "
            "variables."
        )

        if len(numeric_columns) < 2:

            st.info(
                "At least two numerical columns are required "
                "for regression analysis."
            )

        else:

            regression_x = st.selectbox(
                "Select predictor variable (X)",
                numeric_columns,
                key="regression_x"
            )

            regression_y_options = [
                column
                for column in numeric_columns
                if column != regression_x
            ]

            regression_y = st.selectbox(
                "Select response variable (Y)",
                regression_y_options,
                key="regression_y"
            )

            regression_alpha = st.selectbox(
                "Regression Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="regression_alpha"
            )

            if st.button("Run Linear Regression"):

                regression_result = simple_linear_regression(
                    df,
                    regression_x,
                    regression_y
                )

                if regression_result is None:

                    st.error(
                        "At least three valid observations and "
                        "variation in the predictor variable are required."
                    )

                else:

                    st.write("### Regression Equation")

                    st.code(
                        regression_result["Equation"]
                    )

                    result_col1, result_col2 = st.columns(2)

                    with result_col1:

                        st.metric(
                            "Slope",
                            f"{regression_result['Slope']:.4f}"
                        )

                        st.metric(
                            "Intercept",
                            f"{regression_result['Intercept']:.4f}"
                        )

                        st.metric(
                            "R",
                            f"{regression_result['R']:.4f}"
                        )

                        st.metric(
                            "R²",
                            f"{regression_result['R-Squared']:.4f}"
                        )

                    with result_col2:

                        st.metric(
                            "Slope P-Value",
                            f"{regression_result['Slope P-Value']:.6f}"
                        )

                        st.metric(
                            "Standard Error",
                            f"{regression_result['Standard Error']:.4f}"
                        )

                        st.metric(
                            "Observations",
                            regression_result["Observations"]
                        )

                    regression_result_table = pd.DataFrame({
                        "Statistic": [
                            "Slope",
                            "Intercept",
                            "R",
                            "R²",
                            "Standard Error",
                            "Slope p-value",
                        ],
                        "Value": [
                            regression_result["Slope"],
                            regression_result["Intercept"],
                            regression_result["R"],
                            regression_result["R-Squared"],
                            regression_result["Standard Error"],
                            regression_result["Slope P-Value"],
                        ],
                    })

                    st.dataframe(
                        regression_result_table.style.format({
                            "Value": "{:.6f}"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    if regression_result["Slope P-Value"] < regression_alpha:

                        st.warning(
                            f"The slope is statistically significant at "
                            f"α = {regression_alpha:.2f} "
                            f"(p = {regression_result['Slope P-Value']:.6f})."
                        )

                        st.write(
                            "### Interpretation"
                        )

                        st.write(
                            f"For each one-unit increase in "
                            f"{regression_x}, the predicted value of "
                            f"{regression_y} changes by approximately "
                            f"{regression_result['Slope']:.4f} units. "
                            "The slope is statistically significant, "
                            "indicating evidence of a linear association "
                            "between the two variables."
                        )

                    else:

                        st.success(
                            f"The slope is not statistically significant "
                            f"at α = {regression_alpha:.2f} "
                            f"(p = {regression_result['Slope P-Value']:.6f})."
                        )

                        st.write(
                            "### Interpretation"
                        )

                        st.write(
                            "There is insufficient statistical evidence "
                            "of a linear association between the selected "
                            "variables at the chosen significance level."
                        )



        if "regression_result" in locals() and regression_result is not None:
            st.write("### Regression Diagnostics")

            diagnostics = regression_diagnostics(
                df,
                regression_y,
                [regression_x]
            )

            if diagnostics is not None:
                diag_table = pd.DataFrame({
                    "Metric": [
                        "RMSE",
                        "MAE",
                        "Shapiro-Wilk p-value",
                        "Breusch-Pagan p-value",
                        "Durbin-Watson",
                    ],
                    "Value": [
                        diagnostics["RMSE"],
                        diagnostics["MAE"],
                        diagnostics["Shapiro p-value"],
                        diagnostics["Breusch-Pagan p-value"],
                        diagnostics["Durbin-Watson"],
                    ],
                })

                st.dataframe(
                    diag_table.style.format({
                        "Value": "{:.6f}"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

                fig, ax = plt.subplots()
                ax.scatter(
                    diagnostics["Fitted"],
                    diagnostics["Residuals"]
                )
                ax.axhline(0, linestyle="--")
                ax.set_xlabel("Fitted values")
                ax.set_ylabel("Residuals")
                ax.set_title("Residuals vs Fitted Values")
                st.pyplot(fig)
                plt.close(fig)

                st.caption(
                    "Residual diagnostics help assess prediction error and "
                    "common linear-model assumptions. A small p-value in the "
                    "Shapiro-Wilk or Breusch-Pagan test indicates evidence "
                    "against the corresponding assumption."
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


            st.write("### Correlation Interpretation")

            # Use the shared interpretation helper so the automatic and
            # manual correlation sections follow the same wording and thresholds.

            interpretation_rows = []

            for column_index, column in enumerate(correlation_matrix.columns):

                for other_column in correlation_matrix.columns[column_index + 1:]:

                    value = correlation_matrix.loc[
                        column,
                        other_column
                    ]

                    interpretation_rows.append({
                        "Variables": f"{column} ↔ {other_column}",
                        "Pearson r": value,
                        "Interpretation": interpret_correlation(value),
                    })

            if interpretation_rows:

                interpretation_table = pd.DataFrame(
                    interpretation_rows
                )

                st.dataframe(
                    interpretation_table.style.format({
                        "Pearson r": "{:.4f}"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

            st.caption(
                "Interpretation describes the strength and direction "
                "of linear association. Correlation does not establish "
                "causation."
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


        st.subheader("Multiple Linear Regression")

        st.write(
            "Model a numerical response using multiple numerical predictors."
        )

        if len(numeric_columns) < 3:
            st.info(
                "At least one response and two numerical predictors are "
                "recommended for multiple regression."
            )
        else:
            mlr_response = st.selectbox(
                "Response variable",
                numeric_columns,
                key="mlr_response"
            )

            mlr_predictors = st.multiselect(
                "Predictor variables",
                [column for column in numeric_columns if column != mlr_response],
                key="mlr_predictors"
            )

            mlr_alpha = st.selectbox(
                "Multiple Regression Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="mlr_alpha"
            )

            if st.button("Run Multiple Linear Regression"):
                mlr_result = multiple_linear_regression(
                    df,
                    mlr_response,
                    mlr_predictors
                )

                if mlr_result is None:
                    st.error(
                        "Select at least one predictor and provide enough "
                        "valid observations with variation."
                    )
                else:
                    st.write("### Model Summary")
                    mlr_summary = pd.DataFrame({
                        "Metric": [
                            "Observations",
                            "R²",
                            "Adjusted R²",
                            "F-Statistic",
                            "Model p-value",
                        ],
                        "Value": [
                            mlr_result["Observations"],
                            mlr_result["R-Squared"],
                            mlr_result["Adjusted R-Squared"],
                            mlr_result["F-Statistic"],
                            mlr_result["Model P-Value"],
                        ],
                    })

                    st.dataframe(
                        mlr_summary.style.format({
                            "Value": lambda value:
                                f"{value:.6f}"
                                if pd.notna(value) else "—"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    st.write("### Coefficients")
                    st.dataframe(
                        mlr_result["Coefficients"].style.format({
                            "Coefficient": "{:.6f}",
                            "Standard Error": "{:.6f}",
                            "t-Statistic": "{:.4f}",
                            "p-value": lambda value:
                                "<0.000001"
                                if value < 0.000001
                                else f"{value:.6f}",
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

                    if mlr_result["Model P-Value"] < mlr_alpha:
                        st.success(
                            "The overall regression model is statistically "
                            "significant at the selected level."
                        )
                    else:
                        st.info(
                            "The overall regression model is not statistically "
                            "significant at the selected level."
                        )

                    st.write("### Regression Diagnostics")

                    mlr_diagnostics = regression_diagnostics(
                        df,
                        mlr_response,
                        mlr_predictors
                    )

                    if mlr_diagnostics is not None:
                        mlr_diag_table = pd.DataFrame({
                            "Metric": [
                                "RMSE",
                                "MAE",
                                "Shapiro-Wilk p-value",
                                "Breusch-Pagan p-value",
                                "Durbin-Watson",
                            ],
                            "Value": [
                                mlr_diagnostics["RMSE"],
                                mlr_diagnostics["MAE"],
                                mlr_diagnostics["Shapiro p-value"],
                                mlr_diagnostics["Breusch-Pagan p-value"],
                                mlr_diagnostics["Durbin-Watson"],
                            ],
                        })

                        st.dataframe(
                            mlr_diag_table.style.format({
                                "Value": "{:.6f}"
                            }),
                            use_container_width=True,
                            hide_index=True
                        )

                        fig, ax = plt.subplots()
                        ax.scatter(
                            mlr_diagnostics["Fitted"],
                            mlr_diagnostics["Residuals"]
                        )
                        ax.axhline(0, linestyle="--")
                        ax.set_xlabel("Fitted values")
                        ax.set_ylabel("Residuals")
                        ax.set_title("Residuals vs Fitted Values")
                        st.pyplot(fig)
                        plt.close(fig)

                        st.caption(
                            "A residual pattern that is roughly centered around "
                            "zero without systematic structure is generally more "
                            "consistent with a linear model. Diagnostic tests "
                            "provide additional evidence rather than absolute proof."
                        )


        anova_group_columns = []

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

        st.write("### Interpretation")

        st.info(
            f"At α = {chi_critical_alpha:.3f} with {chi_critical_df} "
            f"degree(s) of freedom, the critical χ² value is "
            f"{chi_critical_value:.4f}. A calculated χ² value greater "
            "than this critical value falls in the rejection region."
        )

        chi_calculated = st.number_input(
            "Optional χ²-Calculated value",
            min_value=0.0,
            value=0.0,
            step=0.1,
            key="chi_calculated_for_critical"
        )

        if chi_calculated > 0:

            if chi_calculated > chi_critical_value:

                st.warning(
                    f"χ²-calculated ({chi_calculated:.4f}) > "
                    f"χ²-tabulated ({chi_critical_value:.4f}). "
                    "Reject the null hypothesis at the selected "
                    "significance level."
                )

                st.write(
                    "### Conclusion"
                )

                st.write(
                    "The calculated chi-square statistic lies in the "
                    "rejection region. Therefore, the observed result "
                    "is statistically significant at the selected "
                    "significance level."
                )

            else:

                st.success(
                    f"χ²-calculated ({chi_calculated:.4f}) ≤ "
                    f"χ²-tabulated ({chi_critical_value:.4f}). "
                    "Fail to reject the null hypothesis at the selected "
                    "significance level."
                )

                st.write(
                    "### Conclusion"
                )

                st.write(
                    "The calculated chi-square statistic does not lie "
                    "in the rejection region. Therefore, there is not "
                    "sufficient statistical evidence to reject the null "
                    "hypothesis at the selected significance level."
                )

        st.caption(
            "This value is the same type of critical value found "
            "in a printed χ² distribution table."
        )


        st.subheader("ANOVA Effect Size and Post-Hoc Analysis")

        if anova_group_columns:
            effect_group = st.selectbox(
                "ANOVA grouping variable",
                anova_group_columns,
                key="effect_anova_group"
            )
            effect_value = st.selectbox(
                "ANOVA response variable",
                numeric_columns,
                key="effect_anova_value"
            )

            if st.button("Calculate ANOVA Effect Size and Tukey Post-Hoc"):
                effect_anova = one_way_anova(
                    df,
                    effect_value,
                    effect_group
                )

                if effect_anova is None:
                    st.error(
                        "At least three groups with sufficient valid observations "
                        "are required."
                    )
                else:
                    eta = one_way_eta_squared(effect_anova)

                    st.metric(
                        "Eta-Squared (η²)",
                        f"{eta:.4f}" if eta is not None else "—"
                    )

                    st.caption(
                        "η² describes the proportion of response variation "
                        "associated with the grouping factor."
                    )

                    if effect_anova["P-Value"] < anova_alpha:
                        tukey = tukey_hsd_posthoc(
                            df,
                            effect_value,
                            effect_group,
                            alpha=anova_alpha
                        )

                        if tukey is not None:
                            st.write("### Tukey HSD Post-Hoc Comparisons")
                            st.dataframe(
                                tukey,
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info(
                                "Tukey HSD could not be calculated for the "
                                "selected data."
                            )
                    else:
                        st.info(
                            "Post-hoc comparisons are not run because the "
                            "overall ANOVA is not significant at the selected α."
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


        st.subheader("Effect Sizes")

        st.write(
            "Effect sizes describe the practical magnitude of an association "
            "or difference, complementing statistical significance."
        )

        if len(numeric_columns) >= 2:
            d_col1, d_col2 = st.columns(2)

            with d_col1:
                d_group1 = st.selectbox(
                    "Group 1",
                    numeric_columns,
                    key="effect_d_group1"
                )

            with d_col2:
                d_group2_options = [
                    column for column in numeric_columns
                    if column != d_group1
                ]
                d_group2 = st.selectbox(
                    "Group 2",
                    d_group2_options,
                    key="effect_d_group2"
                )

            if st.button("Calculate Cohen's d"):
                d_result = cohens_d_independent(
                    df,
                    d_group1,
                    d_group2
                )

                if d_result is None:
                    st.error(
                        "Both numerical groups need at least two valid "
                        "observations and non-zero pooled variation."
                    )
                else:
                    d_value = d_result["Cohen's d"]
                    d_abs = abs(d_value)
                    d_strength = (
                        "small" if d_abs < 0.5
                        else "medium" if d_abs < 0.8
                        else "large"
                    )

                    st.metric("Cohen's d", f"{d_value:.4f}")
                    st.write(
                        f"The standardized difference is **{d_strength}** "
                        f"(using common Cohen's d thresholds)."
                    )

        if len(categorical_columns) >= 2:
            cv_factor1 = st.selectbox(
                "Categorical variable 1",
                categorical_columns,
                key="effect_cv_factor1"
            )
            cv_factor2_options = [
                column for column in categorical_columns
                if column != cv_factor1
            ]
            cv_factor2 = st.selectbox(
                "Categorical variable 2",
                cv_factor2_options,
                key="effect_cv_factor2"
            )

            if st.button("Calculate Cramér's V"):
                cv_value = cramers_v(
                    df,
                    cv_factor1,
                    cv_factor2
                )

                if cv_value is None:
                    st.error(
                        "Two categorical variables with at least two "
                        "valid categories each are required."
                    )
                else:
                    st.metric("Cramér's V", f"{cv_value:.4f}")
                    st.caption(
                        "Cramér's V ranges from 0 to 1, with larger values "
                        "indicating stronger association."
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
