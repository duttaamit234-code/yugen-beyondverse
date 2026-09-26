"""Offline bridge for the StatsYuri Android app."""

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


def _analysis_columns(df):
    numeric = [c for c in df.select_dtypes(include="number").columns if not any(token in str(c).strip().lower().split("_") for token in ("id", "index", "serial", "code", "roll", "record"))]
    categorical = [c for c in df.columns if c not in numeric and 2 <= df[c].nunique(dropna=True) <= max(20, int(len(df) * 0.5)) and not any(token in str(c).strip().lower().split("_") for token in ("id", "index", "serial", "code", "roll", "record"))]
    return numeric, categorical


def _auto_plan(df):
    """Choose a defensible first analysis directly from dataset structure."""
    numeric, categorical = _analysis_columns(df)
    if categorical and numeric:
        group = sorted(categorical, key=lambda c: (-df[c].nunique(dropna=True), str(c)))[0]
        response = numeric[0]
        levels = int(df[group].dropna().nunique())
        if levels >= 3:
            analysis = "One-way ANOVA"
            reason = f"No question was entered. {group} has {levels} groups and {response} is a numerical outcome, so an omnibus group comparison can be calculated automatically."
        elif levels == 2:
            analysis = "Welch two-sample t-test"
            reason = f"No question was entered. {group} has two groups and {response} is a numerical outcome, so a two-group comparison can be calculated automatically."
        else:
            return None
        return {"analysis": analysis, "response": response, "grouping": group, "alpha": 0.05, "reason": reason}
    if len(numeric) >= 2:
        return {"analysis": "Pearson correlation + simple linear regression", "variable_1": numeric[0], "variable_2": numeric[1], "alpha": 0.05, "reason": f"No question was entered. Two numerical variables ({numeric[0]} and {numeric[1]}) were found, so their linear association and fitted regression are calculated automatically."}
    if len(categorical) >= 2:
        return {"analysis": "Chi-square test of independence", "variable_1": categorical[0], "variable_2": categorical[1], "alpha": 0.05, "reason": f"No question was entered. Two categorical variables ({categorical[0]} and {categorical[1]}) were found, so their association is tested automatically."}
    return None


