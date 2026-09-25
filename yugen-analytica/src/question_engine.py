"""Natural-language statistical problem interpretation for StatsYuri.

This module converts ordinary research/problem statements into an explainable
analysis plan. It does not calculate statistics. The dataset and Python
statistical functions remain authoritative for validation and execution.
"""

import re
from difflib import SequenceMatcher

import pandas as pd

from src.experimental_designs import experimental_design_plan, detect_experimental_design


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



def extract_tabular_text(text):
    """Extract a simple CSV/TSV/pipe table embedded in a problem statement."""
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    candidates = []
    for delimiter in (",", "\t", "|"):
        parsed = []
        for line in lines:
            raw = line.strip().strip("|")
            parts = [part.strip() for part in raw.split(delimiter)]
            if len(parts) >= 2:
                parsed.append(parts)
        if len(parsed) >= 3:
            width = len(parsed[0])
            consistent = [row for row in parsed if len(row) == width]
            if len(consistent) >= 3 and width >= 2:
                try:
                    frame = pd.DataFrame(consistent[1:], columns=consistent[0])
                    for column in frame.columns:
                        numeric = pd.to_numeric(frame[column], errors="coerce")
                        if numeric.notna().mean() >= 0.75:
                            frame[column] = numeric
                    if frame.shape[0] >= 2:
                        candidates.append(frame)
                except Exception:
                    pass
    return max(candidates, key=lambda frame: frame.shape[0] * frame.shape[1]) if candidates else None


def _text_only_plan(question):
    """Infer the required analysis from the problem statement alone."""
    text = _normalize(question)
    alpha = _extract_alpha(question)
    candidates = []

    design = detect_experimental_design(question)
    if design["design"]:
        candidates.append({
            "analysis": design["analysis"],
            "design": design["design"],
            "alpha": alpha,
            "reason": design["description"],
            "confidence": design["confidence"],
        })
        return candidates

    if any(re.search(pattern, text) for pattern in INTENT_PATTERNS["paired_comparison"]):
        candidates.append({
            "analysis": "Paired t-test",
            "alpha": alpha,
            "reason": "The wording describes paired or before/after measurements.",
        })
    elif any(re.search(pattern, text) for pattern in INTENT_PATTERNS["prediction"]):
        candidates.append({
            "analysis": "Simple linear regression",
            "alpha": alpha,
            "reason": "The problem asks to predict or estimate an outcome from another variable.",
        })
    elif any(re.search(pattern, text) for pattern in INTENT_PATTERNS["categorical_association"]):
        candidates.append({
            "analysis": "Chi-square test of independence",
            "alpha": alpha,
            "reason": "The problem describes association or independence between categorical variables.",
        })
    elif any(re.search(pattern, text) for pattern in INTENT_PATTERNS["correlation"]):
        candidates.append({
            "analysis": "Pearson correlation",
            "alpha": alpha,
            "reason": "The problem asks about a relationship or linear association between numerical variables.",
        })
    elif any(re.search(pattern, text) for pattern in INTENT_PATTERNS["group_comparison"]):
        group_count = re.search(
            r"\b(\d+)\s+(?:independent\s+)?(?:groups?|methods?|treatments?|approaches?|conditions?)\b",
            text,
        )
        three_or_more = bool(group_count and int(group_count.group(1)) >= 3)
        three_or_more = three_or_more or bool(
            re.search(
                r"\b(?:three|four|five|several|multiple)\b.*\b(?:groups?|methods?|treatments?|approaches?)\b",
                text,
            )
        )
        candidates.append({
            "analysis": "One-way ANOVA" if three_or_more else "Welch two-sample t-test",
            "alpha": alpha,
            "reason": (
                "The problem describes comparing a numerical outcome across three or more independent groups."
                if three_or_more
                else "The problem describes comparing a numerical outcome between two independent groups."
            ),
        })
    elif re.search(
        r"\bmean\b.*\b(?:standard|benchmark|reference|hypothesized|population)\b",
        text,
    ):
        candidates.append({
            "analysis": "One-sample t-test",
            "alpha": alpha,
            "reason": "The problem compares a sample mean with a stated reference or population value.",
        })

    return candidates


def _problem_type(intent):
    return {
        "group_comparison": "Comparison of independent groups",
        "categorical_association": "Association between categorical variables",
        "correlation": "Relationship between numerical variables",
        "association": "Association between variables",
        "prediction": "Prediction using numerical variables",
        "paired_comparison": "Paired or before/after comparison",
        "one_sample": "One-sample mean comparison",
    }.get(intent, "Statistical problem")



