"""Experimental-design recognition and analysis for StatsYuri.

The design layer is deliberately separate from generic hypothesis tests. It maps
agricultural and experimental-study language to an explicit design/model before
numerical inference is attempted.
"""

import re
import pandas as pd
from scipy import stats


DESIGN_RULES = [
    # Most specific structures first. Detection is based on experimental
    # structure, not merely the presence of words such as "randomized".
    {
        "design": "Split-Split Plot Design",
        "patterns": [
            r"split[- ]split[- ]plot",
            r"split[- ]split plot",
            r"whole[- ]plot.*subplot.*sub[- ]subplot",
            r"three.*(?:plot|error).*strata",
        ],
        "required": 1,
        "analysis": "Split-split-plot ANOVA",
        "description": "Three nested randomization levels: whole-plot, subplot, and sub-subplot factors.",
    },
    {
        "design": "Split-Plot Design",
        "patterns": [
            r"split[- ]plot",
            r"main[- ]plot.*subplot",
            r"whole[- ]plot.*subplot",
            r"(?:large|main|whole)[- ]plots?.*(?:smaller|subplot)",
            r"one factor.*(?:large|whole|main)[- ]plots?.*another.*(?:subplot|within)",
        ],
        "required": 1,
        "analysis": "Split-plot ANOVA",
        "description": "One factor is randomized to whole plots and another factor is randomized within those whole plots.",
    },
    {
        "design": "Latin Square Design",
        "patterns": [
            r"latin square",
            r"each treatment.*once.*row.*column",
            r"each treatment.*once.*row and column",
            r"every treatment.*once.*row.*column",
            r"row.*column.*each treatment.*once",
        ],
        "required": 1,
        "analysis": "Latin-square ANOVA",
        "description": "Treatments are arranged so that each treatment occurs once in every row and every column, controlling two blocking directions.",
    },
    {
        "design": "Strip-Plot Design",
        "patterns": [
            r"strip[- ]plot",
            r"crossed strips",
            r"two factors.*(?:strips|strip treatments)",
            r"one factor.*strip.*another factor.*strip",
        ],
        "required": 1,
        "analysis": "Strip-plot ANOVA",
        "description": "Two factors are randomized to crossing strips within blocks, producing separate strip error terms.",
    },
    {
        "design": "Factorial Randomized Block Design",
        "patterns": [
            r"factorial.*randomi[sz]ed.*block",
            r"factorial.*randomi[sz]ed complete block",
            r"factorial.*(?:rcbd|rbd).*block",
            r"(?:two|three|multiple|several).*factors?.*within.*blocks?",
            r"factorial.*blocks?.*(?:factor|treatment)",
        ],
        "required": 1,
        "analysis": "Factorial RBD ANOVA",
        "description": "Two or more treatment factors are studied factorially, with treatment combinations randomized within blocks.",
    },
    {
        "design": "Factorial Completely Randomized Design",
        "patterns": [
            r"factorial.*completely randomi[sz]ed",
            r"factorial.*crd",
            r"(?:two|three|multiple|several).*factors?.*randomly assigned.*(?:independent|homogeneous)",
            r"every combination.*(?:randomly assigned|randomized)",
            r"all combinations.*(?:randomly assigned|randomized)",
        ],
        "required": 1,
        "analysis": "Factorial CRD ANOVA",
        "description": "Two or more crossed treatment factors are studied under complete randomization without a blocking factor.",
    },
    {
        "design": "Randomized Block Design",
        "patterns": [
            r"randomi[sz]ed complete block",
            r"randomi[sz]ed block design",
            r"rbd",
            r"rcbd",
            r"each treatment.*every block",
            r"each treatment.*once.*block",
            r"treatments?.*randomi[sz]ed.*within.*blocks?",
            r"randomly assigned.*within.*blocks?",
            r"blocks?.*control.*(?:variation|variability)",
        ],
        "required": 1,
        "analysis": "Randomized-block ANOVA",
        "description": "A single treatment factor is randomized within blocks to control block-to-block variation.",
    },
    {
        "design": "Completely Randomized Design",
        "patterns": [
            r"completely randomi[sz]ed",
            r"crd",
            r"experimental units?.*(?:homogeneous|similar).*randomly assigned.*(?:treatments?|treatment levels?)",
            r"treatments?.*randomly assigned.*(?:independent|homogeneous).*experimental units?",
            r"randomly assigned.*treatments?.*(?:no blocks?|without blocks?|no blocking|without blocking)",
        ],
        "required": 1,
        "analysis": "One-way ANOVA for CRD",
        "description": "A single treatment factor is randomly assigned to otherwise comparable experimental units without blocking.",
    },
]

