import pandas as pd
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls"
}


def load_dataset(uploaded_file):
    """Load a CSV or Excel dataset."""

    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    if extension == ".csv":
        return pd.read_csv(uploaded_file)

    return pd.read_excel(uploaded_file)


def validate_dataset(df):
    """Perform basic dataset validation."""

    missing_values = int(df.isna().sum().sum())

    return {
        "valid": len(df.columns) > 0 and len(df) > 0,
        "missing_values": missing_values,
    }


def get_dataset_summary(df):
    """Return basic dataset statistics."""

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_values": int(df.isna().sum().sum()),
    }