def _calculation_details(df, analysis, result, candidate):
    """Return human-readable calculation steps alongside the numeric result."""
    if not result:
        return None
    if analysis == "One-way ANOVA":
        group, response = candidate.get("grouping"), candidate.get("response")
        data = df[[group, response]].dropna()
        groups = [g for g in data[group].unique() if len(data[data[group] == g][response]) >= 2]
        if len(groups) >= 3:
            sizes = [len(data[data[group] == g][response]) for g in groups]
            means = [float(data[data[group] == g][response].mean()) for g in groups]
            overall = float(data[response].mean())
            ss_between = sum(n * (m - overall) ** 2 for n, m in zip(sizes, means))
            ss_within = sum(float(((data[data[group] == g][response] - m) ** 2).sum()) for g, m in zip(groups, means))
            df_between, df_within = len(groups) - 1, sum(sizes) - len(groups)
            ms_between, ms_within = ss_between / df_between, ss_within / df_within
            return {"steps": [f"Group means: {', '.join(f'{m:.4f}' for m in means)}", f"Overall mean = {overall:.4f}", f"SS_between = Σ nᵢ(x̄ᵢ − x̄)² = {ss_between:.4f}", f"SS_within = ΣΣ(xᵢⱼ − x̄ᵢ)² = {ss_within:.4f}", f"MS_between = {ss_between:.4f} / {df_between} = {ms_between:.4f}", f"MS_within = {ss_within:.4f} / {df_within} = {ms_within:.4f}", f"F = MS_between / MS_within = {ms_between:.4f} / {ms_within:.4f} = {float(result['F-Statistic']):.4f}", f"Decision at α = 0.05: {'statistically significant' if float(result['P-Value']) < 0.05 else 'not statistically significant'} (p = {float(result['P-Value']):.6g})"], "formula": "F = MS_between / MS_within"}
    if analysis == "Welch two-sample t-test":
        group, response = candidate.get("grouping"), candidate.get("response")
        levels = list(df[group].dropna().unique())[:2]
        if len(levels) == 2:
            a = df[df[group] == levels[0]][response].dropna().astype(float)
            b = df[df[group] == levels[1]][response].dropna().astype(float)
            v1, v2 = a.var(ddof=1), b.var(ddof=1)
            se = ((v1 / len(a)) + (v2 / len(b))) ** 0.5
            return {"steps": [f"Mean₁ = {a.mean():.4f}, Mean₂ = {b.mean():.4f}", f"Mean difference = {a.mean() - b.mean():.4f}", f"SE = √(s₁²/n₁ + s₂²/n₂) = {se:.4f}", f"t = (Mean₁ − Mean₂) / SE = {float(result['T-Statistic']):.4f}", f"Welch df = {float(result['Degrees of Freedom']):.4f}", f"Decision at α = 0.05: {'statistically significant' if float(result['P-Value']) < 0.05 else 'not statistically significant'} (p = {float(result['P-Value']):.6g})"], "formula": "t = (x̄₁ − x̄₂) / √(s₁²/n₁ + s₂²/n₂)"}
    if analysis in {"Pearson correlation", "Pearson correlation + simple linear regression"}:
        r = result.get("r")
        if r is None and isinstance(result.get("correlation"), dict): r = result["correlation"].get("r")
        p = result.get("p_value")
        if p is None and isinstance(result.get("correlation"), dict): p = result["correlation"].get("p_value")
        steps = [f"Pearson r = {float(r):.4f}", f"p-value = {float(p):.6g}", f"Decision at α = 0.05: {'statistically significant' if float(p) < 0.05 else 'not statistically significant'}"]
        if isinstance(result.get("regression"), dict):
            reg = result["regression"]
            steps.extend([f"Regression slope = {float(reg.get('Slope', 0)):.4f}", f"Intercept = {float(reg.get('Intercept', 0)):.4f}", f"R² = {float(reg.get('R-Squared', 0)):.4f}"])
        return {"steps": steps, "formula": "r = cov(X,Y) / (sₓ sᵧ)"}
    if analysis == "Chi-square test of independence":
        return {"steps": [f"Observed table = counts of {candidate.get('variable_1')} × {candidate.get('variable_2')}", "Expected count = (row total × column total) / grand total", f"χ² = Σ (O − E)² / E = {float(result['Chi-Square']):.4f}", f"Degrees of freedom = {int(result['Degrees of Freedom'])}", f"Decision at α = 0.05: {'statistically significant' if float(result['P-Value']) < 0.05 else 'not statistically significant'} (p = {float(result['P-Value']):.6g})"], "formula": "χ² = Σ (O − E)² / E"}
    if analysis == "Simple linear regression":
        return {"steps": [f"Slope = {float(result.get('Slope', 0)):.4f}", f"Intercept = {float(result.get('Intercept', 0)):.4f}", f"R² = {float(result.get('R-Squared', 0)):.4f}", f"Slope p-value = {float(result.get('Slope P-Value', 0)):.6g}"], "formula": "ŷ = b₀ + b₁x"}
    if analysis == "One-sample t-test":
        return {"steps": [f"Sample mean = {float(result['Sample Mean']):.4f}", f"Hypothesized mean = {float(result['Hypothesized Mean']):.4f}", f"t = (x̄ − μ₀) / (s/√n) = {float(result['T-Statistic']):.4f}", f"p-value = {float(result['P-Value']):.6g}"], "formula": "t = (x̄ − μ₀) / (s/√n)"}
    return None