def _norm(text):
    return re.sub(r"\s+", " ", str(text).lower().replace("_", " ")).strip()


def _design_structure_evidence(text):
    """Extract structural cues that distinguish DOE designs."""
    return {
        "has_treatment": bool(re.search(r"\b(?:treatment|treatments|fertilizer|fertilizers|variety|varieties|cultivar|cultivars|method|methods|dose|doses|irrigation|intervention|interventions)\b", text)),
        "has_block": bool(re.search(r"\b(?:block|blocking|replication|replicate|rep)\b", text)),
        "has_row": bool(re.search(r"\brows?\b", text)),
        "has_column": bool(re.search(r"\bcolumns?\b", text)),
        "has_whole_plot": bool(re.search(r"whole[- ]plot|main[- ]plot|large[- ]plot", text)),
        "has_subplot": bool(re.search(r"sub[- ]plot|subplot|small[- ]plot", text)),
        "has_subsubplot": bool(re.search(r"sub[- ]sub[- ]plot|subsubplot", text)),
        "has_strips": bool(re.search(r"strip[- ]plot|crossed strips", text)),
        "has_factorial": bool(re.search(r"\bfactorial\b|\b(?:two|three|multiple|several)\s+factors?\b", text)),
        "explicit_no_block": bool(re.search(r"(?:no|without|independent of|not using)\s+(?:blocks?|blocking|replication)", text)),
        "complete_randomization": bool(re.search(
            r"completely randomi[sz]ed|complete randomization|\bcrd\b|"
            r"randomly (?:assigned|allocated|allotted|distributed) (?:to|among|across) "
            r"(?:the\s+)?(?:[a-z0-9]+\s+){0,4}"
            r"(?:treatments?|treatment levels?|groups?|methods?|conditions?|irrigation methods?|fertilizers?|varieties?)|"
            r"(?:treatments?|treatment levels?|methods?|conditions?|groups?) "
            r"(?:were|are|was) randomly (?:assigned|allocated|allotted|distributed)",
            text,
        )),
    }


def detect_experimental_design(problem):
    """Detect DOE from randomization and error structure, not loose keywords."""
    text = _norm(problem)
    evidence = _design_structure_evidence(text)
    matches = []

    if evidence["has_subsubplot"] and evidence["has_subplot"]:
        matches.append(("Split-Split Plot Design", "Split-split-plot ANOVA",
                        "Three nested randomization levels: whole-plot, subplot, and sub-subplot factors.", 0.97))
    elif evidence["has_whole_plot"] and evidence["has_subplot"]:
        matches.append(("Split-Plot Design", "Split-plot ANOVA",
                        "One factor is randomized to whole plots and another factor within whole plots.", 0.96))
    elif evidence["has_strips"]:
        matches.append(("Strip-Plot Design", "Strip-plot ANOVA",
                        "Two factors are randomized to crossing strips within blocks.", 0.96))
    elif evidence["has_row"] and evidence["has_column"] and re.search(
        r"(?:each|every)\s+treatment.*(?:once|one)\s+(?:in|per)\s+(?:each|every)\s+row.*(?:and|,)\s*(?:each|every)\s+column",
        text,
    ):
        matches.append(("Latin Square Design", "Latin-square ANOVA",
                        "Each treatment occurs once in every row and every column, controlling two blocking directions.", 0.99))
    elif evidence["has_factorial"] and evidence["has_block"] and evidence["has_treatment"]:
        matches.append(("Factorial Randomized Block Design", "Factorial RBD ANOVA",
                        "Two or more treatment factors are studied factorially within blocks.", 0.95))
    elif evidence["has_factorial"] and evidence["has_treatment"] and (evidence["complete_randomization"] or evidence["explicit_no_block"]) and not evidence["has_block"]:
        matches.append(("Factorial Completely Randomized Design", "Factorial CRD ANOVA",
                        "Two or more crossed treatment factors are studied under complete randomization without blocking.", 0.95))
    elif evidence["has_block"] and evidence["has_treatment"]:
        matches.append(("Randomized Block Design", "Randomized-block ANOVA",
                        "A treatment factor is randomized within blocks to control block-to-block variation.", 0.95))
    elif (
        evidence["has_treatment"]
        and evidence["complete_randomization"]
        and not evidence["has_block"]
    ):
        matches.append(("Completely Randomized Design", "One-way ANOVA for CRD",
                        "A single treatment factor is randomly assigned to comparable experimental units without blocking.", 0.97))
    elif (
        evidence["has_treatment"]
        and evidence["explicit_no_block"]
        and not evidence["has_block"]
    ):
        matches.append(("Completely Randomized Design", "One-way ANOVA for CRD",
                        "A single treatment factor is assigned to comparable experimental units without a blocking factor.", 0.96))

    if not matches:
        for rule in DESIGN_RULES:
            hits = [pattern for pattern in rule["patterns"] if re.search(pattern, text)]
            if len(hits) >= rule.get("required", 1):
                matches.append((rule["design"], rule["analysis"], rule["description"],
                                min(0.90, 0.70 + 0.06 * len(hits))))
                break

    if not matches:
        return {"design": None, "analysis": None, "description": None,
                "matched_cues": [], "confidence": 0.0, "structure": evidence}

    design, analysis, description, confidence = matches[0]
    return {
        "design": design,
        "analysis": analysis,
        "description": description,
        "matched_cues": [key for key, value in evidence.items() if value],
        "confidence": confidence,
        "structure": evidence,
    }


