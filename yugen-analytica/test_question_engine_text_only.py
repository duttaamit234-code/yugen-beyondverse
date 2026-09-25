from src.question_engine import extract_tabular_text, interpret_question


def test_text_only_problem_selects_anova():
    question = (
        "A college wants to determine whether teaching methods produce a "
        "statistically significant difference in mean examination scores "
        "among three teaching methods at the 5% significance level."
    )
    result = interpret_question(None, question)

    assert result["status"] == "ready"
    assert result["candidates"][0]["analysis"] == "One-way ANOVA"
    assert result["alpha"] == 0.05


def test_text_only_problem_selects_correlation():
    question = (
        "A researcher wants to determine whether there is a statistically "
        "significant linear relationship between study time and examination performance."
    )
    result = interpret_question(None, question)

    assert result["status"] == "ready"
    assert result["candidates"][0]["analysis"] == "Pearson correlation"


def test_embedded_csv_table_is_detected():
    question = """A researcher compares two treatments.

Student,Treatment,Score
1,A,12
2,A,15
3,B,19
4,B,21
"""
    table = extract_tabular_text(question)

    assert table is not None
    assert list(table.columns) == ["Student", "Treatment", "Score"]
    assert table.shape == (4, 3)


def test_embedded_table_can_drive_analysis():
    question = """Determine whether the treatments differ in mean score.

Student,Treatment,Score
1,A,12
2,A,15
3,B,19
4,B,21
"""
    result = interpret_question(None, question)

    assert result["embedded_data"] is not None
    assert result["candidates"][0]["analysis"] == "Welch two-sample t-test"
