import json
from pathlib import Path

import pandas as pd

import statsyuri_bridge as base
from src.question_engine import interpret_question


def _load(path):
    suffix = Path(path).suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(path)
    if suffix in {'.xlsx', '.xls'}:
        return pd.read_excel(path)
    raise ValueError('Offline APK currently supports CSV and Excel files.')


def _candidate(df, analysis, **kwargs):
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
            candidates.append(_candidate(
                df, 'One-way ANOVA', response=numeric[0], grouping=group,
                reason=f"{group} has {levels} groups and {numeric[0]} is numeric, so ANOVA can compare the group means."
            ))
            candidates.append(_candidate(
                df, 'Kruskal-Wallis test', response=numeric[0], grouping=group,
                reason=f"{group} has {levels} groups and {numeric[0]} is numeric, so Kruskal-Wallis provides a non-parametric group comparison."
            ))
            break

    for group in categorical:
        if df[group].nunique(dropna=True) == 2 and numeric:
            candidates.append(_candidate(
                df, 'Welch two-sample t-test', response=numeric[0], grouping=group,
                reason=f"{group} has two groups, so Welch's t-test compares their means without assuming equal variances."
            ))
            candidates.append(_candidate(
                df, 'Mann-Whitney U test', response=numeric[0], grouping=group,
                reason=f"{group} has two groups, so Mann-Whitney provides a non-parametric comparison."
            ))
            break

    if len(numeric) >= 2:
        candidates.append(_candidate(
            df, 'Pearson correlation + simple linear regression',
            variable_1=numeric[0], variable_2=numeric[1],
            reason=f"{numeric[0]} and {numeric[1]} are numeric, so StatsYuri can measure their linear association and fit a simple regression."
        ))
        candidates.append(_candidate(
            df, 'Simple linear regression', predictor=numeric[0], response=numeric[1],
            reason=f"Simple regression can model {numeric[1]} using {numeric[0]} as the predictor."
        ))

    if len(categorical) >= 2:
        candidates.append(_candidate(
            df, 'Chi-square test of independence',
            variable_1=categorical[0], variable_2=categorical[1],
            reason=f"Both {categorical[0]} and {categorical[1]} are categorical, so chi-square can test whether they are associated."
        ))

    return candidates


def _question_candidates(df, question):
    interpretation = interpret_question(df, question)
    candidates = interpretation.get('candidates', [])
    return interpretation, candidates


def analyze_full(question, file_path=None):
    question = (question or '').strip()
    if not file_path:
        raise ValueError('Full analysis needs a dataset so compatible tests can be calculated.')
    df = _load(file_path)

    if question:
        interpretation, candidates = _question_candidates(df, question)
        if not candidates:
            candidates = _automatic_candidates(df)
            reason = 'The question was not mapped confidently, so StatsYuri inspected the dataset structure and selected compatible analyses.'
        else:
            reason = interpretation.get('reason', 'Compatible analyses were selected from the question and dataset.')
        plan = interpretation.get('plan', {})
    else:
        candidates = _automatic_candidates(df)
        reason = 'No question was entered. StatsYuri generated compatible analyses directly from the dataset structure.'
        plan = {'objective': reason}

    analyses = []
    seen = set()
    for candidate in candidates:
        name = candidate.get('analysis', '')
        key = (name, candidate.get('response'), candidate.get('grouping'), candidate.get('variable_1'), candidate.get('variable_2'), candidate.get('predictor'))
        if key in seen:
            continue
        seen.add(key)
        try:
            execution = base._execute(df, candidate)
            analyses.append({
                'analysis': name,
                'ok': True,
                'reason': candidate.get('reason') or reason,
                'execution': execution,
                'candidate': candidate,
            })
        except Exception as exc:
            analyses.append({
                'analysis': name,
                'ok': False,
                'reason': candidate.get('reason') or reason,
                'error': str(exc),
                'candidate': candidate,
            })

    return json.dumps({
        'app': 'StatsYuri Offline',
        'mode': 'Full',
        'rows': int(df.shape[0]),
        'columns': [str(c) for c in df.columns],
        'problem_type': interpretation.get('problem_type', 'Dataset analysis') if question else 'Automatic dataset analysis',
        'reason': reason,
        'plan': plan,
        'analysis_count': len(analyses),
        'analyses': analyses,
        'confirmed_analysis': analyses[0]['analysis'] if analyses else None,
        'ok': any(item.get('ok') for item in analyses),
    }, default=str)
