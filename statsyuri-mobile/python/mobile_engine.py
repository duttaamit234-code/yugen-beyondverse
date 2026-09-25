"""Offline bridge for the StatsYuri Android app.

This module is intentionally UI-independent. Flutter passes a local file path and
research question here; the existing StatsYuri Python analysis modules do the work.
"""

import json
import re
from pathlib import Path

import pandas as pd
from scipy import stats

from src.statistics import (
    chi_square_independence,
    one_sample_t_test,
    one_way_anova,
    simple_linear_regression,
    two_sample_t_test,
)

from src.question_engine import interpret_question
from src.experimental_designs import run_experimental_design_analysis


def _load(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError("Supported mobile data files are CSV and Excel.")


def _json_safe(value):
    if isinstance(value, pd.DataFrame):
        return value.reset_index().to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.to_dict()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    try:
        json.dumps(value)
        return value
    except Exception:
        return str(value)


def analyze_file(path, question="", mode="efficient"):
    df = _load(path)
    question = str(question or "").strip()

    if not question:
        return json.dumps({
            "ok": True,
            "rows": int(df.shape[0]),
            "columns": list(map(str, df.columns)),
            "message": "Dataset loaded. Describe the statistical problem to continue.",
        })

    plan = interpret_question(df, question)

    if not plan.get("candidates"):
        return json.dumps({
            "ok": False,
            "error": plan.get("reason", "More information is needed to select an analysis."),
            "plan": _json_safe(plan),
        })

    candidate = plan["candidates"][0]
    analysis = candidate.get("analysis", "")
    design = candidate.get("design")

    # Experimental designs use the same confirmed Python engine as the web app.
    if design:
        result = run_experimental_design_analysis(df, question, design=design)
        return json.dumps({
            "ok": result.get("error") is None,
            "analysis": analysis,
            "design": design,
            "roles": _json_safe(result.get("roles", {})),
            "result": _json_safe(result.get("result")),
            "error": result.get("error"),
            "rows": int(df.shape[0]),
        })

    response = candidate.get("response")
    grouping = candidate.get("grouping")
    variable_1 = candidate.get("variable_1")
    variable_2 = candidate.get("variable_2")
    result = None

    if analysis in {"One-way ANOVA", "Welch two-sample t-test"} and response and grouping:
        result = (
            one_way_anova(df, response, grouping)
            if analysis == "One-way ANOVA"
            else two_sample_t_test(df, response, grouping)
        )
    elif analysis == "Chi-square test of independence" and variable_1 and variable_2:
        result = chi_square_independence(df, variable_1, variable_2)
    elif analysis == "Simple linear regression":
        predictor = candidate.get("predictor") or variable_1
        outcome = candidate.get("response") or variable_2
        if predictor and outcome:
            result = simple_linear_regression(df, predictor, outcome)
    elif analysis == "Pearson correlation":
        x = variable_1 or response
        y = variable_2
        if x and y:
            clean = df[[x, y]].dropna()
            r_value, p_value = stats.pearsonr(clean[x], clean[y])
            result = {"r": float(r_value), "p_value": float(p_value), "n": int(len(clean))}
    elif analysis == "Pearson correlation + simple linear regression":
        x = variable_1
        y = variable_2
        if x and y:
            clean = df[[x, y]].dropna()
            r_value, p_value = stats.pearsonr(clean[x], clean[y])
            result = {
                "correlation": {"r": float(r_value), "p_value": float(p_value), "n": int(len(clean))},
                "regression": _json_safe(simple_linear_regression(df, x, y)),
            }
    elif analysis in {"Paired t-test", "Paired t-test candidate"}:
        x = variable_1 or response
        y = variable_2
        if x and y:
            clean = df[[x, y]].dropna()
            statistic, p_value = stats.ttest_rel(clean[x], clean[y])
            result = {"t": float(statistic), "p_value": float(p_value), "n_pairs": int(len(clean))}
    elif analysis == "One-sample t-test":
        column = response or variable_1
        numbers = [
            float(x) for x in re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", question)
            if abs(float(x)) > 0.049
        ]
        if column and numbers:
            result = one_sample_t_test(df, column, numbers[-1])
        elif column:
            return json.dumps({
                "ok": False,
                "analysis": analysis,
                "error": "A hypothesized mean or reference value is required for a one-sample t-test.",
            })

    if result is None:
        return json.dumps({
            "ok": True,
            "analysis": analysis,
            "design": None,
            "roles": _json_safe(candidate),
            "plan": _json_safe(plan.get("plan", {})),
            "rows": int(df.shape[0]),
            "columns": list(map(str, df.columns)),
            "message": "The analysis was identified, but its mobile executor needs another data-structure check.",
        })

    return json.dumps({
        "ok": True,
        "analysis": analysis,
        "design": None,
        "roles": _json_safe(candidate),
        "result": _json_safe(result),
        "rows": int(df.shape[0]),
    })