def extract_experimental_entities(problem):
    """Extract explicit response, treatment, block, levels, and replication cues."""
    text = str(problem).strip()
    lower = _norm(text)

    def first_match(patterns):
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip(" .,:;")
        return None

    response = first_match([
        r"(?:effect|effects|impact|influence).*?on\s+(?:the\s+)?([A-Za-z][A-Za-z ]+?)(?:\.|,|\s+at\s+the\s+|$)",
        r"(?:determine|measure|record|observe|compare).*?(?:on|for|of)\s+(?:the\s+)?([A-Za-z][A-Za-z ]+?)(?:\.|,|\s+at\s+the\s+|$)",
        r"(?:response|outcome|dependent variable)\s+(?:was|is|of)\s+([A-Za-z][A-Za-z ]+?)(?:\.|,|$)",
    ])

    treatment = first_match([
        r"(?:effects?|effectiveness)\s+of\s+(?:different\s+|various\s+|the\s+)?([A-Za-z][A-Za-z ]+?)\s+on",
        r"(?:compare|comparing)\s+(?:the\s+)?(?:effects?\s+of\s+)?(?:different\s+|various\s+)?([A-Za-z][A-Za-z ]+?)\s+(?:on|for)",
        r"(?:treatments?|treatment factor)\s*(?:were|was|are|is)?\s*([A-Za-z][A-Za-z ]+?)(?:\.|,|\s+were|\s+was|\s+at\s+the\s+|$)",
    ])

    block = first_match([
        r"(?:using|with|across)\s+(?:\d+\s+)?(?:blocks?|replications?)",
        r"(?:in|using|with)\s+(?:a\s+)?randomi[sz]ed(?:\s+complete)?\s+block\s+design\s+with\s+(\d+)\s+blocks?",
    ])

    block_count = None
    block_match = re.search(r"(\d+)\s+(?:blocks?|replications?|replicates?)", lower)
    if block_match:
        block_count = int(block_match.group(1))

    treatment_count = None
    treatment_match = re.search(
        r"(\d+)\s+(?:different\s+)?(?:treatments?|fertilizers?|varieties?|methods?|doses?|irrigation\s+levels?|treatment\s+levels?)",
        lower,
    )
    if treatment_match:
        treatment_count = int(treatment_match.group(1))

    # Only report named treatment levels when the sentence explicitly
    # enumerates them. Generic structural phrases such as "five blocks, each..."
    # must never become treatment names.
    levels = []
    explicit_level_patterns = [
        r"(?:treatments?|methods?|fertilizers?|varieties?)\s+"
        r"(?:were|are|included|used)\s*[:\-]?\s*(.+?)(?:\.|$)",
        r"(?:using|with|having)\s+(?:the\s+)?"
        r"(?:treatments?|methods?|fertilizers?|varieties?)\s*[:\-]\s*(.+?)(?:\.|$)",
    ]
    for pattern in explicit_level_patterns:
        level_match = re.search(pattern, text, flags=re.IGNORECASE)
        if not level_match:
            continue
        candidate = level_match.group(1).strip(" .,:;")
        if (
            len(candidate) < 120
            and not re.match(
                r"^(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
                r"(?:blocks?|replications?|replicates?)\b",
                candidate,
                flags=re.IGNORECASE,
            )
        ):
            parsed_levels = [
                item.strip(" .,:;")
                for item in re.split(r",|\band\b", candidate, flags=re.IGNORECASE)
                if item.strip(" .,:;")
            ]
            if 2 <= len(parsed_levels) <= 12:
                levels = parsed_levels
                break

    # More reliable response/factor vocabulary when the narrative uses
    # standard experimental-science wording.
    factor_aliases = {
        "fertilizer": ["fertilizer", "fertilizers"],
        "variety": ["variety", "varieties", "cultivar", "cultivars"],
        "teaching method": ["teaching method", "teaching methods"],
        "irrigation": ["irrigation", "irrigation level", "irrigation levels"],
        "nitrogen": ["nitrogen", "nitrogen dose", "nitrogen doses"],
        "dose": ["dose", "doses"],
        "treatment": ["treatment", "treatments"],
    }
    factor_name = None
    for canonical, aliases in factor_aliases.items():
        if any(re.search(r"\b" + re.escape(alias) + r"\b", lower) for alias in aliases):
            factor_name = canonical.title()
            break

    if factor_name:
        treatment = factor_name

    response_aliases = {
        "crop yield": ["crop yield", "yield"],
        "plant height": ["plant height"],
        "grain yield": ["grain yield"],
        "exam score": ["exam score", "examination performance", "examination score"],
        "weight": ["weight"],
        "growth": ["growth"],
    }
    for canonical, aliases in response_aliases.items():
        if any(re.search(r"\b" + re.escape(alias) + r"\b", lower) for alias in aliases):
            response = canonical.title()
            break

    return {
        "response": response,
        "treatment": treatment,
        "block": "Block" if re.search(r"\bblocks?\b", lower) else None,
        "treatment_count": treatment_count,
        "block_count": block_count,
        "treatment_levels": levels,
    }

