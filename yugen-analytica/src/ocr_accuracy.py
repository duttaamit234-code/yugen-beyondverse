import re


def normalize_ocr_text(text):
    """Normalize OCR and ground-truth text before comparison."""
    text = "" if text is None else str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def _levenshtein(sequence_a, sequence_b):
    """Calculate Levenshtein edit distance for strings or token lists."""
    if len(sequence_a) < len(sequence_b):
        sequence_a, sequence_b = sequence_b, sequence_a

    previous = list(range(len(sequence_b) + 1))

    for i, value_a in enumerate(sequence_a, start=1):
        current = [i]

        for j, value_b in enumerate(sequence_b, start=1):
            insertion = current[j - 1] + 1
            deletion = previous[j] + 1
            substitution = previous[j - 1] + (value_a != value_b)
            current.append(min(insertion, deletion, substitution))

        previous = current

    return previous[-1]


def calculate_ocr_accuracy(ground_truth, ocr_output):
    """Compare OCR output against ground truth using CER and WER.

    Returns edit distances, error rates, and corresponding accuracy values.
    Accuracy is defined as 1 - error rate and is bounded to [0, 1].
    """
    reference = normalize_ocr_text(ground_truth)
    hypothesis = normalize_ocr_text(ocr_output)

    reference_chars = list(reference)
    hypothesis_chars = list(hypothesis)

    reference_words = reference.split()
    hypothesis_words = hypothesis.split()

    character_distance = _levenshtein(
        reference_chars,
        hypothesis_chars,
    )
    word_distance = _levenshtein(
        reference_words,
        hypothesis_words,
    )

    character_count = len(reference_chars)
    word_count = len(reference_words)

    character_error_rate = (
        character_distance / character_count
        if character_count
        else (0.0 if not hypothesis_chars else 1.0)
    )

    word_error_rate = (
        word_distance / word_count
        if word_count
        else (0.0 if not hypothesis_words else 1.0)
    )

    return {
        "Character Edit Distance": character_distance,
        "Word Edit Distance": word_distance,
        "Reference Characters": character_count,
        "Reference Words": word_count,
        "CER": character_error_rate,
        "WER": word_error_rate,
        "Character Accuracy": max(0.0, min(1.0, 1.0 - character_error_rate)),
        "Word Accuracy": max(0.0, min(1.0, 1.0 - word_error_rate)),
    }
