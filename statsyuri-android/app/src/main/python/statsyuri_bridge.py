import json
from pathlib import Path

import pandas as pd
from scipy import stats

from src.question_engine import interpret_question
from src.experimental_designs import run_experimental_design_analysis
from src.statistics import (
    get_numeric_statistics,
    calculate_correlation,
    one_sample_t_test,
    one_way_anova,
    two_sample_t_test,
    simple_linear_regression,
    chi_square_independence,
    wilcoxon_signed_rank_test,
    mann_whitney_u_test,
    kruskal_wallis_test,
)


def _load(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError("Offline APK currently supports CSV and Excel files.")


def _clean(value):
    if isinstance(value, pd.DataFrame):
        return {
            "columns": list(value.columns),
            "rows": value.fillna("").astype(str).values.tolist(),
        }
    if isinstance(value, pd.Series):
        return value.fillna("").tolist()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    return value


def _looks_like_identifier(column):
    name = str(column).strip().lower().replace("-", "_").replace(" ", "_")
    identifier_tokens = ("id", "index", "serial", "code", "roll", "record", "row", "column")
    return name in identifier_tokens or any(
        name.startswith(token + "_") or name.endswith("_" + token)
        for token in identifier_tokens
    )


def _numeric_columns(df):
    return [
        c for c in df.select_dtypes(include="number").columns
        if not _looks_like_identifier(c)
    ]


def _categorical_columns(df):
    numeric = set(_numeric_columns(df))
    return [
        c for c in df.columns
        if c not in numeric
        and not _looks_like_identifier(c)
        and 2 <= df[c].nunique(dropna=True) <= max(20, int(len(df) * 0.5))
    ]


def _automatic_candidate(df):
    """Choose a safe analysis when the user only supplies a dataset."""
    numeric = _numeric_columns(df)
    categorical = _categorical_columns(df)

    for group in categorical:
        if df[group].nunique(dropna=True) >= 3 and numeric:
            return {
                "analysis": "One-way ANOVA",
                "response": numeric[0],
                "grouping": group,
                "reason": f"Automatically selected one-way ANOVA because '{numeric[0]}' is numeric and '{group}' contains three or more groups.",
            }

    for group in categorical:
        if df[group].nunique(dropna=True) == 2 and numeric:
            return {
                "analysis": "Welch two-sample t-test",
                "response": numeric[0],
                "grouping": group,
                "reason": f"Automatically selected Welch's t-test because '{numeric[0]}' is numeric and '{group}' contains exactly two groups.",
            }

    if len(numeric) >= 2:
        return {
            "analysis": "Pearson correlation + simple linear regression",
            "variable_1": numeric[0],
            "variable_2": numeric[1],
            "reason": "Automatically selected correlation and regression because the dataset contains at least two analysis-ready numeric variables.",
        }

    if numeric:
        return {
            "analysis": "Descriptive statistics",
            "response": numeric[0],
            "reason": "Automatically selected descriptive statistics because the dataset contains one analysis-ready numeric variable.",
        }

    if len(categorical) >= 2:
        return {
            "analysis": "Chi-square test of independence",
            "variable_1": categorical[0],
            "variable_2": categorical[1],
            "reason": "Automatically selected a chi-square test because the dataset contains at least two categorical variables.",
        }

    return None


def _anova_calculation(df, response, grouping, result):
    data = df[[response, grouping]].dropna().copy()
    groups = []
    for label, part in data.groupby(grouping):
        values = pd.to_numeric(part[response], errors="coerce").dropna()
        if len(values) >= 2:
            groups.append((label, values))
    if len(groups) < 2:
        return "ANOVA calculation unavailable: fewer than two groups have at least two observations."

    all_values = pd.concat([values for _, values in groups], ignore_index=True)
    grand_mean = all_values.mean()
    ss_between = sum(len(values) * (values.mean() - grand_mean) ** 2 for _, values in groups)
    ss_within = sum(((values - values.mean()) ** 2).sum() for _, values in groups)
    k = len(groups)
    n = len(all_values)
    df_between = k - 1
    df_within = n - k
    ms_between = ss_between / df_between if df_between else float("nan")
    ms_within = ss_within / df_within if df_within else float("nan")
    f_value = ms_between / ms_within if ms_within else float("nan")

    return "\n".join([
        "One-way ANOVA calculation",
        f"Grand mean = Σx / N = {grand_mean:.6g}",
        f"SS_between = Σ nᵢ(x̄ᵢ − x̄)² = {ss_between:.6g}",
        f"SS_within = ΣΣ(xᵢⱼ − x̄ᵢ)² = {ss_within:.6g}",
        f"df_between = k − 1 = {df_between}",
        f"df_within = N − k = {df_within}",
        f"MS_between = SS_between / df_between = {ms_between:.6g}",
        f"MS_within = SS_within / df_within = {ms_within:.6g}",
        f"F = MS_between / MS_within = {f_value:.6g}",
        f"p-value = {float(result.get('P-Value')):.6g}",
    ])


def _welch_calculation(df, response, grouping, result):
    groups = list(df[grouping].dropna().unique())
    if len(groups) != 2:
        return "Welch calculation unavailable: exactly two groups are required."
    a = pd.to_numeric(df.loc[df[grouping] == groups[0], response], errors="coerce").dropna()
    b = pd.to_numeric(df.loc[df[grouping] == groups[1], response], errors="coerce").dropna()
    if len(a) < 2 or len(b) < 2:
        return "Welch calculation unavailable: each group needs at least two observations."
    se = ((a.var(ddof=1) / len(a)) + (b.var(ddof=1) / len(b))) ** 0.5
    diff = a.mean() - b.mean()
    t_value = diff / se if se else float("nan")
    return "\n".join([
        "Welch two-sample t-test calculation",
        f"Mean difference = x̄₁ − x̄₂ = {diff:.6g}",
        f"SE = √(s₁²/n₁ + s₂²/n₂) = {se:.6g}",
        f"t = difference / SE = {t_value:.6g}",
        f"df (Welch–Satterthwaite) = {float(result.get('Degrees of Freedom')):.6g}",
        f"p-value = {float(result.get('P-Value')):.6g}",
    ])


def _descriptive_calculation(df, numeric):
    lines = ["Descriptive statistics calculation"]
    for column in numeric:
        data = pd.to_numeric(df[column], errors="coerce").dropna()
        if data.empty:
            continue
        mean = data.mean()
        sd = data.std(ddof=1) if len(data) > 1 else float("nan")
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        lines.extend([
            f"{column}: n={len(data)}, mean=Σx/n={mean:.6g}, SD=√(Σ(x−x̄)²/(n−1))={sd:.6g}",
            f"  median={data.median():.6g}, Q1={q1:.6g}, Q3={q3:.6g}, IQR=Q3−Q1={q3-q1:.6g}",
        ])
    return "\n".join(lines)


def _execute(df, candidate):
    analysis = candidate.get("analysis", "")

    if analysis == "One-sample t-test":
        response = candidate.get("response") or _numeric_columns(df)[0]
        result = one_sample_t_test(df, response, 0.0)
        return {"test": analysis, "result": _clean(result), "calculation": "t = (x̄ − μ₀) / (s/√n), with μ₀ = 0. The result above contains the computed t-statistic, p-value and degrees of freedom."}

    if analysis == "One-way ANOVA":
        response = candidate.get("response")
        grouping = candidate.get("grouping")
        if not response or not grouping:
            numeric = _numeric_columns(df)
            categorical = [c for c in df.columns if c not in numeric and not _looks_like_identifier(c) and df[c].nunique() >= 3]
            response = response or (numeric[0] if numeric else None)
            grouping = grouping or (categorical[0] if categorical else None)
        if not response or not grouping:
            raise ValueError("Could not identify the response and grouping columns.")
        result = one_way_anova(df, response, grouping)
        if result is None:
            raise ValueError("ANOVA needs at least three groups with at least two observations each.")
        return {"test": analysis, "result": _clean(result), "calculation": _anova_calculation(df, response, grouping, result)}

    if analysis == "Welch two-sample t-test":
        response = candidate.get("response")
        grouping = candidate.get("grouping")
        if not response or not grouping:
            numeric = _numeric_columns(df)
            categorical = [c for c in df.columns if c not in numeric and not _looks_like_identifier(c) and df[c].nunique() == 2]
            response = response or (numeric[0] if numeric else None)
            grouping = grouping or (categorical[0] if categorical else None)
        if not response or not grouping:
            raise ValueError("Could not identify the response and grouping columns.")
        groups = list(df[grouping].dropna().unique())
        if len(groups) != 2:
            raise ValueError("Exactly two groups are required for Welch's t-test.")
        result = two_sample_t_test(df, response, grouping, groups[0], groups[1])
        return {"test": analysis, "result": _clean(result), "calculation": _welch_calculation(df, response, grouping, result)}

    if analysis.startswith("Pearson correlation"):
        cols = [candidate.get("variable_1"), candidate.get("variable_2")]
        cols = [c for c in cols if c]
        if len(cols) < 2:
            cols = _numeric_columns(df)[:2]
        result = calculate_correlation(df[cols])
        return {"test": "Pearson correlation", "result": _clean(result), "calculation": "r = cov(X,Y)/(sₓsᵧ), computed from the selected numeric columns."}

    if analysis == "Simple linear regression":
        x = candidate.get("predictor") or candidate.get("variable_1")
        y = candidate.get("response") or candidate.get("variable_2")
        numeric = _numeric_columns(df)
        x = x or (numeric[0] if numeric else None)
        y = y or (numeric[1] if len(numeric) > 1 else None)
        if not x or not y:
            raise ValueError("Two numerical variables are required for regression.")
        result = simple_linear_regression(df, x, y)
        return {"test": analysis, "result": _clean(result), "calculation": "ŷ = a + bx, where b = Cov(X,Y)/Var(X), a = ȳ − bx̄, and R² = r²."}

    if analysis == "Chi-square test of independence":
        f1 = candidate.get("variable_1")
        f2 = candidate.get("variable_2")
        categorical = [c for c in df.columns if df[c].dtype == "object" and not _looks_like_identifier(c) and df[c].nunique() >= 2]
        f1 = f1 or (categorical[0] if categorical else None)
        f2 = f2 or (categorical[1] if len(categorical) > 1 else None)
        if not f1 or not f2:
            raise ValueError("Two categorical variables are required.")
        result = chi_square_independence(df, f1, f2)
        return {"test": analysis, "result": _clean(result), "calculation": "Expected count Eᵢⱼ = (row total × column total)/grand total; χ² = Σ(Oᵢⱼ−Eᵢⱼ)²/Eᵢⱼ."}

    if analysis == "Paired t-test candidate":
        a = candidate.get("variable_1")
        b = candidate.get("variable_2")
        numeric = _numeric_columns(df)
        if not a or not b:
            a, b = numeric[:2]
        if not a or not b:
            raise ValueError("Two numerical paired columns are required.")
        data = df[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
        result = stats.ttest_rel(data[a], data[b])
        return {"test": "Paired t-test", "result": {"Variable 1": a, "Variable 2": b, "Mean Difference": float((data[a] - data[b]).mean()), "T-Statistic": float(result.statistic), "P-Value": float(result.pvalue), "Degrees of Freedom": int(len(data) - 1)}, "calculation": "dᵢ = Xᵢ − Yᵢ; t = d̄/(s_d/√n), with df = n−1."}

    return {"test": analysis or "Descriptive statistics", "result": _clean(get_numeric_statistics(df)), "calculation": _descriptive_calculation(df, _numeric_columns(df))}


def analyze(question, file_path=None, mode="Efficient"):
    question = (question or "").strip()
    df = _load(file_path) if file_path else None

    # A blank question is intentional: Analyze works from the dataset alone.
    if df is not None and not question:
        selected = _automatic_candidate(df)
        interpretation = {
            "problem_type": "Automatic dataset analysis",
            "reason": selected.get("reason") if selected else "The dataset could not be mapped to an automatic analysis.",
            "plan": {"objective": selected.get("reason") if selected else "Additional information is required."},
            "candidates": [selected] if selected else [],
        }
    else:
        interpretation = interpret_question(df, question)
        candidates = interpretation.get("candidates", [])
        selected = candidates[0] if candidates else None
        if df is not None and selected is None:
            selected = _automatic_candidate(df)
            if selected:
                interpretation["reason"] = "The question was not mapped confidently, so StatsYuri analyzed the dataset structure automatically. " + selected.get("reason", "")
                interpretation["candidates"] = [selected]

    candidates = interpretation.get("candidates", [])
    selected = candidates[0] if candidates else None

    payload = {
        "app": "StatsYuri Offline",
        "mode": mode,
        "rows": int(df.shape[0]) if df is not None else None,
        "columns": list(df.columns) if df is not None else [],
        "problem_type": interpretation.get("problem_type"),
        "reason": interpretation.get("reason"),
        "plan": interpretation.get("plan", {}),
        "confirmed_analysis": selected.get("analysis") if selected else None,
        "candidate_count": len(candidates),
    }

    if df is not None and selected:
        design = selected.get("design")
        if design:
            payload["execution"] = _clean(run_experimental_design_analysis(df, question, design=design))
        else:
            payload["execution"] = _execute(df, selected)
    elif df is not None:
        payload["execution"] = {
            "test": "No automatic analysis available",
            "calculation": "Select a dataset with at least one numeric or two categorical analysis-ready columns, or provide a statistical question.",
        }

    return json.dumps(payload, ensure_ascii=False, default=str)
