import pandas as pd
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}


def load_dataset(uploaded_file):
    """Load a CSV or Excel dataset."""

    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            "Supported formats: CSV, XLSX, XLS."
        )

    if extension == ".csv":
        return pd.read_csv(uploaded_file)

    return pd.read_excel(uploaded_file)


def validate_dataset(df):
    """Perform basic dataset validation."""

    if df.empty:
        return False, ["The dataset is empty."]

    problems = []

    if len(df.columns) == 0:
        problems.append("No columns were detected.")

    duplicate_columns = (
        df.columns[df.columns.duplicated()]
        .tolist()
    )

    if duplicate_columns:
        problems.append(
            f"Duplicate column names detected: "
            f"{duplicate_columns}"
        )

    return len(problems) == 0, problems


def get_dataset_summary(df):
    """Return basic dataset information."""

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": int(
            df.isna().sum().sum()
        ),
        "duplicate_rows": int(
            df.duplicated().sum()
        ),
    }
