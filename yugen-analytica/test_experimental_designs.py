import pandas as pd

from src.experimental_designs import (
    detect_experimental_design,
    experimental_design_plan,
    crd_anova,
    rbd_anova,
    latin_square_anova,
    factorial_crd_anova,
    factorial_rbd_anova,
    split_plot_anova,
    split_split_plot_anova,
    strip_plot_anova,
)


def test_design_language_detection():
    assert detect_experimental_design(
        "Four fertilizers were tested in a randomized complete block design."
    )["design"] == "Randomized Block Design"

    assert detect_experimental_design(
        "Treatments were arranged in a Latin square with each treatment once per row and column."
    )["design"] == "Latin Square Design"

    assert detect_experimental_design(
        "Irrigation was the main-plot factor and nitrogen was the subplot factor in a split-plot experiment."
    )["design"] == "Split-Plot Design"


def test_crd_anova():
    df = pd.DataFrame({
        "Treatment": ["A", "A", "B", "B", "C", "C"],
        "Yield": [10, 11, 14, 15, 18, 17],
    })
    result = crd_anova(df, "Yield", "Treatment")
    assert result is not None
    assert "C(Q(\"Treatment\"))" in result["ANOVA Table"]["Source"].tolist()


def test_rbd_anova():
    df = pd.DataFrame({
        "Block": ["B1", "B1", "B1", "B2", "B2", "B2"],
        "Treatment": ["A", "B", "C", "A", "B", "C"],
        "Yield": [10, 13, 17, 11, 14, 18],
    })
    assert rbd_anova(df, "Yield", "Treatment", "Block") is not None


def test_latin_square_anova():
    df = pd.DataFrame({
        "Row": ["R1", "R1", "R1", "R2", "R2", "R2", "R3", "R3", "R3"],
        "Column": ["C1", "C2", "C3"] * 3,
        "Treatment": ["A", "B", "C", "B", "C", "A", "C", "A", "B"],
        "Yield": [10, 12, 14, 11, 15, 13, 16, 14, 12],
    })
    assert latin_square_anova(df, "Yield", "Treatment", "Row", "Column") is not None


def test_factorial_designs():
    rows = []
    for block in ["B1", "B2"]:
        for a in ["A1", "A2"]:
            for b in ["B1", "B2"]:
                rows.append({
                    "Block": block,
                    "A": a,
                    "B": b,
                    "Yield": 10 + (a == "A2") * 2 + (b == "B2") * 3,
                })
    df = pd.DataFrame(rows)
    assert factorial_crd_anova(df, "Yield", "A", "B") is not None
    assert factorial_rbd_anova(df, "Yield", "A", "B", "Block") is not None


def test_split_plot_family():
    rows = []
    for block in ["B1", "B2", "B3"]:
        for a in ["A1", "A2"]:
            for b in ["B1", "B2"]:
                rows.append({
                    "Block": block,
                    "A": a,
                    "B": b,
                    "C": "C1",
                    "Yield": 10,
                })
    df = pd.DataFrame(rows)

    assert split_plot_anova(df, "Yield", "A", "B", "Block") is not None
    assert split_split_plot_anova(
        df, "Yield", "A", "B", "C", "Block"
    ) is not None
    assert strip_plot_anova(df, "Yield", "A", "B", "Block") is not None


def test_design_plan_contains_experimental_structure():
    plan = experimental_design_plan(
        "Three fertilizers were compared in a randomized complete block design with five blocks."
    )
    assert plan is not None
    assert plan["design"] == "Randomized Block Design"
    assert plan["blocking_factor"] == "Block"
    assert "error_structure" in plan
