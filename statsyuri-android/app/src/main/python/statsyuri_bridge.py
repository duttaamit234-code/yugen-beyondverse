import json
from pathlib import Path

import pandas as pd

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


def _numeric_columns(df):
    return [
        c for c in df.select_dtypes(include="number").columns
        if not str(c).lower().endswith("_id")
    ]


def _execute(df, candidate):
    analysis = candidate.get("analysis", "")

    if analysis == "One-sample t-test":
        response = candidate.get("response") or _numeric_columns(df)[0]
        result = one_sample_t_test(df, response, 0.0)
        return {"test": analysis, "result": _clean(result)}

    if analysis == "One-way ANOVA":
        response = candidate.get("response")
        grouping = candidate.get("grouping")
        if not response or not grouping:
            numeric = _numeric_columns(df)
            categorical = [c for c in df.columns if c not in numeric and df[c].nunique() >= 3]
            response = response or (numeric[0] if numeric else None)
            grouping = grouping or (categorical[0] if categorical else None)
        if not response or not grouping:
            raise ValueError("Could not identify the response and grouping columns.")
        return {"test": analysis, "result": _clean(one_way_anova(df, response, grouping))}

    if analysis == "Welch two-sample t-test":
        response = candidate.get("response")
        grouping = candidate.get("grouping")
        if not response or not grouping:
            numeric = _numeric_columns(df)
            categorical = [c for c in df.columns if c not in numeric and df[c].nunique() == 2]
            response = response or (numeric[0] if numeric else None)
            grouping = grouping or (categorical[0] if categorical else None)
        if not response or not grouping:
            raise ValueError("Could not identify the response and grouping columns.")
        groups = list(df[grouping].dropna().unique())
        if len(groups) != 2:
            raise ValueError("Exactly two groups are required for Welch's t-test.")
        return {
            "test": analysis,
            "result": _clean(two_sample_t_test(df, response, grouping, groups[0], groups[1])),
        }

    if analysis.startswith("Pearson correlation"):
        cols = [candidate.get("variable_1"), candidate.get("variable_2")]
        cols = [c for c in cols if c]
        if len(cols) < 2:
            cols = _numeric_columns(df)[:2]
        return {"test": "Pearson correlation", "result": _clean(calculate_correlation(df[cols]))}

    if analysis == "Simple linear regression":
        x = candidate.get("predictor") or candidate.get("variable_1")
        y = candidate.get("response") or candidate.get("variable_2")
        numeric = _numeric_columns(df)
        x = x or (numeric[0] if numeric else None)
        y = y or (numeric[1] if len(numeric) > 1 else None)
        if not x or not y:
            raise ValueError("Two numerical variables are required for regression.")
        return {"test": analysis, "result": _clean(simple_linear_regression(df, x, y))}

    if analysis == "Chi-square test of independence":
        f1 = candidate.get("variable_1")
        f2 = candidate.get("variable_2")
        categorical = [c for c in df.columns if df[c].dtype == "object" and df[c].nunique() >= 2]
        f1 = f1 or (categorical[0] if categorical else None)
        f2 = f2 or (categorical[1] if len(categorical) > 1 else None)
        if not f1 or not f2:
            raise ValueError("Two categorical variables are required.")
        return {"test": analysis, "result": _clean(chi_square_independence(df, f1, f2))}

    if analysis == "Paired t-test candidate":
        a = candidate.get("variable_1")
        b = candidate.get("variable_2")
        numeric = _numeric_columns(df)
        if not a or not b:
            a, b = numeric[:2]
        if not a or not b:
            raise ValueError("Two numerical paired columns are required.")
        from scipy import stats
        data = df[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
        result = stats.ttest_rel(data[a], data[b])
        return {
            "test": "Paired t-test",
            "result": {
                "Variable 1": a,
                "Variable 2": b,
                "Mean Difference": float((data[a] - data[b]).mean()),
                "T-Statistic": float(result.statistic),
                "P-Value": float(result.pvalue),
                "Degrees of Freedom": int(len(data) - 1),
            },
        }

    return {
        "test": analysis or "Descriptive statistics",
        "result": _clean(get_numeric_statistics(df)),
    }


def analyze(question, file_path=None, mode="Efficient"):
    question = (question or "").strip()

    if file_path:
        df = _load(file_path)
        interpretation = interpret_question(df, question)
    else:
        df = None
        interpretation = interpret_question(None, question)

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
            payload["execution"] = _clean(
                run_experimental_design_analysis(df, question, design=design)
            )
        elif mode == "Efficient":
            payload["execution"] = _execute(df, selected)
        else:
            payload["execution"] = _execute(df, selected)

    return json.dumps(payload, ensure_ascii=False, default=str)