def experimental_design_plan(problem):
    """Return an explainable design-level plan from narrative text."""
    detected = detect_experimental_design(problem)
    if not detected["design"]:
        return None

    design = detected["design"]
    entities = extract_experimental_entities(problem)

    common = {
        "design": design,
        "analysis": detected["analysis"],
        "confidence": detected["confidence"],
        "reason": detected["description"],
        "matched_cues": detected["matched_cues"],
        "response": entities["response"] or "Numerical experimental response",
        "treatment_factor": entities["treatment"] or "Treatment or treatment factor",
        "blocking_factor": entities["block"],
        "treatment_count": entities["treatment_count"],
        "block_count": entities["block_count"],
        "treatment_levels": entities["treatment_levels"],
        "error_structure": "Determined from the experimental design.",
        "hypotheses": [
            "H₀: The relevant treatment effect(s) are equal/absent.",
            "H₁: At least one relevant treatment effect differs/is present.",
        ],
        "assumptions": [
            "Experimental units are independent at the appropriate randomization level.",
            "Residuals are approximately normal for classical ANOVA inference.",
            "Residual variance is reasonably homogeneous within the relevant error stratum.",
            "The randomization and blocking structure described in the problem is correctly represented.",
        ],
        "follow_up": [
            "Report the treatment means and the confirmed primary test result.",
            "Do not run an additional statistical test automatically.",
        ],
    }

    if entities["response"] and entities["treatment"]:
        count_text = (
            f" across {entities['treatment_count']} treatment levels"
            if entities["treatment_count"] else ""
        )
        common["objective"] = (
            f"Determine whether mean {entities['response'].lower()} differs "
            f"among the {entities['treatment'].lower()} treatment groups{count_text}, "
            "while accounting for the stated experimental structure."
        )
    else:
        common["objective"] = detected["description"]

    if entities["treatment_count"]:
        common["design_details"] = (
            f"{entities['treatment_count']} treatment levels"
            + (
                f" × {entities['block_count']} blocks"
                if entities["block_count"] else ""
            )
        )
    elif entities["block_count"]:
        common["design_details"] = f"{entities['block_count']} blocks"

    if entities["treatment_levels"]:
        common["treatment_levels"] = entities["treatment_levels"]

    # Translate each detected design into explicit experimental-language
    # statements. This keeps the plan understandable without requiring the
    # user to know the design name in advance.
    language = {
        "Completely Randomized Design": {
            "study_design": "Completely Randomized Design (CRD)",
            "treatment_factor_label": "Treatment factor",
            "randomization_structure": "Experimental units are treated as comparable and treatment levels are assigned completely at random.",
            "model_basis": "Treatment differences are compared against common residual error.",
        },
        "Randomized Block Design": {
            "study_design": "Randomized Block Design (RBD)",
            "treatment_factor_label": "Treatment factor",
            "randomization_structure": "Treatment levels are randomized within each block, separating block-to-block variation from treatment variation.",
            "model_basis": "Treatment effects are tested after accounting for systematic block variation.",
        },
        "Latin Square Design": {
            "study_design": "Latin Square Design (LSD)",
            "treatment_factor_label": "Treatment factor",
            "randomization_structure": "Each treatment occurs once in every row and once in every column, controlling two blocking directions.",
            "model_basis": "Treatment effects are estimated after accounting for both row and column effects.",
        },
        "Factorial Completely Randomized Design": {
            "study_design": "Factorial Completely Randomized Design",
            "treatment_factor_label": "Treatment factors",
            "randomization_structure": "All combinations of the treatment factors are randomly assigned to comparable experimental units without blocking.",
            "model_basis": "The model estimates main effects and interactions between treatment factors.",
        },
        "Factorial Randomized Block Design": {
            "study_design": "Factorial Randomized Block Design",
            "treatment_factor_label": "Treatment factors",
            "randomization_structure": "All treatment-factor combinations are randomized within blocks.",
            "model_basis": "Block variation is accounted for while estimating factorial main effects and interactions.",
        },
        "Split-Plot Design": {
            "study_design": "Split-Plot Design",
            "treatment_factor_label": "Whole-plot factor and subplot factor",
            "randomization_structure": "One factor is randomized to whole plots and the second factor is randomized within those whole plots.",
            "model_basis": "The factors use different error strata because they were randomized at different experimental levels.",
        },
        "Split-Split Plot Design": {
            "study_design": "Split-Split-Plot Design",
            "treatment_factor_label": "Whole-plot, subplot, and sub-subplot factors",
            "randomization_structure": "Three treatment factors are randomized at three nested experimental levels.",
            "model_basis": "Each factor and interaction is evaluated against the error stratum created by its randomization level.",
        },
        "Strip-Plot Design": {
            "study_design": "Strip-Plot Design",
            "treatment_factor_label": "Crossed strip treatment factors",
            "randomization_structure": "Two treatment factors are assigned to crossing strips within blocks.",
            "model_basis": "Each strip factor has its own strip-level error and their interaction is assessed separately.",
        },
    }.get(design)
    if language:
        common.update(language)

    if design == "Randomized Block Design":
        common.update({
            "blocking_factor": entities["block"] or "Block",
            "error_structure": "Treatment is tested against residual variation after accounting for blocks.",
            "hypotheses": [
                "H₀: All treatment means are equal after accounting for block effects.",
                "H₁: At least one treatment mean differs after accounting for blocks.",
            ],
        })
    elif design == "Latin Square Design":
        common.update({
            "blocking_factor": "Row and column",
            "error_structure": "Treatment is adjusted for both row and column blocking effects.",
            "hypotheses": [
                "H₀: All treatment means are equal after accounting for row and column effects.",
                "H₁: At least one treatment mean differs after accounting for row and column effects.",
            ],
        })
    elif design == "Factorial Completely Randomized Design":
        common.update({
            "treatment_factor": "Two or more crossed treatment factors",
            "error_structure": "Main effects and interactions are tested against residual error.",
            "hypotheses": [
                "H₀: Each main effect and interaction is absent.",
                "H₁: At least one main effect or interaction is present.",
            ],
            "follow_up": [
                "Interpret significant interactions before interpreting main effects in isolation.",
                "Use adjusted pairwise comparisons or simple-effects analysis when appropriate.",
            ],
        })
    elif design == "Factorial Randomized Block Design":
        common.update({
            "treatment_factor": "Two or more crossed treatment factors",
            "blocking_factor": "Block",
            "error_structure": "Block variation is removed before testing factorial treatment effects.",
            "hypotheses": [
                "H₀: Each factorial main effect and interaction is absent after accounting for blocks.",
                "H₁: At least one factorial treatment effect is present.",
            ],
        })
    elif design == "Split-Plot Design":
        common.update({
            "treatment_factor": "Whole-plot factor A and subplot factor B",
            "blocking_factor": "Block / whole-plot unit",
            "error_structure": "Whole-plot factor A uses the whole-plot error; B and A×B use subplot error.",
            "hypotheses": [
                "H₀: Whole-plot factor A has no effect.",
                "H₀: Subplot factor B has no effect and A×B has no interaction.",
            ],
        })
    elif design == "Split-Split Plot Design":
        common.update({
            "treatment_factor": "Whole-plot A, subplot B, and sub-subplot C",
            "blocking_factor": "Block / whole-plot unit",
            "error_structure": "A, B, and C effects are tested against their appropriate nested error strata.",
            "hypotheses": [
                "H₀: Relevant A, B, C main effects and interactions are absent.",
                "H₁: At least one relevant treatment effect or interaction is present.",
            ],
        })
    elif design == "Strip-Plot Design":
        common.update({
            "treatment_factor": "Crossed strip factors A and B",
            "blocking_factor": "Block",
            "error_structure": "A and B use their respective strip errors; A×B is tested against residual error.",
        })

    return common