def analyze_file(path, question="", mode="efficient"):
    df = _load(path)
    question = str(question or "").strip()
    if not question:
        candidate = _auto_plan(df)
        if candidate is None:
            numeric, _ = _analysis_columns(df)
            descriptive = {}
            for column in numeric:
                series = pd.to_numeric(df[column], errors="coerce").dropna()
                if len(series):
                    descriptive[str(column)] = {"n": int(series.size), "mean": float(series.mean()), "median": float(series.median()), "sd": float(series.std(ddof=1)) if len(series) > 1 else None, "min": float(series.min()), "max": float(series.max())}
            return json.dumps({"ok": True, "analysis": "Descriptive statistics", "rows": int(df.shape[0]), "columns": list(map(str, df.columns)), "reason": "No single inferential analysis could be selected safely from the dataset structure, so descriptive statistics were calculated instead.", "result": _json_safe(descriptive), "calculation": {"steps": ["For each numerical column: calculate n, mean, median, sample standard deviation, minimum and maximum."], "formula": "mean = Σx / n"}})
    else:
        plan = interpret_question(df, question)
        if not plan.get("candidates"):
            return json.dumps({"ok": False, "error": plan.get("reason", "More information is needed to select an analysis."), "plan": _json_safe(plan)})
        candidate = plan["candidates"][0]
    analysis = candidate.get("analysis", "")
    design = candidate.get("design")
    if design:
        result = run_experimental_design_analysis(df, question, design=design)
        calculation = _calculation_details(df, analysis, result.get("result"), candidate) if result.get("result") else None
        return json.dumps({"ok": result.get("error") is None, "analysis": analysis, "design": design, "roles": _json_safe(result.get("roles", {})), "result": _json_safe(result.get("result")), "calculation": _json_safe(calculation), "error": result.get("error"), "rows": int(df.shape[0])})
    response, grouping = candidate.get("response"), candidate.get("grouping")
    variable_1, variable_2 = candidate.get("variable_1"), candidate.get("variable_2")
    result = None
    if analysis == "One-way ANOVA" and response and grouping:
        result = one_way_anova(df, response, grouping)
    elif analysis == "Welch two-sample t-test" and response and grouping:
        levels = list(df[grouping].dropna().unique())[:2]
        if len(levels) == 2:
            result = two_sample_t_test(df, response, grouping, levels[0], levels[1])
    elif analysis == "Chi-square test of independence" and variable_1 and variable_2:
        result = chi_square_independence(df, variable_1, variable_2)
    elif analysis == "Simple linear regression":
        predictor, outcome = candidate.get("predictor") or variable_1, candidate.get("response") or variable_2
        if predictor and outcome:
            result = simple_linear_regression(df, predictor, outcome)
    elif analysis == "Pearson correlation":
        x, y = variable_1 or response, variable_2
        if x and y:
            clean = df[[x, y]].dropna()
            r_value, p_value = stats.pearsonr(clean[x], clean[y])
            result = {"r": float(r_value), "p_value": float(p_value), "n": int(len(clean))}
    elif analysis == "Pearson correlation + simple linear regression":
        x, y = variable_1, variable_2
        if x and y:
            clean = df[[x, y]].dropna()
            r_value, p_value = stats.pearsonr(clean[x], clean[y])
            result = {"correlation": {"r": float(r_value), "p_value": float(p_value), "n": int(len(clean))}, "regression": _json_safe(simple_linear_regression(df, x, y))}
    elif analysis in {"Paired t-test", "Paired t-test candidate"}:
        x, y = variable_1 or response, variable_2
        if x and y:
            clean = df[[x, y]].dropna()
            statistic, p_value = stats.ttest_rel(clean[x], clean[y])
            result = {"t": float(statistic), "p_value": float(p_value), "n_pairs": int(len(clean))}
    elif analysis == "One-sample t-test":
        column = response or variable_1
        numbers = [float(x) for x in re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", question) if abs(float(x)) > 0.049]
        if column and numbers:
            result = one_sample_t_test(df, column, numbers[-1])
        elif column:
            return json.dumps({"ok": False, "analysis": analysis, "error": "A hypothesized mean or reference value is required for a one-sample t-test."})
    if result is None:
        return json.dumps({"ok": False, "analysis": analysis, "design": None, "roles": _json_safe(candidate), "plan": _json_safe(candidate), "rows": int(df.shape[0]), "columns": list(map(str, df.columns)), "error": "The analysis was identified, but the dataset does not contain enough compatible observations to calculate it."})
    return json.dumps({"ok": True, "analysis": analysis, "design": None, "roles": _json_safe(candidate), "result": _json_safe(result), "calculation": _json_safe(_calculation_details(df, analysis, result, candidate)), "rows": int(df.shape[0])})
