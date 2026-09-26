import io
import json
import re

import pandas as pd
from scipy import stats

from src.question_engine import interpret_question
from src.statistics import (
    get_numeric_statistics,
    one_way_anova,
    two_sample_t_test,
    two_sample_t_test_wide,
    chi_square_independence,
    simple_linear_regression,
)


def _jsonable(value):
    if isinstance(value, pd.DataFrame):
        return {
            "columns": [str(x) for x in value.columns],
            "rows": value.where(pd.notna(value), None).to_dict(orient="records"),
        }
    if isinstance(value, pd.Series):
        return [_jsonable(x) for x in value.tolist()]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(x) for x in value]
    return value


def _read_data(data_bytes, filename):
    name = (filename or "").lower()
    stream = io.BytesIO(data_bytes)
    if name.endswith(".csv"):
        return pd.read_csv(stream)
    if name.endswith(".xlsx"):
        return pd.read_excel(stream, engine="openpyxl")
    if name.endswith(".xls"):
        return pd.read_excel(stream, engine="xlrd")
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(stream)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return None, text
    raise ValueError("Supported files: CSV, XLSX, XLS and text-based PDF.")


def _solve(plan, df):
    candidates = plan.get("candidates") or []
    if not candidates:
        return {"status": "needs_clarification", "message": "Analyze first and provide enough information to choose a test."}

    candidate = candidates[0]
    analysis = candidate.get("analysis", "")

    if "Randomized-block" in analysis:
        response = _find_column(df, candidate, ["response", "yield", "outcome"])
        treatment = _find_column(df, candidate, ["treatment", "factor", "group"])
        block = _find_column(df, candidate, ["block"])
        if not (response and treatment and block):
            return {"status": "error", "message": "RBD was detected, but the treatment, block, or response column could not be matched."}
        data = df[[response, treatment, block]].dropna().copy()
        model = _anova_formula(data, response, [treatment, block])
        return {"status": "solved", "test": analysis, "response": response, "treatment": treatment, "block": block, "anova": model}

    if "Latin-square" in analysis:
        response = _find_column(df, candidate, ["response", "yield", "outcome"])
        treatment = _find_column(df, candidate, ["treatment", "factor", "group"])
        row = _find_column(df, candidate, ["row"])
        column = _find_column(df, candidate, ["column"])
        if not (response and treatment and row and column):
            return {"status": "error", "message": "Latin Square was detected, but treatment, row, column, or response could not be matched."}
        data = df[[response, treatment, row, column]].dropna().copy()
        model = _anova_formula(data, response, [row, column, treatment])
        return {"status": "solved", "test": analysis, "response": response, "treatment": treatment, "row": row, "column": column, "anova": model}

    if analysis == "One-way ANOVA":
        response = candidate.get("response")
        grouping = candidate.get("grouping")
        if response and grouping:
            return {"status": "solved", "test": analysis, "result": _jsonable(one_way_anova(df, response, grouping))}

    if analysis == "Welch two-sample t-test":
        response = candidate.get("response")
        grouping = candidate.get("grouping")
        if response and grouping:
            levels = df[grouping].dropna().unique().tolist()
            if len(levels) >= 2:
                return {"status": "solved", "test": analysis, "result": _jsonable(two_sample_t_test(df, response, grouping, levels[0], levels[1]))}

    if analysis == "Chi-square test of independence":
        return {"status": "solved", "test": analysis, "result": _jsonable(chi_square_independence(df, candidate.get("variable_1"), candidate.get("variable_2")))}

    if analysis == "Simple linear regression":
        return {"status": "solved", "test": analysis, "result": _jsonable(simple_linear_regression(df, candidate.get("predictor"), candidate.get("response")))}

    return {"status": "solved", "test": analysis, "message": "The analysis was identified. This mobile build currently exposes the matching core calculation when supported by the offline engine."}


def _find_column(df, candidate, keys):
    for key in keys:
        value = candidate.get(key)
        if value in df.columns:
            return value
    lowered = {str(c).lower(): c for c in df.columns}
    for key in keys:
        for low, original in lowered.items():
            if key in low:
                return original
    return None


def _anova_formula(df, response, factors):
    from statsmodels.formula.api import ols
    from statsmodels.stats.anova import anova_lm

    terms = " + ".join(f'C(Q("{factor}"))' for factor in factors)
    formula = f'Q("{response}") ~ {terms}'
    model = ols(formula, data=df).fit()
    table = anova_lm(model, typ=2).reset_index().rename(columns={"index": "Source"})
    table = table.rename(columns={"sum_sq": "Sum of Squares", "df": "Degrees of Freedom", "F": "F-Statistic", "PR(>F)": "P-Value"})
    return _jsonable(table)


def analyze(question, data_bytes=None, filename="", ocr_text=""):
    df = None
    source_text = question or ""
    if ocr_text:
        source_text = (source_text + "\n" + ocr_text).strip()

    if data_bytes:
        loaded = _read_data(data_bytes, filename)
        if isinstance(loaded, tuple):
            df, extracted = loaded
            source_text = (source_text + "\n" + extracted).strip()
        else:
            df = loaded

    plan = interpret_question(df=df, question=source_text)
    result = {
        "status": plan.get("status"),
        "confidence": plan.get("confidence"),
        "reason": plan.get("reason"),
        "analysis_requests": plan.get("analysis_requests", []),
        "candidates": plan.get("candidates", []),
        "plan": plan.get("plan", {}),
        "columns": [str(c) for c in df.columns] if df is not None else [],
    }
    if df is not None:
        result["numeric_summary"] = _jsonable(get_numeric_statistics(df))
    return json.dumps(_jsonable(result), ensure_ascii=False)


def solve(question, data_bytes=None, filename="", ocr_text=""):
    df = None
    source_text = question or ""
    if ocr_text:
        source_text = (source_text + "\n" + ocr_text).strip()
    if data_bytes:
        loaded = _read_data(data_bytes, filename)
        if isinstance(loaded, tuple):
            df, extracted = loaded
            source_text = (source_text + "\n" + extracted).strip()
        else:
            df = loaded
    plan = interpret_question(df=df, question=source_text)
    if df is None:
        return json.dumps({"status": "error", "message": "A dataset is required for Solve in this offline build."})
    return json.dumps(_jsonable(_solve(plan, df)), ensure_ascii=False)
