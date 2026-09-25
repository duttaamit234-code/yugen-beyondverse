import pandas as pd

from src.question_engine import interpret_question


def sample_dataset():
    return pd.DataFrame({
        "Student_ID": range(101, 116),
        "Study_Hours": [2, 3, 4, 5, 6, 7, 8, 2, 4, 6, 7, 9, 3, 5, 8],
        "Attendance_%": [62, 68, 71, 76, 81, 84, 91, 60, 74, 79, 87, 94, 66, 78, 89],
        "Teaching_Method": [
            "Traditional", "Traditional", "Traditional", "Traditional", "Traditional",
            "Digital", "Digital", "Digital", "Digital", "Digital",
            "Blended", "Blended", "Blended", "Blended", "Blended",
        ],
        "Exam_Score": [45, 49, 54, 58, 63, 68, 73, 51, 57, 69, 75, 84, 55, 65, 78],
    })


def test_narrative_group_comparison():
    question = (
        "A college wants to determine whether the method of teaching affects "
        "students' final examination performance. Students were taught using "
        "Traditional, Digital, or Blended methods. Determine whether there is a "
        "statistically significant difference in mean examination scores among "
        "the three teaching methods at the 5% significance level."
    )
    result = interpret_question(sample_dataset(), question)
    assert result["status"] == "ready"
    assert result["alpha"] == 0.05
    assert result["candidates"][0]["analysis"] == "One-way ANOVA"
    assert result["candidates"][0]["grouping"] == "Teaching_Method"
    assert result["candidates"][0]["response"] == "Exam_Score"


def test_narrative_correlation():
    question = (
        "A researcher wants to determine whether students who spend more time "
        "studying tend to obtain higher examination scores and whether there is "
        "a statistically significant linear relationship between study time and "
        "examination performance."
    )
    result = interpret_question(sample_dataset(), question)
    assert result["status"] == "ready"
    assert result["candidates"][0]["analysis"] == (
        "Pearson correlation + simple linear regression"
    )
