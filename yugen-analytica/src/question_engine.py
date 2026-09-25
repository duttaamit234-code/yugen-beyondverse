"""Natural-language statistical problem interpretation for StatsYuri.

This module converts ordinary research/problem statements into an explainable
analysis plan. It does not calculate statistics. The dataset and Python
statistical functions remain authoritative for validation and execution.
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
        r"\bpre[- ]?treatment\b.*\bpost[- ]?treatment\b",
        r"\bimprov\w*\b.*\bafter\b",
        r"\bchange\w*\b.*\bbefore\b",
        r"\bchange\w*\b.*\bafter\b",
    ],
    "prediction": [
        r"\bpredict\w*\b",
        r"\bforecast\w*\b",
        r"\bestimat\w*\b.*\bfrom\b",
        r"\buse .* to predict\b",
    ],
    "categorical_association": [
        r"\bchi[- ]?square\b",
        r"\bcategor\w*\b.*\bassociat\w*\b",
        r"\bdepend\w*\b.*\bcategory\b",
        r"\bindependent\b.*\bcategor\w*\b",
        r"\btwo categorical\b",
    ],
    "correlation": [
        r"\bcorrelat\w*\b",
        r"\brelationship\b.*\bbetween\b",
        r"\brelated\b.*\bto\b",
        r"\blinear relationship\b",
        r"\blinear association\b",
    ],
    "group_comparison": [
        r"\bdiffer\w*\b.*\bbetween\b",
        r"\bcompare\w*\b",
        r"\bdifference\b",
        r"\bmean difference\b",
        r"\bmean[s]?\b.*\bbetween\b",
        r"\bmean[s]?\b.*\bamong\b",
        r"\beffect\b.*\bon\b",
        r"\baffect\w*\b",
        r"\bimpact\w*\b",
        r"\bwhich\b.*\bgroup\b",
        r"\bamong\b.*\bmethods?\b",
        r"\bamong\b.*\btreatments?\b",
    ],
    "one_sample": [
        r"\btest\w*\b.*\bmean\b.*\bvalue\b",
        r"\bmean\b.*\bcompared with\b.*\bstandard\b",
        r"\bcompare\w*\b.*\bpopulation mean\b",
        r"\bagainst\b.*\bbenchmark\b",
    ],
}


# Natural-language concepts are deliberately broad. They help bridge the gap
# between a column called Exam_Score and a problem statement saying
# "examination performance", without pretending to be a general-purpose LLM.
CONCEPT_ALIASES = {
    "outcome": {
        "score", "scores", "mark", "marks", "grade", "grades", "result",
        "results", "performance", "achievement", "response", "measurement",
        "measure", "value", "yield", "production", "output", "income",
        "weight", "height", "time", "duration", "rating", "rate", "amount",
        "concentration", "temperature", "exam", "examination", "test",
        "final", "accuracy", "error", "profit", "sales",
    },
    "group": {
        "group", "groups", "method", "methods", "approach", "approaches",
        "treatment", "treatments", "type", "types", "category", "categories",
        "class", "classes", "condition", "conditions", "arm", "level",
        "levels", "technique", "techniques", "program", "programs",
        "intervention", "interventions", "diet", "variety", "varieties",
        "fertilizer", "fertilizers", "irrigation", "location", "locations",
        "teaching", "instruction", "strategy", "strategies",
    },
}

WORD_ALIASES = {
    "exam": {"exam", "examination", "exams", "examinations"},
    "score": {"score", "scores", "mark", "marks", "grade", "grades", "result", "results"},
    "performance": {"performance", "achievement", "attainment", "outcome"},
    "study": {"study", "studying", "studytime", "studyhours"},
    "attendance": {"attendance", "attend", "presence"},
    "teaching": {"teaching", "instruction", "educational"},
    "method": {"method", "methods", "approach", "approaches", "technique", "techniques", "strategy", "strategies"},
    "treatment": {"treatment", "treatments", "intervention", "interventions"},
    "yield": {"yield", "production", "output"},
    "weight": {"weight", "bodyweight", "mass"},
    "height": {"height", "stature"},
    "age": {"age", "ages"},
    "income": {"income", "earnings", "salary", "revenue"},
    "sales": {"sales", "revenue"},
}


def _normalize(text):
    text = str(text).lower().replace("_", " ")
    text = re.sub(r"[^a-z0-9%\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text):
    return set(_normalize(text).split())


def _expand_tokens(tokens):
    expanded = set(tokens)
    for token in list(tokens):
        for canonical, aliases in WORD_ALIASES.items():
            if token == canonical or token in aliases:
                expanded.update(aliases)
                expanded.add(canonical)
    return expanded


def _column_aliases(column):
    normalized = _normalize(column)
    aliases = {normalized, normalized.replace(" ", "")}
    aliases.update(normalized.split())

    # Add semantic variants for words in the column name.
    for token in normalized.split():
        for canonical, variants in WORD_ALIASES.items():
            if token == canonical or token in variants:
                aliases.update(variants)
                aliases.add(canonical)

    return aliases


def _match_columns(question, columns, threshold=0.72):
    """Match explicit names plus conservative fuzzy natural-language variants."""
    normalized_question = _normalize(question)
    question_tokens = normalized_question.split()
    matches = []

    for column in columns:
        aliases = _column_aliases(column)
        score = 0.0
        evidence = ""

        # Exact phrase or alias occurrence is the strongest evidence.
        for alias in aliases:
            if len(alias) >= 3 and alias in normalized_question:
                score = max(score, 1.0)
                evidence = alias

        # Token/phrase similarity catches "examination scores" vs "Exam_Score".
        if score < 1.0:
            column_text = _normalize(column)
            column_tokens = _expand_tokens(_tokens(column_text))
            question_expanded = _expand_tokens(_tokens(question))

            overlap = len(column_tokens & question_expanded)
            if overlap:
                token_score = overlap / max(1, len(_tokens(column_text)))
                score = max(score, min(0.94, 0.55 + 0.22 * token_score))
                evidence = " ".join(sorted(column_tokens & question_expanded))

            window = max(1, len(_tokens(column_text)))
            for start in range(0, max(1, len(question_tokens) - window + 1)):
                phrase = " ".join(question_tokens[start:start + window])
                similarity = SequenceMatcher(None, phrase, column_text).ratio()
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

    if "correlation" in scores:
        scores["association"] = max(0, scores.get("association", 0) - 1)

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def _extract_alpha(question):
    """Extract an explicitly stated significance level, defaulting to 0.05."""
    text = _normalize(question)

    percent_match = re.search(
        r"(?:at|with|using|of)?\s*(?:the\s*)?(\d+(?:\.\d+)?)\s*%\s*(?:significance|significance level|level)?",
        text,
    )
    if percent_match:
        value = float(percent_match.group(1)) / 100
        if 0 < value < 1:
            return value

    alpha_match = re.search(
        r"(?:alpha|α)\s*(?:=|of|at)?\s*(0?\.\d+)",
        text,
    )
    if alpha_match:
        value = float(alpha_match.group(1))
        if 0 < value < 1:
            return value

    return 0.05


def _column_profile(df):
    identifier_tokens = ("id", "index", "serial", "code", "roll", "record")

    def is_identifier(column):
        name = str(column).strip().lower()
        return (
            name in identifier_tokens
            or any(
                name.startswith(token + "_")
                or name.endswith("_" + token)
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


def _semantic_column_score(question, df, column, role):
    """Score how well a column's meaning fits a role described in the text."""
    q = _normalize(question)
    q_tokens = _expand_tokens(_tokens(q))
    column_tokens = _expand_tokens(_tokens(column))

    score = 0.0
    evidence = []

    # Column name semantics.
    overlap = q_tokens & column_tokens
    if overlap:
        score += min(0.55, 0.20 * len(overlap))
        evidence.extend(sorted(overlap))

    # Role words in the problem statement.
    role_words = CONCEPT_ALIASES[role]
    role_hits = q_tokens & _expand_tokens(role_words)
    if role_hits:
        score += min(0.30, 0.10 * len(role_hits))
        evidence.extend(sorted(role_hits))

    # Categorical values are useful semantic anchors: "Traditional,
    # Digital and Blended" can identify Teaching_Method even when the
    # question never says the exact column name.
    if column in df.columns and not pd.api.types.is_numeric_dtype(df[column]):
        values = {
            _normalize(value)
            for value in df[column].dropna().astype(str).unique()
            if len(_normalize(value)) >= 3
        }
        value_hits = [
            value for value in values
            if value and value in q
        ]
        if value_hits:
            score += min(0.60, 0.25 + 0.15 * len(value_hits))
            evidence.extend(value_hits[:4])

    return min(score, 1.0), ", ".join(dict.fromkeys(evidence))