def _anova_table(model, typ=2):
    from statsmodels.stats.anova import anova_lm

    table = anova_lm(model, typ=typ).reset_index()
    table = table.rename(
        columns={
            "index": "Source",
            "sum_sq": "Sum of Squares",
            "df": "Degrees of Freedom",
            "F": "F-Statistic",
            "PR(>F)": "P-Value",
        }
    )
    return table


def _fit_formula(df, formula, typ=2):
    from statsmodels.formula.api import ols

    model = ols(formula, data=df).fit()
    return {
        "Model": formula,
        "ANOVA Table": _anova_table(model, typ=typ),
        "Observations": len(df),
        "Residuals": model.resid,
        "Fitted Values": model.fittedvalues,
    }


def _q(column):
    return f'Q("{column}")'


def crd_anova(df, response, treatment):
    """Analyze a completely randomized design."""
    data = df[[response, treatment]].dropna().copy()
    if data[treatment].nunique() < 2:
        return None
    data[response] = pd.to_numeric(data[response], errors="coerce")
    data = data.dropna()
    if data[treatment].nunique() < 2:
        return None
    return _fit_formula(data, f"{_q(response)} ~ C({_q(treatment)})")


def rbd_anova(df, response, treatment, block):
    """Analyze a randomized complete block design."""
    data = df[[response, treatment, block]].dropna().copy()
    if data[treatment].nunique() < 2 or data[block].nunique() < 2:
        return None
    data[response] = pd.to_numeric(data[response], errors="coerce")
    data = data.dropna()
    if data.empty:
        return None
    return _fit_formula(
        data,
        f"{_q(response)} ~ C({_q(block)}) + C({_q(treatment)})",
    )


