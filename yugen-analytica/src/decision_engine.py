"""Shared decision and automatic-analysis helpers for StatsYuri."""

from itertools import combinations

import pandas as pd


def compare_p_value(p_value, alpha=0.05):
    """Compare a p-value with alpha and return a consistent decision."""
    if p_value is None or pd.isna(p_value):
        return {
            "Decision": "Unavailable",
            "Comparison": "p-value unavailable",
            "Interpretation": "A statistical decision cannot be made from the available result.",
        }

    if p_value < alpha:
        return {
            "Decision": "Reject H₀",
            "Comparison": f"p = {p_value:.6g} < α = {alpha:.2f}",
            "Interpretation": (
                "The result provides statistical evidence against the null "
                "hypothesis at the selected significance level."
            ),
        }

    return {
        "Decision": "Fail to reject H₀",
        "Comparison": f"p = {p_value:.6g} ≥ α = {alpha:.2f}",
        "Interpretation": (
            "The result does not provide sufficient statistical evidence "
            "against the null hypothesis at the selected significance level."
        ),
    }


def interpret_correlation(r):
    """Return a consistent plain-language interpretation of Pearson r."""
    if r is None or pd.isna(r):
        return "Correlation is unavailable."

    magnitude = abs(r)

    if magnitude < 0.20:
        strength = "very weak"
    elif magnitude < 0.40:
        strength = "weak"
    elif magnitude < 0.60:
        strength = "moderate"
    elif magnitude < 0.80:
        strength = "strong"
    else:
        strength = "very strong"

    direction = "positive" if r > 0 else "negative" if r < 0 else "no"

    if r == 0:
        return "There is no linear correlation in the sample."

    return (
        f"The sample shows a {strength} {direction} linear correlation "
        f"(r = {r:.4f}). Correlation does not establish causation."
    )


def interpret_effect_size(effect_name, value):
    """Provide cautious labels for common effect-size measures."""
    if value is None or pd.isna(value):
        return "Effect size is unavailable."

    magnitude = abs(value)

    if effect_name.lower() in {"cohen's d", "cohens d"}:
        if magnitude < 0.20:
            label = "negligible"
        elif magnitude < 0.50:
            label = "small"
        elif magnitude < 0.80:
            label = "medium"
        else:
            label = "large"
    elif effect_name.lower() in {"eta squared", "η²", "eta-squared"}:
        if magnitude < 0.01:
            label = "small"
        elif magnitude < 0.06:
            label = "medium"
        else:
            label = "large"
    elif effect_name.lower() in {"cramer's v", "cramers v"}:
        if magnitude < 0.10:
            label = "very small"
        elif magnitude < 0.30:
            label = "small"
        elif magnitude < 0.50:
            label = "moderate"
        else:
            label = "large"
    else:
        label = "not classified"

    return f"{effect_name} = {value:.4f} ({label} by the selected heuristic)."


def _column_profile(df):
    numeric = df.select_dtypes(include="number").columns.tolist()
    categorical = [
        column
        for column in df.columns
        if column not in numeric
        and df[column].nunique(dropna=True) >= 2
    ]

    return numeric, categorical


def recommend_analyses(df):
    """Detect common dataset structures and suggest suitable analyses.

    The function deliberately returns recommendations rather than pretending
    that software can infer the research question from a table alone.
    """
    numeric, categorical = _column_profile(df)
    recommendations = []

    # Two-level categorical factor + numerical response.
    for group_column in categorical:
        levels = df[group_column].dropna().unique()
        if len(levels) != 2:
            continue

        for response in numeric:
            data = df[[group_column, response]].dropna()
            counts = data.groupby(group_column)[response].count()

            if len(counts) == 2 and (counts >= 2).all():
                recommendations.append({
                    "Analysis": "Welch two-sample t-test",
                    "Structure": "Numerical response + two independent groups",
                    "Response": response,
                    "Grouping": group_column,
                    "Why": (
                        "A numerical outcome is available across exactly "
                        "two groups with at least two observations per group."
                    ),
                    "Follow-up": "Cohen's d can quantify standardized mean difference.",
                })

    # Three or more groups + numerical response.
    for group_column in categorical:
        levels = df[group_column].dropna().nunique()
        if levels < 3:
            continue

        for response in numeric:
            data = df[[group_column, response]].dropna()
            counts = data.groupby(group_column)[response].count()

            if len(counts) >= 3 and (counts >= 2).all():
                recommendations.append({
                    "Analysis": "One-way ANOVA",
                    "Structure": "Numerical response + three or more independent groups",
                    "Response": response,
                    "Grouping": group_column,
                    "Why": (
                        "A numerical outcome is available across three or "
                        "more groups with at least two observations per group."
                    ),
                    "Follow-up": (
                        "If the omnibus result is significant, Tukey HSD "
                        "can examine pairwise mean differences."
                    ),
                    "Alternative": "Kruskal-Wallis is a non-parametric alternative.",
                })

    # Two or more numerical variables.
    for x, y in combinations(numeric, 2):
        data = df[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(data) >= 3 and data[x].nunique() >= 2 and data[y].nunique() >= 2:
            recommendations.append({
                "Analysis": "Pearson correlation + simple linear regression",
                "Structure": "Two numerical variables",
                "Variable 1": x,
                "Variable 2": y,
                "Why": (
                    "Both variables are numerical and contain enough valid "
                    "observations with variation to examine linear association."
                ),
                "Follow-up": (
                    "Inspect the scatter pattern and remember that "
                    "correlation does not establish causation."
                ),
            })

    # Two categorical variables.
    for factor1, factor2 in combinations(categorical, 2):
        data = df[[factor1, factor2]].dropna()
        if (
            data[factor1].nunique() >= 2
            and data[factor2].nunique() >= 2
            and len(data) >= 2
        ):
            recommendations.append({
                "Analysis": "Chi-square test of independence",
                "Structure": "Two categorical variables",
                "Variable 1": factor1,
                "Variable 2": factor2,
                "Why": (
                    "Both variables are categorical with at least two "
                    "observed levels."
                ),
                "Follow-up": "Cramér's V can quantify association strength.",
            })

    # Keep the automatic dashboard readable on wide datasets.
    return recommendations[:12]


def summarize_recommendations(recommendations):
    """Convert recommendation dictionaries into a compact DataFrame."""
    if not recommendations:
        return pd.DataFrame(
            columns=["Analysis", "Structure", "Variables", "Reason"]
        )

    rows = []
    for item in recommendations:
        variables = [
            str(item[key])
            for key in (
                "Response",
                "Grouping",
                "Variable 1",
                "Variable 2",
            )
            if key in item
        ]
        rows.append({
            "Analysis": item["Analysis"],
            "Structure": item["Structure"],
            "Variables": ", ".join(variables),
            "Reason": item["Why"],
        })

    return pd.DataFrame(rows)


def decision_from_result(p_value, alpha=0.05, test_name="Test"):
    """Build the standard calculate → compare → decide → interpret output."""
    decision = compare_p_value(p_value, alpha)
    return {
        "Test": test_name,
        "p-value": p_value,
        "alpha": alpha,
        **decision,
    }
