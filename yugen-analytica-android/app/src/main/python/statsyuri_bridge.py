import io
import json

import pandas as pd

from src.question_engine import interpret_question
from src.statistics import get_numeric_statistics, one_way_anova, two_sample_t_test, chi_square_independence, simple_linear_regression


def _jsonable(value):
    if isinstance(value, pd.DataFrame):
        return {"columns": [str(x) for x in value.columns], "rows": value.where(pd.notna(value), None).to_dict(orient="records")}
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
        try:
            import pdfplumber
            stream.seek(0)
            tables = []
            with pdfplumber.open(stream) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables() or []:
                        if table and len(table) >= 2:
                            header = [str(x or "").strip() for x in table[0]]
                            rows = table[1:]
                            if any(header) and rows:
                                tables.append(pd.DataFrame(rows, columns=header))
            if tables:
                return pd.concat(tables, ignore_index=True), text
        except Exception:
            pass
        return None, text
    raise ValueError("Supported files: CSV, XLSX, XLS and PDF.")


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
        return {"status": "solved", "test": analysis, "response": response, "treatment": treatment, "block": block, "anova": _anova_formula(df[[response, treatment, block]].dropna(), response, [treatment, block])}

    if "Latin-square" in analysis:
        response = _find_column(df, candidate, ["response", "yield", "outcome"])
        treatment = _find_column(df, candidate, ["treatment", "factor", "group"])
        row = _find_column(df, candidate, ["row"])
        column = _find_column(df, candidate, ["column"])
        if not (response and treatment and row and column):
            return {"status": "error", "message": "Latin Square was detected, but treatment, row, column, or response could not be matched."}
        return {"status": "solved", "test": analysis, "response": response, "treatment": treatment, "row": row, "column": column, "anova": _anova_formula(df[[response, treatment, row, column]].dropna(), response, [row, column, treatment])}

    if analysis == "One-way ANOVA":
        return {"status": "solved", "test": analysis, "result": _jsonable(one_way_anova(df, candidate.get("response"), candidate.get("grouping")))}

    if analysis == "Welch two-sample t-test":
        grouping = candidate.get("grouping")
        levels = df[grouping].dropna().unique().tolist() if grouping in df.columns else []
        if len(levels) >= 2:
            return {"status": "solved", "test": analysis, "result": _jsonable(two_sample_t_test(df, candidate.get("response"), grouping, levels[0], levels[1]))}

    if analysis == "Chi-square test of independence":
        return {"status": "solved", "test": analysis, "result": _jsonable(chi_square_independence(df, candidate.get("variable_1"), candidate.get("variable_2")))}

    if analysis == "Simple linear regression":
        return {"status": "solved", "test": analysis, "result": _jsonable(simple_linear_regression(df, candidate.get("predictor"), candidate.get("response")))}

    return {"status": "solved", "test": analysis, "message": "The analysis was identified, but this offline build does not yet expose that calculation through the mobile UI."}


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
    result = {"status": plan.get("status"), "confidence": plan.get("confidence"), "reason": plan.get("reason"), "analysis_requests": plan.get("analysis_requests", []), "candidates": plan.get("candidates", []), "plan": plan.get("plan", {}), "columns": [str(c) for c in df.columns] if df is not None else []}
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
    if df is None:
        return json.dumps({"status": "error", "message": "A tabular dataset is required for Solve. PDF text or OCR can still be used for question understanding."})
    return json.dumps(_jsonable(_solve(interpret_question(df=df, question=source_text), df)), ensure_ascii=False)