def latin_square_anova(df, response, treatment, row, column):
    """Analyze a Latin square with treatment, row, and column effects."""
    data = df[[response, treatment, row, column]].dropna().copy()
    if min(data[treatment].nunique(), data[row].nunique(), data[column].nunique()) < 2:
        return None
    data[response] = pd.to_numeric(data[response], errors="coerce")
    data = data.dropna()
    return _fit_formula(
        data,
        f"{_q(response)} ~ C({_q(row)}) + C({_q(column)}) + C({_q(treatment)})",
    )


def factorial_crd_anova(df, response, factor_a, factor_b):
    """Analyze a two-factor factorial CRD."""
    data = df[[response, factor_a, factor_b]].dropna().copy()
    data[response] = pd.to_numeric(data[response], errors="coerce")
    data = data.dropna()
    if min(data[factor_a].nunique(), data[factor_b].nunique()) < 2:
        return None
    return _fit_formula(
        data,
        f"{_q(response)} ~ C({_q(factor_a)}) * C({_q(factor_b)})",
    )


def factorial_rbd_anova(df, response, factor_a, factor_b, block):
    """Analyze a two-factor factorial RBD."""
    data = df[[response, factor_a, factor_b, block]].dropna().copy()
    data[response] = pd.to_numeric(data[response], errors="coerce")
    data = data.dropna()
    if min(data[factor_a].nunique(), data[factor_b].nunique(), data[block].nunique()) < 2:
        return None
    return _fit_formula(
        data,
        f"{_q(response)} ~ C({_q(block)}) + C({_q(factor_a)}) * C({_q(factor_b)})",
    )