def _rank_semantic_columns(question, df, columns, role):
    ranked = []
    for column in columns:
        score, evidence = _semantic_column_score(question, df, column, role)
        ranked.append({
            "column": column,
            "score": round(score, 3),
            "evidence": evidence,
        })
    return sorted(ranked, key=lambda item: item["score"], reverse=True)


def _explicit_analysis_request(question):
    text = _normalize(question)
    requests = []
    if re.search(r"\b(one[- ]way anova|analysis of variance|anova)\b", text):
        requests.append("One-way ANOVA")
    if re.search(r"\b(welch|two[- ]sample t[- ]test|independent t[- ]test)\b", text):
        requests.append("Welch two-sample t-test")
    if re.search(r"\b(chi[- ]square|chi square)\b", text):
        requests.append("Chi-square test of independence")
    if re.search(r"\b(pearson|correlation)\b", text):
        requests.append("Pearson correlation + simple linear regression")
    if re.search(r"\b(simple linear regression|regression)\b", text):
        requests.append("Simple linear regression")
    return list(dict.fromkeys(requests))


def interpret_question(df, question):
    """Turn an ordinary statistical problem into an explainable analysis plan.

    The parser can use study-design language, outcome/group semantics, and
    categorical values when the exact dataset column names are absent from the
    question. All proposed columns are still validated against the dataset.
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
    direct_matches = _match_columns(question, all_columns)

    intent = intents[0][0] if intents else None
    intent_score = intents[0][1] if intents else 0
    alpha = _extract_alpha(question)
    explicit_analyses = _explicit_analysis_request(question)

    semantic_numeric = _rank_semantic_columns(question, df, numeric, "outcome")
    semantic_categorical = _rank_semantic_columns(question, df, categorical, "group")

    explicit_numeric = [
        item for item in direct_matches
        if item["column"] in numeric
    ]
    explicit_categorical = [
        item for item in direct_matches
        if item["column"] in categorical
    ]

    # Explicit column references win. Semantic role matching is the fallback.
    likely_numeric = explicit_numeric or [
        item for item in semantic_numeric if item["score"] >= 0.38
    ]
    likely_categorical = explicit_categorical or [
        item for item in semantic_categorical if item["score"] >= 0.38
    ]

    # If the wording clearly describes a group comparison but does not name
    # the variables, the dataset structure can supply the final compatible
    # pair. This is deliberately restricted to avoid inventing a design.
    if intent == "group_comparison":
        if not likely_categorical:
            compatible = [
                item for item in semantic_categorical
                if df[item["column"]].dropna().nunique() >= 2
            ]
            likely_categorical = compatible[:2]

        if not likely_numeric and len(numeric) == 1:
            likely_numeric = [{"column": numeric[0], "score": 0.35, "evidence": "only compatible numeric response"}]

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

                    explicit_test_conflict = (
                        explicit_analyses
                        and test not in explicit_analyses
                    )
                    if explicit_test_conflict:
                        continue

                    candidates.append({
                        "analysis": test,
                        "response": response["column"],
                        "grouping": group["column"],
                        "alpha": alpha,
                        "reason": (
                            f"{group['column']} was identified as the grouping factor "
                            f"({levels} observed groups), while {response['column']} "
                            f"was identified as the numerical outcome."
                        ),
                        "evidence": {
                            "grouping": group["evidence"],
                            "response": response["evidence"],
                        },
                    })

        if intent == "categorical_association" and len(likely_categorical) >= 2:
            candidates.append({
                "analysis": "Chi-square test of independence",
                "variable_1": likely_categorical[0]["column"],
                "variable_2": likely_categorical[1]["column"],
                "alpha": alpha,
                "reason": "Two categorical variables were identified from the problem statement.",
            })

    elif intent in {"correlation", "association"}:
        if len(likely_numeric) >= 2:
            candidates.append({
                "analysis": "Pearson correlation + simple linear regression",
                "variable_1": likely_numeric[0]["column"],
                "variable_2": likely_numeric[1]["column"],
                "alpha": alpha,
                "reason": "Two numerical variables were identified as the variables in the relationship.",
            })

    elif intent == "prediction":
        if len(likely_numeric) >= 2:
            candidates.append({
                "analysis": "Simple linear regression",
                "predictor": likely_numeric[0]["column"],
                "response": likely_numeric[1]["column"],
                "alpha": alpha,
                "reason": "A prediction problem was identified with two compatible numerical variables.",
            })

    elif intent == "paired_comparison":
        if len(likely_numeric) >= 2:
            candidates.append({
                "analysis": "Paired t-test candidate",
                "variable_1": likely_numeric[0]["column"],
                "variable_2": likely_numeric[1]["column"],
                "alpha": alpha,
                "reason": "The wording suggests repeated measurements such as before and after.",
            })

    # Fallback for a natural comparison statement whose intent detector did
    # not fire strongly enough.
    if not candidates and len(likely_numeric) == 1 and len(likely_categorical) == 1:
        text = _normalize(question)
        levels = df[likely_categorical[0]["column"]].dropna().nunique()
        if levels in (2, 3) and any(
            word in text
            for word in ("compare", "difference", "effect", "affect", "impact", "among", "between")
        ):
            candidates.append({
                "analysis": "Welch two-sample t-test" if levels == 2 else "One-way ANOVA",
                "response": likely_numeric[0]["column"],
                "grouping": likely_categorical[0]["column"],
                "alpha": alpha,
                "reason": "The wording indicates a group comparison and the dataset contains a compatible response/factor pair.",
            })

    # Remove duplicate candidate structures.
    unique = []
    seen = set()
    for candidate in candidates:
        key = tuple(sorted(
            (key, str(value))
            for key, value in candidate.items()
            if key in {"analysis", "response", "grouping", "variable_1", "variable_2", "predictor"}
        ))
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    candidates = unique

    matched_columns = direct_matches[:6]

    # Surface semantic matches too, so the user can audit how the narrative
    # was translated into dataset roles.
    for item in (semantic_categorical + semantic_numeric):
        if item["score"] >= 0.38 and not any(
            existing["column"] == item["column"]
            for existing in matched_columns
        ):
            matched_columns.append(item)
    matched_columns = sorted(
        matched_columns,
        key=lambda item: item["score"],
        reverse=True,
    )[:8]

    match_quality = matched_columns[0]["score"] if matched_columns else 0.0
    semantic_quality = max(
        [item["score"] for item in semantic_numeric + semantic_categorical] or [0.0]
    )

    confidence = min(
        0.98,
        0.18 * min(intent_score, 3)
        + 0.32 * match_quality
        + 0.20 * semantic_quality
        + (0.30 if candidates else 0.0),
    )

    if not candidates:
        status = "needs_clarification"
        reason = (
            "The problem statement could not be mapped confidently to a "
            "compatible analysis structure in the current dataset."
        )
    elif len(candidates) > 1:
        status = "ambiguous"
        reason = "More than one compatible interpretation was found."
    else:
        status = "ready"
        reason = candidates[0]["reason"]

    problem_type = {
        "group_comparison": "Comparison of independent groups",
        "categorical_association": "Association between categorical variables",
        "correlation": "Relationship between numerical variables",
        "association": "Association between variables",
        "prediction": "Prediction using numerical variables",
        "paired_comparison": "Paired or before/after comparison",
        "one_sample": "One-sample mean comparison",
    }.get(intent, "Statistical problem")

    return {
        "status": status,
        "intent": intent,
        "problem_type": problem_type,
        "confidence": round(confidence, 2),
        "alpha": alpha,
        "matched_columns": matched_columns,
        "candidates": candidates[:6],
        "reason": reason,
        "analysis_requests": explicit_analyses,
    }
