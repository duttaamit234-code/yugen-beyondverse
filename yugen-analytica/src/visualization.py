import pandas as pd
import matplotlib.pyplot as plt


def _looks_like_identifier(column_name):
    """Identify common identifier/index columns that should not drive analysis."""
    name = str(column_name).strip().lower()
    identifier_tokens = (
        "id",
        "index",
        "serial",
        "code",
        "roll",
        "record",
    )
    return (
        name in identifier_tokens
        or any(
            name.startswith(token + "_")
            or name.endswith("_" + token)
            for token in identifier_tokens
        )
    )


def get_numeric_columns(df):
    """Return numerical columns suitable for statistical analysis."""
    return [
        column
        for column in df.select_dtypes(include="number").columns.tolist()
        if not _looks_like_identifier(column)
    ]


def create_histogram(df, column):
    """Create a histogram for a numerical column."""

    data = df[column].dropna()

    fig, ax = plt.subplots()

    ax.hist(data, bins=10)

    ax.set_title(f"Distribution of {column}")
    ax.set_xlabel(column)
    ax.set_ylabel("Frequency")

    return fig


def create_box_plot(df, column):
    """Create a box plot for a numerical column."""

    data = df[column].dropna()

    fig, ax = plt.subplots()

    ax.boxplot(data)

    ax.set_title(f"Box Plot of {column}")
    ax.set_ylabel(column)

    return fig


def create_correlation_heatmap(correlation_matrix):
    """Create a heatmap from a correlation matrix."""

    fig, ax = plt.subplots()

    image = ax.imshow(
        correlation_matrix,
        interpolation="nearest",
        aspect="auto"
    )

    ax.set_xticks(
        range(len(correlation_matrix.columns))
    )

    ax.set_yticks(
        range(len(correlation_matrix.columns))
    )

    ax.set_xticklabels(
        correlation_matrix.columns,
        rotation=45,
        ha="right"
    )

    ax.set_yticklabels(
        correlation_matrix.columns
    )

    ax.set_title("Correlation Matrix")

    fig.colorbar(image, ax=ax)

    return fig
