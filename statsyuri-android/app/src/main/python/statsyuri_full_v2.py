import json
from pathlib import Path

import pandas as pd
import statsyuri_bridge as base
from src.question_engine import interpret_question


def _load(path):
    suffix = Path(path).suffix.lower()
    if suffix == '.csv': return pd.read_csv(path)
    if suffix in {'.xlsx', '.xls'}: return pd.read_excel(path)
    raise ValueError('Offline APK currently supports CSV and Excel files.')


def _candidate(analysis, **kwargs):
    item = {'analysis': analysis}
    item.update(kwargs)
    return item


def _automatic_candidates(df):
    numeric = base._numeric_columns(df)
    categorical = base._categorical_columns(df)
    candidates = []
    for group in categorical:
        levels = df[group].nunique(dropna=True)
        if levels >= 3 and numeric:
            candidates.append(_candidate('One-way ANOVA', response=numeric[0], grouping=group,
                reason=f"{group} has {levels} groups and {numeric[0]} is numeric, so ANOVA compares the group means."))
            break
    for group in categorical:
        if df[group].nunique(dropna=True) == 2 and numeric:
            candidates.append(_candidate('Welch two-sample t-test', response=numeric[0], grouping=group,
                reason=f"{group} has two groups, so Welch's t-test compares their means without assuming equal variances."))
            break
    if len(numeric) >= 2:
        candidates.append(_candidate('Pearson correlation + simple linear regression', variable_1=numeric[0], variable_2=numeric[1],
            reason=f"{numeric[0]} and {numeric[1]} are numeric, so StatsYuri can measure their linear association and fit a regression."))
        candidates.append(_candidate('Simple linear regression', predictor=numeric[0], response=numeric[1],
            reason=f"Simple regression can model {numeric[1]} using {numeric[0]} as the predictor."))
    if len(categorical) >= 2:
        candidates.append(_candidate('Chi-square test of independence', variable_1=categorical[0], variable_2=categorical[1],
            reason=f"{categorical[0]} and {categorical[1]} are categorical, so chi-square can test whether they are associated."))
    return candidates


def analyze_full(question, file_path=None):
    question = (question or '').strip()
    if not file_path: raise ValueError('Full analysis needs a dataset so compatible tests can be calculated.')
    df = _load(file_path)
    if question:
        interpretation = interpret_question(df, question)
        candidates = interpretation.get('candidates', [])
        if not candidates:
            candidates = _automatic_candidates(df)
            reason = 'The question was not mapped confidently, so StatsYuri inspected the dataset structure and selected compatible analyses.'
        else:
            reason = interpretation.get('reason', 'Compatible analyses were selected from the question and dataset.')
        plan = interpretation.get('plan', {})
        problem_type = interpretation.get('problem_type', 'Statistical problem')
    else:
        interpretation = {}
        candidates = _automatic_candidates(df)
        reason = 'No question was entered. StatsYuri generated compatible analyses directly from the dataset structure.'
        plan = {'objective': reason}
        problem_type = 'Automatic dataset analysis'

    analyses, seen = [], set()
    for candidate in candidates:
        key = tuple(candidate.get(k) for k in ('analysis','response','grouping','variable_1','variable_2','predictor'))
        if key in seen: continue
        seen.add(key)
        try:
            execution = base._execute(df, candidate)
            analyses.append({'analysis': candidate.get('analysis','Analysis'), 'ok': True,
                'reason': candidate.get('reason') or reason, 'execution': execution, 'candidate': candidate})
        except Exception as exc:
            analyses.append({'analysis': candidate.get('analysis','Analysis'), 'ok': False,
                'reason': candidate.get('reason') or reason, 'error': str(exc), 'candidate': candidate})

    return json.dumps({'app':'StatsYuri Offline','mode':'Full','rows':int(df.shape[0]),
        'columns':[str(c) for c in df.columns],'problem_type':problem_type,'reason':reason,'plan':plan,
        'analysis_count':len(analyses),'analyses':analyses,
        'confirmed_analysis':analyses[0]['analysis'] if analyses else None,
        'ok':any(x.get('ok') for x in analyses)}, default=str)