def _build_statistical_plan(question, intent, candidate):
    """Build an explainable statistical plan before numerical calculation."""
    analysis = candidate.get("analysis", "Statistical analysis")
    alpha = candidate.get("alpha", _extract_alpha(question))

    design_plan = experimental_design_plan(question)
    if design_plan:
        design_plan["alpha"] = alpha
        design_plan["decision_rule"] = (
            f"Compare the relevant p-value with α = {alpha:.3f}; "
            "reject H₀ for a statistically significant effect when p < α."
        )
        return design_plan

    plan = {
        "objective": "Determine the statistical relationship, difference, or effect described in the problem.",
        "design": _problem_type(intent),
        "response": "Numerical outcome",
        "factor": None,
        "hypotheses": [],
        "assumptions": [],
        "effect_size": None,
        "follow_up": [],
        "alpha": alpha,
        "data_needed": "Observations matching the variables and study design described in the problem.",
    }

    # Replace generic role descriptions with the variables actually
    # resolved from the user's natural-language question and dataset.
    # The language model/parser may describe the problem, but the dataset
    # mapping is authoritative.
    response_column = candidate.get("response")
    grouping_column = candidate.get("grouping")
    variable_1 = candidate.get("variable_1")
    variable_2 = candidate.get("variable_2")
    predictor_column = candidate.get("predictor")

    if response_column:
        plan["response"] = response_column
    if grouping_column:
        plan["factor"] = grouping_column
    if predictor_column:
        plan["predictor"] = predictor_column
    if variable_1:
        plan["variable_1"] = variable_1
    if variable_2:
        plan["variable_2"] = variable_2

    resolved = [
        value for value in (
            response_column,
            grouping_column,
            predictor_column,
            variable_1,
            variable_2,
        )
        if value
    ]
    if resolved:
        plan["resolved_variables"] = list(dict.fromkeys(resolved))
        plan["question_interpretation"] = (
            f"The question was interpreted using the dataset variables: "
            f"{', '.join(dict.fromkeys(resolved))}."
        )

    if analysis == "One-way ANOVA" and grouping_column and response_column:
        plan.update({
            "objective": (
                f"Determine whether mean {response_column} differs across "
                f"the groups defined by {grouping_column}."
            ),
            "design": f"One numerical response ({response_column}) measured across "
                       f"three or more independent groups defined by {grouping_column}",
            "response": response_column,
            "factor": grouping_column,
        })
    elif analysis == "Welch two-sample t-test" and grouping_column and response_column:
        plan.update({
            "objective": (
                f"Determine whether mean {response_column} differs between "
                f"the two groups defined by {grouping_column}."
            ),
            "design": f"Two independent groups from {grouping_column}, with "
                       f"{response_column} as the numerical response",
            "response": response_column,
            "factor": grouping_column,
        })
    elif analysis == "Pearson correlation" and variable_1 and variable_2:
        plan.update({
            "objective": (
                f"Determine whether {variable_1} and {variable_2} have a "
                "linear association in the observed data."
            ),
            "design": f"Two numerical variables: {variable_1} and {variable_2}",
            "response": variable_2,
            "predictor": variable_1,
        })
    elif analysis == "Pearson correlation + simple linear regression" and variable_1 and variable_2:
        plan.update({
            "objective": (
                f"Determine whether {variable_1} and {variable_2} are related "
                "and quantify the linear relationship."
            ),
            "design": f"Two numerical variables: {variable_1} and {variable_2}",
            "response": variable_2,
            "predictor": variable_1,
        })
    elif analysis == "Simple linear regression" and predictor_column and response_column:
        plan.update({
            "objective": (
                f"Estimate how {response_column} changes with {predictor_column} "
                "and use the fitted relationship for prediction."
            ),
            "design": f"{response_column} modeled from numerical predictor {predictor_column}",
            "response": response_column,
            "predictor": predictor_column,
        })
    elif analysis == "Chi-square test of independence" and variable_1 and variable_2:
        plan.update({
            "objective": (
                f"Determine whether {variable_1} and {variable_2} are "
                "statistically independent."
            ),
            "design": f"Two categorical variables: {variable_1} and {variable_2}",
            "factor": f"{variable_1} and {variable_2}",
        })
    elif analysis == "Paired t-test" and variable_1 and variable_2:
        plan.update({
            "objective": (
                f"Determine whether the mean paired change from {variable_1} "
                f"to {variable_2} differs from zero."
            ),
            "design": f"Paired measurements: {variable_1} and {variable_2}",
            "response": f"{variable_1} → {variable_2}",
        })

    if analysis == "One-way ANOVA":
        plan.update({
            "objective": "Determine whether the mean numerical outcome differs across the independent groups.",
            "design": "One numerical response measured across three or more independent groups",
            "response": "Numerical outcome",
            "factor": "Categorical grouping factor with three or more levels",
            "hypotheses": [
                "H₀: All population group means are equal.",
                "H₁: At least one population group mean differs.",
            ],
            "assumptions": [
                "Observations are independent.",
                "The response is approximately normal within groups, especially for small samples.",
                "Group variances are reasonably homogeneous for ordinary one-way ANOVA.",
            ],
            "effect_size": "Eta-squared (η²).",
            "follow_up": [
                "If the omnibus ANOVA is significant, perform a multiple-comparison procedure such as Tukey HSD.",
                "Report group means and the magnitude of observed differences.",
            ],
            "data_needed": "One numerical response value and one group label for each independent observation.",
        })
    elif analysis == "Welch two-sample t-test":
        plan.update({
            "objective": "Determine whether the mean numerical outcome differs between two independent groups.",
            "design": "Two independent groups with a numerical response",
            "factor": "Binary categorical grouping factor",
            "hypotheses": [
                "H₀: The two population means are equal.",
                "H₁: The two population means differ.",
            ],
            "assumptions": [
                "Observations are independent.",
                "The response is approximately normal within each group, particularly for small samples.",
                "Welch's test does not require equal population variances.",
            ],
            "effect_size": "Cohen's d or another standardized mean-difference measure.",
            "follow_up": [
                "Report both group means and the estimated mean difference.",
                "Interpret significance together with effect size and uncertainty.",
            ],
            "data_needed": "One numerical response value and a two-level group label for each independent observation.",
        })
    elif analysis == "Pearson correlation":
        plan.update({
            "objective": "Determine whether two numerical variables have a statistically significant linear association.",
            "design": "Observational relationship between two numerical variables",
            "response": "Two numerical variables",
            "hypotheses": [
                "H₀: The population Pearson correlation is zero.",
                "H₁: The population Pearson correlation is not zero.",
            ],
            "assumptions": [
                "Observations are independent.",
                "The relationship is approximately linear.",
                "Extreme outliers should be investigated.",
            ],
            "effect_size": "Pearson's r is the standardized measure of linear association.",
            "follow_up": [
                "Report the direction and magnitude of r with its p-value.",
                "Consider simple linear regression when prediction is relevant.",
            ],
            "data_needed": "Paired numerical observations for both variables.",
        })
    elif analysis == "Simple linear regression":
        plan.update({
            "objective": "Estimate or predict a numerical response from a numerical predictor.",
            "design": "Linear regression with one numerical predictor",
            "response": "Numerical response variable",
            "factor": "Numerical predictor",
            "hypotheses": [
                "H₀: The population slope is zero.",
                "H₁: The population slope is not zero.",
            ],
            "assumptions": [
                "Linearity between predictor and response.",
                "Independent observations.",
                "Approximately constant residual variance.",
                "Residual distribution should be checked for inference.",
            ],
            "effect_size": "R² describes the proportion of sample response variation explained by the fitted model.",
            "follow_up": [
                "Report slope, R², p-value, and confidence interval.",
                "For prediction, distinguish a mean-response confidence interval from an individual prediction interval.",
            ],
            "data_needed": "Paired numerical predictor and response observations.",
        })
    elif analysis == "Chi-square test of independence":
        plan.update({
            "objective": "Determine whether two categorical variables are statistically independent.",
            "design": "Cross-tabulation of two categorical variables",
            "response": "Two categorical variables",
            "hypotheses": [
                "H₀: The two categorical variables are independent.",
                "H₁: The two categorical variables are associated.",
            ],
            "assumptions": [
                "Observations are independent.",
                "Categories are mutually exclusive and consistently defined.",
                "Expected cell counts should be adequate for the chi-square approximation.",
            ],
            "effect_size": "Cramér's V measures association strength.",
            "follow_up": [
                "Inspect the contingency table and expected counts.",
                "If significant, inspect category patterns contributing to the association.",
            ],
            "data_needed": "Two categorical variables recorded for each independent observation.",
        })
    elif analysis == "Paired t-test":
        plan.update({
            "objective": "Determine whether the mean paired difference between two measurements differs from zero.",
            "design": "Paired or before/after measurements on the same units",
            "response": "Two measurements per subject or unit",
            "hypotheses": [
                "H₀: The mean paired difference is zero.",
                "H₁: The mean paired difference is not zero.",
            ],
            "assumptions": [
                "Pairs are correctly matched.",
                "Paired differences are approximately normal for small samples.",
                "Different pairs are independent.",
            ],
            "effect_size": "A standardized mean difference for paired observations.",
            "follow_up": [
                "Report the mean paired change and its confidence interval.",
                "Consider a non-parametric paired alternative if assumptions are poor.",
            ],
            "data_needed": "Two matched measurements from each subject, unit, or condition.",
        })

    plan["decision_rule"] = (
        f"Compare the relevant p-value with α = {alpha:.3f}; reject H₀ when p < α."
    )

    # A useful statistical plan should explain not only the test name, but
    # what is being estimated, why this model fits, what can invalidate it,
    # and what should be reported after the test.
    plan["analysis_justification"] = (
        f"{analysis} is selected because the stated research problem "
        "matches the comparison, association, prediction, or experimental "
        "structure described in the question."
    )
    plan["estimand"] = (
        "The primary quantity being tested or estimated under the stated model."
    )
    plan["evidence_to_report"] = [
        "Sample size and descriptive summaries for the relevant variables.",
        "Test statistic, degrees of freedom when applicable, and p-value.",
        "Effect size and a confidence interval when the required calculation is available.",
    ]
    plan["data_validation"] = [
        "Confirm the required variables are present and have appropriate measurement types.",
        "Remove or document missing observations used by the analysis.",
        "Check that observations match the independence or pairing structure stated in the problem.",
    ]
    plan["interpretation_guardrails"] = [
        "Statistical significance does not by itself establish practical importance.",
        "Association or group differences should not automatically be interpreted as causation unless the study design supports a causal conclusion.",
        "Report uncertainty and effect magnitude alongside the p-value.",
    ]

    if analysis == "Welch two-sample t-test":
        plan.update({
            "estimand": "Difference between the two population means (μ₁ − μ₂).",
            "analysis_justification": (
                "Welch's t-test is appropriate for two independent groups with a "
                "numerical response because it tests a mean difference without "
                "assuming equal population variances."
            ),
            "evidence_to_report": [
                "n, mean, and standard deviation for each group.",
                "Mean difference with a confidence interval.",
                "Welch t-statistic, Welch-Satterthwaite degrees of freedom, and p-value.",
                "A standardized effect size such as Cohen's d, with its interpretation kept separate from significance.",
            ],
            "data_validation": [
                "Verify exactly two independent groups are present.",
                "Check sample sizes and missing values within each group.",
                "Inspect extreme observations and group distributions.",
                "Use Welch's unequal-variance formulation rather than silently assuming equal variances.",
            ],
            "follow_up": [
                "Report the estimated mean difference and its confidence interval.",
                "Report an effect size to describe magnitude.",
                "If the normal approximation is questionable, consider a robust or non-parametric sensitivity analysis.",
            ],
        })
    elif analysis == "One-way ANOVA":
        plan.update({
            "estimand": "The set of population mean differences across the independent groups.",
            "analysis_justification": (
                "One-way ANOVA tests a common mean-equality hypothesis across "
                "three or more independent groups while controlling the overall "
                "omnibus Type-I error for the primary comparison."
            ),
            "evidence_to_report": [
                "Sample size and mean/standard deviation for every group.",
                "ANOVA F-statistic, numerator and denominator degrees of freedom, and p-value.",
                "Eta-squared or another appropriate effect size.",
                "Adjusted pairwise comparisons when the omnibus test is significant.",
            ],
        })
    elif analysis == "Paired t-test":
        plan.update({
            "estimand": "Mean paired change, μ_d, between the two matched measurements.",
            "analysis_justification": (
                "The paired t-test analyzes within-pair differences, removing "
                "between-subject variation when the same units are measured twice."
            ),
            "evidence_to_report": [
                "Number of complete pairs and mean paired difference.",
                "Confidence interval for the mean difference.",
                "t-statistic, degrees of freedom, and p-value.",
                "A paired standardized effect size where available.",
            ],
        })
    elif analysis == "Pearson correlation":
        plan.update({
            "estimand": "Population Pearson correlation coefficient ρ.",
            "analysis_justification": (
                "Pearson correlation quantifies the direction and strength of a "
                "linear association between two numerical variables."
            ),
            "evidence_to_report": [
                "Sample size and Pearson r.",
                "Confidence interval for r when available.",
                "Test statistic and p-value for H₀: ρ = 0.",
                "A scatterplot and outlier/linearity assessment.",
            ],
        })
    elif analysis == "Simple linear regression":
        plan.update({
            "estimand": "Population regression slope β₁ and the fitted conditional mean response.",
            "analysis_justification": (
                "Simple linear regression models a numerical response as a "
                "function of one numerical predictor and separates the estimated "
                "slope from unexplained residual variation."
            ),
            "evidence_to_report": [
                "Regression equation, slope and intercept.",
                "R² and slope p-value.",
                "Confidence interval for the slope.",
                "Residual diagnostics and, for prediction, a prediction interval for an individual future observation.",
            ],
        })
    elif analysis == "Chi-square test of independence":
        plan.update({
            "estimand": "Departure of the observed contingency-table frequencies from independence.",
            "analysis_justification": (
                "The chi-square independence test compares observed cell counts "
                "with the counts expected if the two categorical variables were independent."
            ),
            "evidence_to_report": [
                "Observed and expected contingency tables.",
                "Chi-square statistic, degrees of freedom, and p-value.",
                "Cramér's V as an association effect size.",
                "Cell-level patterns or adjusted residuals when interpretation of a significant result is needed.",
            ],
        })

    return plan


