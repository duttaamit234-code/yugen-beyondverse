import streamlit as st

from src.data_loader import (
    load_dataset,
    validate_dataset,
    get_dataset_summary,
)


st.set_page_config(
    page_title="Yugen Analytica",
    page_icon="📊",
    layout="wide",
)

st.title("Yugen Analytica")
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

        valid, problems = validate_dataset(df)

        if not valid:
            st.warning("Dataset validation found some problems.")

            for problem in problems:
                st.error(problem)

        else:
            st.success(
                f"Successfully imported `{uploaded_file.name}`"
            )

        summary = get_dataset_summary(df)

        st.markdown("### Dataset Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Rows", summary["rows"])

        with col2:
            st.metric("Columns", summary["columns"])

        with col3:
            st.metric(
                "Missing Values",
                summary["missing_values"],
            )

        with col4:
            st.metric(
                "Duplicate Rows",
                summary["duplicate_rows"],
            )

        st.markdown("### Dataset Preview")

        st.dataframe(
            df.head(100),
            use_container_width=True,
        )

        st.markdown("### Column Information")

        column_info = df.dtypes.astype(str).reset_index()
        column_info.columns = ["Column", "Data Type"]

        st.dataframe(
            column_info,
            use_container_width=True,
        )

        st.markdown("### Missing Values")

        missing = df.isna().sum().reset_index()
        missing.columns = ["Column", "Missing Values"]

        st.dataframe(
            missing,
            use_container_width=True,
        )

    except Exception as error:
        st.error(
            f"Unable to load the dataset: {error}"
        )
