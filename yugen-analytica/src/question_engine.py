"""Natural-language question interpretation helpers for StatsYuri.

This module intentionally handles language interpretation, not statistical
calculation. Its output must be validated against the dataset before any
analysis is executed.
"""

import re
from difflib import SequenceMatcher

import pandas as pd


INTENT_PATTERNS = {
    "paired_comparison": [
        r"\bbefore\b.*\bafter\b",
        r"\bafter\b.*\bbefore\b",
        r"\bpre\b.*\bpost\b",
        r"\bpost\b.*\bpre\b",
        r"\bimprov\w*\b.*\bafter\b",
        r"\bchange\w*\b.*\bbefore\b",
    ],
    "prediction": [
        r"\bpredict\w*\b",
        r"\bforecast\w*\b",
        r"\bestimat\w*\b.*\bfrom\b",
    ],
    "association": [
        r"\bassociat\w*\b",
        r"\bindependent\b.*\bof\b",
        r"\brelated\b",
        r"\brelationship\b",
        r"\bconnected\b",
    ],
    "correlation": [
        r"\bcorrelat\w*\b",
        r"\brelationship\b.*\bbetween\b",
        r"\brelated\b.*\bto\b",
    ],
    "group_comparison": [
        r"\bdiffer\w*\b.*\bbetween\b",
        r"\bcompare\w*\b",
        r"\bdifference\b",
        r"\beffect\b.*\bon\b",
        r"\baffect\w*\b",
        r"\bimpact\w*\b",
        r"\bwhich\b.*\bgroup\b",
    ],
    "categorical_association": [
        r"\bassociat\w*\b.*\bcategor\w*\b",
        r"\bdepend\w*\b.*\bcategory\b",
        r"\bindependent\b.*\bcategor\w*\b",
    ],
}

SYNONYMS = {
    "affect": ["effect", "impact", "influence"],
    "score": ["scores", "marks", "grade", "grades"],
    "yield": ["production", "output"],
    "study": ["studying", "study time"],
    "group": ["groups", "treatment", "treatments"],
    "before": ["pre", "baseline"],
    "after": ["post", "followup", "follow-up"],
}


