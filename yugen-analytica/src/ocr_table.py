import io
from pathlib import Path

import pandas as pd
import pytesseract
from PIL import Image, ImageOps, ImageEnhance
from pytesseract import Output


def _clean_text(value):
    value = str(value).strip()
    return " ".join(value.split())


def _prepare_image(uploaded_file):
    image = Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGB")
    return _prepare_pil_image(image)


def _prepare_pil_image(image):
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(1.5)

    if gray.width < 1600:
        scale = 1600 / gray.width
        gray = gray.resize((int(gray.width * scale), int(gray.height * scale)))

    return gray


def _group_positions(values):
    groups = []
    for value in values:
        if not groups or value > groups[-1][-1] + 1:
            groups.append([value])
        else:
            groups[-1].append(value)
    return [int(sum(group) / len(group)) for group in groups]


def _detect_grid(image):
    import numpy as np
    array = np.array(image)
    dark = array < 120
    vertical_strength = dark.sum(axis=0)
    horizontal_strength = dark.sum(axis=1)

    x_positions = [i for i, value in enumerate(vertical_strength) if value >= image.height * 0.55]
    y_positions = [i for i, value in enumerate(horizontal_strength) if value >= image.width * 0.55]

    x_lines = _group_positions(x_positions)
    y_lines = _group_positions(y_positions)

    if len(x_lines) >= 3 and len(y_lines) >= 3:
        return x_lines, y_lines
    return None, None


def _normalise_headers(headers):
    result = []
    seen = {}
    for index, header in enumerate(headers, start=1):
        header = _clean_text(header)
        if not header:
            header = f"Column_{index}"
        count = seen.get(header, 0) + 1
        seen[header] = count
        result.append(header if count == 1 else f"{header}_{count}")
    return result


def _convert_values(df):
    for column in df.columns:
        series = df[column].astype(str).str.strip()
        numeric = pd.to_numeric(
            series.str.replace(",", "", regex=False).str.replace("%", "", regex=False),
            errors="coerce",
        )
        if numeric.notna().mean() >= 0.75:
            df[column] = numeric
    return df


def _extract_bordered_table(image):
    x_lines, y_lines = _detect_grid(image)
    if not x_lines or not y_lines:
        return None

    rows = []
    confidences = []

    for row_index in range(len(y_lines) - 1):
        row = []
        for column_index in range(len(x_lines) - 1):
            left = x_lines[column_index] + 4
            top = y_lines[row_index] + 4
            right = x_lines[column_index + 1] - 4
            bottom = y_lines[row_index + 1] - 4

            if right <= left or bottom <= top:
                row.append("")
                continue

            cell = image.crop((left, top, right, bottom))
            result = pytesseract.image_to_data(cell, output_type=Output.DICT, config="--psm 7")
            pieces = []

            for text, confidence in zip(result["text"], result["conf"]):
                text = _clean_text(text)
                confidence = float(confidence)
                if text and confidence >= 0:
                    pieces.append(text)
                    confidences.append(confidence)

            row.append(_clean_text(" ".join(pieces)))
        rows.append(row)

    if len(rows) < 2 or len(rows[0]) < 2:
        return None

    headers = _normalise_headers(rows[0])
    df = pd.DataFrame(rows[1:], columns=headers)
    df = df.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all")
    df = _convert_values(df)

    confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return df.reset_index(drop=True), confidence


def _group_words_into_rows(data):
    words = []
    for i, text in enumerate(data["text"]):
        text = _clean_text(text)
        confidence = float(data["conf"][i])
        if not text or confidence < 20:
            continue
        words.append({
            "text": text,
            "x": int(data["left"][i]),
            "y": int(data["top"][i]),
            "w": int(data["width"][i]),
            "h": int(data["height"][i]),
            "conf": confidence,
        })

    words.sort(key=lambda item: (item["y"], item["x"]))
    rows = []

    for word in words:
        center_y = word["y"] + word["h"] / 2
        target = None
        for row in rows:
            if abs(center_y - row["center_y"]) <= max(12, word["h"] * 0.6):
                target = row
                break

        if target is None:
            rows.append({"center_y": center_y, "words": [word]})
        else:
            target["words"].append(word)
            target["center_y"] = sum(
                item["y"] + item["h"] / 2 for item in target["words"]
            ) / len(target["words"])

    for row in rows:
        row["words"].sort(key=lambda item: item["x"])
    return rows


def _assign_words_to_columns(row_words, centers):
    assigned = [[] for _ in centers]
    for word in row_words:
        x = word["x"] + word["w"] / 2
        index = min(range(len(centers)), key=lambda i: abs(x - centers[i][0]))
        assigned[index].append(word["text"])
    return [_clean_text(" ".join(values)) for values in assigned]


def extract_pil_table(image):
    """Extract a table from a PIL image and return DataFrame + OCR confidence."""
    image = _prepare_pil_image(image)

    bordered = _extract_bordered_table(image)
    if bordered is not None:
        return bordered

    data = pytesseract.image_to_data(image, output_type=Output.DICT, config="--psm 6")
    rows = _group_words_into_rows(data)

    if len(rows) < 2:
        raise ValueError("OCR could not detect a table with a header and data rows.")

    header_row = next((row for row in rows if len(row["words"]) >= 2), None)
    if header_row is None:
        raise ValueError("OCR could not identify a table header.")

    centers = [
        (word["x"] + word["w"] / 2, _clean_text(word["text"]))
        for word in header_row["words"]
    ]

    if len(centers) < 2:
        raise ValueError("OCR found too few columns. Use a clearer table image.")

    headers = _normalise_headers([item[1] for item in centers])
    data_rows = []

    for row in rows:
        if row is header_row or row["center_y"] <= header_row["center_y"]:
            continue
        values = _assign_words_to_columns(row["words"], centers)
        if sum(bool(value) for value in values) >= 2:
            data_rows.append(values)

    if not data_rows:
        raise ValueError("OCR detected the header but no data rows.")

    df = pd.DataFrame(data_rows, columns=headers)
    df = df.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all")
    df = _convert_values(df)

    confidence_values = [
        float(value) for value in data["conf"]
        if str(value).strip() and float(value) >= 0
    ]
    confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    return df.reset_index(drop=True), confidence


def extract_table_from_image(uploaded_file):
    """Extract a table from a PNG/JPEG upload."""
    return extract_pil_table(Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGB"))


def extract_tables_from_scanned_pdf(uploaded_file, dpi=150):
    """Render scanned PDF pages and pass each page through the existing OCR engine."""
    import pdf2image

    raw = uploaded_file.getvalue()
    pages = pdf2image.convert_from_bytes(raw, dpi=dpi, fmt="png")

    results = []

    for page_number, image in enumerate(pages, start=1):
        try:
            dataframe, confidence = extract_pil_table(image)
            dataframe["__PDF_Page"] = page_number
            results.append({
                "page": page_number,
                "dataframe": dataframe,
                "confidence": confidence,
            })
        except ValueError as exc:
            results.append({
                "page": page_number,
                "dataframe": None,
                "confidence": 0.0,
                "error": str(exc),
            })

    return results
