"""PDF text extraction utilities for Doc-Auditor.

This module keeps extraction logic isolated so it can be reused by
CLI workflows, web handlers, and future automation jobs.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


class PDFExtractionError(Exception):
    """Raised when no text can be extracted from a PDF."""


def _extract_with_pdfplumber(pdf_path: Path) -> str:
    """Extract text using pdfplumber page-by-page."""
    import pdfplumber  # local import to keep optional dependency flexible

    pages_text: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages_text.append(f"\n--- Page {page_no} ---\n{page_text}")
    return "\n".join(pages_text).strip()


def _extract_with_pypdf2(pdf_path: Path) -> str:
    """Fallback extraction using PyPDF2."""
    from PyPDF2 import PdfReader  # local import

    reader = PdfReader(str(pdf_path))
    pages_text: List[str] = []
    for page_no, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages_text.append(f"\n--- Page {page_no} ---\n{page_text}")
    return "\n".join(pages_text).strip()


def _extract_with_ocr(pdf_path: Path, lang: str = "eng") -> str:
    """OCR extraction path for scanned PDFs.

    Requires optional dependencies:
    - pytesseract
    - pdf2image
    - tesseract binary installed on system
    """
    import pytesseract  # type: ignore
    from pdf2image import convert_from_path  # type: ignore

    pages_text: List[str] = []
    images = convert_from_path(str(pdf_path))
    for page_no, image in enumerate(images, start=1):
        page_text = pytesseract.image_to_string(image, lang=lang) or ""
        if page_text.strip():
            pages_text.append(f"\n--- OCR Page {page_no} ---\n{page_text}")
    return "\n".join(pages_text).strip()


def extract_text_from_pdf(pdf_file: str | Path, use_ocr: bool = False, ocr_lang: str = "eng") -> str:
    """Extract text from a PDF using primary and fallback methods.

    Args:
        pdf_file: path to the input PDF.
        use_ocr: enable OCR fallback for scanned PDFs.
        ocr_lang: OCR language passed to pytesseract.

    Returns:
        Extracted text.

    Raises:
        FileNotFoundError: if input PDF does not exist.
        PDFExtractionError: when extraction fails or produces empty text.
    """
    pdf_path = Path(pdf_file)
    if not pdf_path.exists() or not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    extraction_errors: List[str] = []

    for method_name, method in (
        ("pdfplumber", _extract_with_pdfplumber),
        ("PyPDF2", _extract_with_pypdf2),
    ):
        try:
            text = method(pdf_path)
            if text.strip():
                return text
        except Exception as exc:  # noqa: BLE001 - gather all extraction failures
            extraction_errors.append(f"{method_name}: {exc}")

    if use_ocr:
        try:
            text = _extract_with_ocr(pdf_path, lang=ocr_lang)
            if text.strip():
                return text
        except Exception as exc:  # noqa: BLE001
            extraction_errors.append(f"OCR: {exc}")

    details = "; ".join(extraction_errors) if extraction_errors else "No readable text found."
    raise PDFExtractionError(f"Unable to extract text from {pdf_path.name}. Details: {details}")