def _normalize(text):
    text = str(text).lower().replace("_", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _column_aliases(column):
    normalized = _normalize(column)
    aliases = {normalized, normalized.replace(" ", "")}
    aliases.update(normalized.split())
    return aliases


def _match_columns(question, columns, threshold=0.72):
    """Match explicit column names and close natural-language variants."""
    normalized_question = _normalize(question)
    matches = []

    for column in columns:
        aliases = _column_aliases(column)
        score = 0.0
        evidence = ""

        for alias in aliases:
            if len(alias) >= 3 and alias in normalized_question:
                score = max(score, 1.0)
                evidence = alias

        # Compare the full column name with question tokens/phrases.
        if score < 1.0:
            question_tokens = normalized_question.split()
            column_words = normalized_question.split()
            for start in range(max(1, len(question_tokens) - 3)):
                phrase = " ".join(question_tokens[start:start + max(1, len(_normalize(column).split()))])
                similarity = SequenceMatcher(None, phrase, _normalize(column)).ratio()
                if similarity > score:
                    score = similarity
                    evidence = phrase

        if score >= threshold:
            matches.append({
                "column": column,
                "score": round(score, 3),
                "evidence": evidence,
            })

    return sorted(matches, key=lambda item: item["score"], reverse=True)


def _detect_intents(question):
    text = _normalize(question)
    scores = {}

    for intent, patterns in INTENT_PATTERNS.items():
        score = sum(bool(re.search(pattern, text)) for pattern in patterns)
        if score:
            scores[intent] = score

    # Correlation is a more specific interpretation than generic association.
    if "correlation" in scores:
        scores["association"] = max(0, scores.get("association", 0) - 1)

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def _column_profile(df):
    identifier_tokens = ("id", "index", "serial", "code", "roll", "record")

    def is_identifier(column):
        name = str(column).strip().lower()
        return (
            name in identifier_tokens
            or any(
                name.startswith(token + "_") or name.endswith("_" + token)
                for token in identifier_tokens
            )
        )

    numeric = [
        column for column in df.select_dtypes(include="number").columns
        if not is_identifier(column)
    ]

    categorical = [
        column for column in df.columns
        if column not in numeric
        and not is_identifier(column)
        and 2 <= df[column].nunique(dropna=True) <= max(20, int(len(df) * 0.5))
    ]

    return numeric, categorical


def interpret_question(df, question):
    """Interpret a natural-language research question against a dataset.

    Returns an explainable structure that must be validated before execution.
    """
    if not question or not str(question).strip():
        return {
            "status": "empty",
            "intent": None,
            "confidence": 0.0,
            "matched_columns": [],
            "candidates": [],
            "reason": "Enter a research question.",
        }

    numeric, categorical = _column_profile(df)
    intents = _detect_intents(question)
    all_columns = list(df.columns)
    matches = _match_columns(question, all_columns)

    intent = intents[0][0] if intents else None
    intent_score = intents[0][1] if intents else 0

    explicit = [item for item in matches if item["score"] >= 0.99]
    likely_numeric = [item for item in matches if item["column"] in numeric]
    likely_categorical = [item for item in matches if item["column"] in categorical]

    candidates = []

    if intent in {"group_comparison", "categorical_association"}:
        if likely_categorical and likely_numeric:
            for group in likely_categorical[:2]:
                for response in likely_numeric[:2]:
                    levels = df[group["column"]].dropna().nunique()
                    if levels == 2:
                        test = "Welch two-sample t-test"
                    elif levels >= 3:
                        test = "One-way ANOVA"
                    else:
                        continue
                    candidates.append({
                        "analysis": test,
                        "response": response["column"],
                        "grouping": group["column"],
                        "reason": f"{group['column']} has {levels} observed groups and {response['column']} is numeric.",
                    })

        if intent == "categorical_association" and len(likely_categorical) >= 2:
            candidates.append({
                "analysis": "Chi-square test of independence",
                "variable_1": likely_categorical[0]["column"],
                "variable_2": likely_categorical[1]["column"],
                "reason": "Two categorical variables were identified.",
            })

    elif intent in {"correlation", "association"}:
        if len(likely_numeric) >= 2:
            candidates.append({
                "analysis": "Pearson correlation + simple linear regression",
                "variable_1": likely_numeric[0]["column"],
                "variable_2": likely_numeric[1]["column"],
                "reason": "Two numeric variables were identified.",
            })

    elif intent == "prediction":
        if len(likely_numeric) >= 2:
            candidates.append({
                "analysis": "Simple linear regression",
                "predictor": likely_numeric[0]["column"],
                "response": likely_numeric[1]["column"],
                "reason": "Two numeric variables were identified; regression can model a response from a predictor.",
            })

    elif intent == "paired_comparison":
        if len(likely_numeric) >= 2:
            candidates.append({
                "analysis": "Paired t-test candidate",
                "variable_1": likely_numeric[0]["column"],
                "variable_2": likely_numeric[1]["column"],
                "reason": "The wording suggests repeated measurements such as before/after.",
            })

    # A generic comparison can still be inferred from a strong explicit
    # numeric + categorical pairing even if no special intent matched.
    if not candidates and len(likely_numeric) == 1 and len(likely_categorical) == 1:
        levels = df[likely_categorical[0]["column"]].dropna().nunique()
        if levels in (2, 3) and any(word in _normalize(question) for word in ("compare", "difference", "effect", "affect")):
            candidates.append({
                "analysis": "Welch two-sample t-test" if levels == 2 else "One-way ANOVA",
                "response": likely_numeric[0]["column"],
                "grouping": likely_categorical[0]["column"],
                "reason": "The wording indicates a group comparison and the dataset contains a compatible response/factor pair.",
            })

    if explicit:
        match_quality = 1.0
    elif matches:
        match_quality = matches[0]["score"]
    else:
        match_quality = 0.0

    confidence = min(
        0.98,
        0.25 * min(intent_score, 2) + 0.45 * match_quality + (0.30 if candidates else 0.0),
    )

    if not candidates:
        status = "needs_clarification"
        reason = (
            "The question could not be mapped confidently to a compatible "
            "analysis structure in the current dataset."
        )
    elif len(candidates) > 1:
        status = "ambiguous"
        reason = "More than one compatible interpretation was found."
    else:
        status = "ready"
        reason = candidates[0]["reason"]

    return {
        "status": status,
        "intent": intent,
        "confidence": round(confidence, 2),
        "matched_columns": matches[:6],
        "candidates": candidates[:6],
        "reason": reason,
    }