def split_plot_anova(df, response, factor_a, factor_b, block):
    """Analyze a balanced split-plot using explicit whole-plot error."""
    data = df[[response, factor_a, factor_b, block]].dropna().copy()
    data[response] = pd.to_numeric(data[response], errors="coerce")
    data = data.dropna()
    if min(
        data[factor_a].nunique(),
        data[factor_b].nunique(),
        data[block].nunique(),
    ) < 2:
        return None

    formula = (
        f"{_q(response)} ~ C({_q(block)}) + C({_q(factor_a)}) "
        f"+ C({_q(block)}):C({_q(factor_a)}) + "
        f"C({_q(factor_b)}) + C({_q(factor_a)}):C({_q(factor_b)})"
    )
    result = _fit_formula(data, formula)
    result["Error Structure"] = {
        "Whole-plot factor": f"C({_q(block)}):C({_q(factor_a)})",
        "Subplot factors": "Residual",
    }
    return result


def split_split_plot_anova(df, response, factor_a, factor_b, factor_c, block):
    """Analyze a balanced split-split-plot using nested error strata."""
    data = df[[response, factor_a, factor_b, factor_c, block]].dropna().copy()
    data[response] = pd.to_numeric(data[response], errors="coerce")
    data = data.dropna()
    if min(
        data[factor_a].nunique(),
        data[factor_b].nunique(),
        data[factor_c].nunique(),
        data[block].nunique(),
    ) < 2:
        return None

    formula = (
        f"{_q(response)} ~ C({_q(block)}) + C({_q(factor_a)}) + "
        f"C({_q(block)}):C({_q(factor_a)}) + C({_q(factor_b)}) + "
        f"C({_q(factor_a)}):C({_q(factor_b)}) + "
        f"C({_q(block)}):C({_q(factor_a)}):C({_q(factor_b)}) + "
        f"C({_q(factor_c)}) + C({_q(factor_a)}):C({_q(factor_c)}) + "
        f"C({_q(factor_b)}):C({_q(factor_c)}) + "
        f"C({_q(factor_a)}):C({_q(factor_b)}):C({_q(factor_c)})"
    )
    result = _fit_formula(data, formula)
    result["Error Structure"] = {
        "A": f"C({_q(block)}):C({_q(factor_a)})",
        "B": f"C({_q(block)}):C({_q(factor_a)}):C({_q(factor_b)})",
        "C and interactions with C": "Residual",
    }
    return result


def strip_plot_anova(df, response, factor_a, factor_b, block):
    """Analyze a strip-plot with separate strip errors."""
    data = df[[response, factor_a, factor_b, block]].dropna().copy()
    data[response] = pd.to_numeric(data[response], errors="coerce")
    data = data.dropna()
    if min(
        data[factor_a].nunique(),
        data[factor_b].nunique(),
        data[block].nunique(),
    ) < 2:
        return None

    formula = (
        f"{_q(response)} ~ C({_q(block)}) + C({_q(factor_a)}) + "
        f"C({_q(block)}):C({_q(factor_a)}) + C({_q(factor_b)}) + "
        f"C({_q(block)}):C({_q(factor_b)}) + "
        f"C({_q(factor_a)}):C({_q(factor_b)})"
    )
    result = _fit_formula(data, formula)
    result["Error Structure"] = {
        "Factor A": f"C({_q(block)}):C({_q(factor_a)})",
        "Factor B": f"C({_q(block)}):C({_q(factor_b)})",
        "A × B": "Residual",
    }
    return result