def interpret_question(df=None, question=""):
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

    embedded_df = extract_tabular_text(question) if df is None else None
    if df is None and embedded_df is not None:
        df = embedded_df

    if df is None:
        intents = _detect_intents(question)
        intent = intents[0][0] if intents else None
        candidates = _text_only_plan(question)
        plan = _build_statistical_plan(question, intent, candidates[0]) if candidates else {
            "objective": "More information is required to select a defensible analysis.",
            "design": "Undetermined",
            "response": None,
            "factor": None,
            "hypotheses": [],
            "assumptions": [],
            "effect_size": None,
            "follow_up": [],
            "alpha": _extract_alpha(question),
            "data_needed": "Describe the outcome, groups, relationship, or prediction target.",
            "decision_rule": f"Use α = {_extract_alpha(question):.3f} when a test is selected.",
        }

        return {
            "status": "ready" if candidates else "needs_clarification",
            "intent": intent,
            "problem_type": _problem_type(intent),
            "confidence": round(
                min(0.96, 0.45 + 0.12 * (intents[0][1] if intents else 0))
                if candidates else 0.20,
                2,
            ),
            "alpha": _extract_alpha(question),
            "matched_columns": [],
            "candidates": candidates,
            "reason": (
                candidates[0]["reason"]
                if candidates
                else "Describe the outcome, comparison, relationship, prediction, or study design in the problem."
            ),
            "analysis_requests": _explicit_analysis_request(question),
            "embedded_data": None,
            "plan": plan,
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

    # Experimental-design language is authoritative. Once a concrete design
    # such as RBD is detected, do not also generate generic group-comparison
    # candidates. The design determines the correct model and error structure.
    detected_design = detect_experimental_design(question)
    if detected_design.get("design"):
        candidates = [{
            "analysis": detected_design["analysis"],
            "design": detected_design["design"],
            "alpha": alpha,
            "reason": detected_design["description"],
            "confidence": detected_design["confidence"],
        }]

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
        "embedded_data": (
            df.to_dict(orient="records") if embedded_df is not None else None
        ),
        "plan": (
            _build_statistical_plan(question, intent, candidates[0])
            if candidates else {
                "objective": reason,
                "design": _problem_type(intent),
                "response": None,
                "factor": None,
                "hypotheses": [],
                "assumptions": [],
                "effect_size": None,
                "follow_up": [],
                "alpha": alpha,
                "data_needed": "Additional information is required.",
                "decision_rule": f"Use α = {alpha:.3f} when a test is selected.",
            }
        ),
    }
