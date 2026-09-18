import pandas as pd
import matplotlib.pyplot as plt


def get_numeric_columns(df):
    """Return the names of numerical columns."""

    return df.select_dtypes(include="number").columns.tolist()


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