def infer_design_columns(df, problem, design):
    """Infer response/treatment/block roles from names and narrative semantics."""
    text = _norm(problem)
    numeric = [
        col for col in df.select_dtypes(include="number").columns
        if str(col).strip().lower() not in {"id", "index", "serial"}
    ]
    categorical = [
        col for col in df.columns
        if col not in numeric and df[col].nunique(dropna=True) >= 2
    ]

    def score(column, aliases):
        name = _norm(column)
        return sum(1 for alias in aliases if alias in name or alias in text and alias in name)

    response = max(
        numeric,
        key=lambda col: score(
            col,
            ["yield", "score", "response", "height", "weight", "production",
             "output", "growth", "rate", "value", "measurement"],
        ),
        default=None,
    )

    def choose(aliases, excluded=()):
        available = [col for col in categorical if col not in excluded]
        if not available:
            return None
        ranked = sorted(
            available,
            key=lambda col: score(col, aliases),
            reverse=True,
        )
        return ranked[0]

    if design in {"Completely Randomized Design", "Factorial Completely Randomized Design"}:
        treatment = choose(
            ["treatment", "fertilizer", "variety", "method", "dose", "irrigation"],
        )
        factor_b = None
        if design == "Factorial Completely Randomized Design":
            factor_b = choose(
                ["factor b", "nitrogen", "irrigation", "dose", "variety", "method"],
                excluded=(treatment,),
            )
        return {
            "response": response,
            "treatment": treatment,
            "factor_a": treatment,
            "factor_b": factor_b,
        }

    if design in {"Randomized Block Design", "Factorial Randomized Block Design"}:
        treatment = choose(
            ["treatment", "fertilizer", "variety", "method", "dose", "irrigation"],
        )
        block = choose(["block", "replication", "rep", "location", "farm", "field"], (treatment,))
        factor_b = None
        if design == "Factorial Randomized Block Design":
            factor_b = choose(
                ["factor b", "nitrogen", "irrigation", "dose", "variety", "method"],
                excluded=(treatment, block),
            )
        return {
            "response": response,
            "treatment": treatment,
            "block": block,
            "factor_a": treatment,
            "factor_b": factor_b,
        }

    if design == "Latin Square Design":
        treatment = choose(["treatment", "fertilizer", "variety", "method", "dose"])
        row = choose(["row", "replication", "rep"], (treatment,))
        column = choose(["column", "col"], (treatment, row))
        remaining = [col for col in categorical if col not in {treatment, row, column}]
        if row is None and remaining:
            row = remaining[0]
        if column is None and remaining:
            column = remaining[0]
        return {
            "response": response,
            "treatment": treatment,
            "row": row,
            "column": column,
        }

    if design in {"Split-Plot Design", "Split-Split Plot Design", "Strip-Plot Design"}:
        factor_a = choose(["main plot", "whole plot", "factor a", "irrigation", "variety", "treatment"])
        factor_b = choose(["subplot", "factor b", "nitrogen", "dose", "fertilizer"], (factor_a,))
        factor_c = None
        if design == "Split-Split Plot Design":
            factor_c = choose(["sub-subplot", "factor c", "variety", "dose", "time"], (factor_a, factor_b))
        block = choose(["block", "replication", "rep"], (factor_a, factor_b, factor_c))
        return {
            "response": response,
            "factor_a": factor_a,
            "factor_b": factor_b,
            "factor_c": factor_c,
            "block": block,
        }

    return {}


def run_experimental_design_analysis(df, problem, design=None):
    """Infer roles and run the corresponding experimental-design ANOVA."""
    detected = detect_experimental_design(problem)
    design = design or detected["design"]
    if not design:
        return None

    roles = infer_design_columns(df, problem, design)
    response = roles.get("response")
    if not response:
        return {"design": design, "roles": roles, "result": None, "error": "No numerical response was identified."}

    try:
        if design == "Completely Randomized Design":
            result = crd_anova(df, response, roles.get("treatment"))
        elif design == "Randomized Block Design":
            result = rbd_anova(df, response, roles.get("treatment"), roles.get("block"))
        elif design == "Latin Square Design":
            result = latin_square_anova(df, response, roles.get("treatment"), roles.get("row"), roles.get("column"))
        elif design == "Factorial Completely Randomized Design":
            result = factorial_crd_anova(df, response, roles.get("factor_a"), roles.get("factor_b"))
        elif design == "Factorial Randomized Block Design":
            result = factorial_rbd_anova(df, response, roles.get("factor_a"), roles.get("factor_b"), roles.get("block"))
        elif design == "Split-Plot Design":
            result = split_plot_anova(df, response, roles.get("factor_a"), roles.get("factor_b"), roles.get("block"))
        elif design == "Split-Split Plot Design":
            result = split_split_plot_anova(df, response, roles.get("factor_a"), roles.get("factor_b"), roles.get("factor_c"), roles.get("block"))
        elif design == "Strip-Plot Design":
            result = strip_plot_anova(df, response, roles.get("factor_a"), roles.get("factor_b"), roles.get("block"))
        else:
            result = None
    except Exception as exc:
        return {"design": design, "roles": roles, "result": None, "error": str(exc)}

    return {"design": design, "roles": roles, "result": result, "error": None}
