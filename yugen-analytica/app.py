import streamlit as st

from src.data_loader import (
    load_dataset,
    validate_dataset,
    get_dataset_summary,
)

from src.statistics import get_numeric_statistics


st.set_page_config(
    page_title="Yugen Analytics",
    page_icon="📊",
    layout="wide",
)


st.title("Yugen Analytics")
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


    except Exception as e:

        st.error(
            f"Unable to process the dataset: {e}"
        )
