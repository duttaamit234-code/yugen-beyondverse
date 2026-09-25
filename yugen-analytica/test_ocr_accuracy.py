import unittest

from src.ocr_accuracy import calculate_ocr_accuracy, normalize_ocr_text


class OcrAccuracyTests(unittest.TestCase):
    def test_identical_text_is_perfect(self):
        result = calculate_ocr_accuracy("A B C", "A B C")
        self.assertEqual(result["CER"], 0.0)
        self.assertEqual(result["WER"], 0.0)
        self.assertEqual(result["Character Accuracy"], 1.0)
        self.assertEqual(result["Word Accuracy"], 1.0)

    def test_single_character_error(self):
        result = calculate_ocr_accuracy("cat", "bat")
        self.assertEqual(result["Character Edit Distance"], 1)
        self.assertEqual(result["CER"], 1 / 3)

    def test_word_error_rate(self):
        result = calculate_ocr_accuracy(
            "student exam score",
            "student test score",
        )
        self.assertEqual(result["Word Edit Distance"], 1)
        self.assertEqual(result["WER"], 1 / 3)

    def test_whitespace_and_case_are_normalized(self):
        self.assertEqual(
            normalize_ocr_text(" Student   SCORE\n"),
            "student score",
        )


if __name__ == "__main__":
    unittest.main()
