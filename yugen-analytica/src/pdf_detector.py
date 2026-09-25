import io

import pdfplumber
from pypdf import PdfReader


def detect_pdf(uploaded_file):
    """Inspect a PDF and classify its pages for dataset extraction."""
    raw = uploaded_file.getvalue()
    reader = PdfReader(io.BytesIO(raw))

    pages = []
    total_text_chars = 0
    total_tables = 0

    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            text_chars = len(text.strip())
            table_count = len(tables)

            total_text_chars += text_chars
            total_tables += table_count

            if table_count:
                page_type = "table"
            elif text_chars >= 30:
                page_type = "text"
            else:
                page_type = "scanned_or_image"

            pages.append({
                "Page": index,
                "Type": page_type,
                "Text Characters": text_chars,
                "Tables Detected": table_count,
            })

    if total_tables:
        document_type = "table_pdf"
    elif total_text_chars >= 30:
        document_type = "text_pdf"
    else:
        document_type = "scanned_pdf"

    return {
        "Pages": len(reader.pages),
        "Document Type": document_type,
        "Total Text Characters": total_text_chars,
        "Total Tables Detected": total_tables,
        "Page Details": pages,
    }


def extract_pdf_tables(uploaded_file):
    """Extract detected PDF tables into pandas DataFrames."""
    import pandas as pd

    raw = uploaded_file.getvalue()
    frames = []

    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table_number, table in enumerate(page.extract_tables() or [], start=1):
                if not table:
                    continue

                rows = [
                    [cell.strip() if isinstance(cell, str) else cell for cell in row]
                    for row in table
                    if row and any(cell not in (None, "") for cell in row)
                ]

                if len(rows) < 2:
                    continue

                header = rows[0]
                data = rows[1:]
                seen = {}
                clean_header = []

                for column_index, value in enumerate(header, start=1):
                    name = str(value or "").strip() or f"Column_{column_index}"
                    count = seen.get(name, 0) + 1
                    seen[name] = count
                    clean_header.append(
                        name if count == 1 else f"{name}_{count}"
                    )

                frame = pd.DataFrame(data, columns=clean_header)
                frame["__PDF_Page"] = page_number
                frame["__PDF_Table"] = table_number
                frames.append(frame)

    return frames
