"""Offline bridge for the StatsYuri Android app.

This module is intentionally UI-independent. Flutter passes a local file path and
research question here; the existing StatsYuri Python analysis modules do the work.
"""

import json
from pathlib import Path

import pandas as pd

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

    # Keep the first mobile build conservative: it exposes the detected plan
    # and dataset metadata while the common non-design executors are wired next.
    return json.dumps({
        "ok": True,
        "analysis": analysis,
        "design": None,
        "roles": _json_safe(candidate),
        "plan": _json_safe(plan.get("plan", {})),
        "rows": int(df.shape[0]),
        "columns": list(map(str, df.columns)),
        "message": "Analysis plan detected. Numerical execution for this analysis is being connected to the offline mobile engine.",
    })
