import unittest

import pandas as pd

from src.question_engine import interpret_question


class QuestionEngineTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            "Student_ID": range(1, 9),
            "Fertilizer": ["A", "A", "B", "B", "C", "C", "A", "B"],
            "Yield": [48, 50, 61, 63, 75, 78, 49, 62],
            "Study_Hours": [1, 2, 3, 4, 5, 6, 7, 8],
            "Exam_Score": [42, 45, 51, 55, 61, 65, 70, 76],
        })

    def test_group_effect_question(self):
        result = interpret_question(
            self.df,
            "Does fertilizer affect crop yield?"
        )
        self.assertIn(result["status"], {"ready", "ambiguous"})
        self.assertTrue(
            any(
                item.get("analysis") == "One-way ANOVA"
                for item in result["candidates"]
            )
        )

    def test_relationship_question(self):
        result = interpret_question(
            self.df,
            "Is study time related to exam score?"
        )
        self.assertEqual(result["intent"], "correlation")
        self.assertTrue(
            any(
                item.get("analysis") == "Pearson correlation + simple linear regression"
                for item in result["candidates"]
            )
        )

    def test_prediction_question(self):
        result = interpret_question(
            self.df,
            "Can exam score be predicted from study hours?"
        )
        self.assertEqual(result["intent"], "prediction")
        self.assertTrue(result["candidates"])

    def test_identifier_is_not_selected(self):
        result = interpret_question(
            self.df,
            "Is student ID related to exam score?"
        )
        self.assertNotIn(
            "Student_ID",
            [item["column"] for item in result["matched_columns"]]
        )

    def test_unknown_question_requests_clarification(self):
        result = interpret_question(
            self.df,
            "Which moon phase changes the dataset?"
        )
        self.assertEqual(result["status"], "needs_clarification")


if __name__ == "__main__":
    unittest.main()
