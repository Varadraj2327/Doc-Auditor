"""CLI entry point for Doc-Auditor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audit_logger import setup_logger
from extractor import PDFExtractionError, extract_text_from_pdf
from notifier import send_failure_email
from reporter import save_report_files
from validator import extract_fields, validate_fields


def run_audit(
    pdf_path: str,
    use_ocr: bool = False,
    ocr_lang: str = "eng",
    reports_dir: str = "reports",
    notify_email: str | None = None,
) -> int:
    """Execute end-to-end audit pipeline and print output."""
    logger = setup_logger(reports_dir)
    logger.info("Starting audit for file: %s", pdf_path)

    try:
        text = extract_text_from_pdf(pdf_path, use_ocr=use_ocr, ocr_lang=ocr_lang)
    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        print(f"Error: {exc}")
        return 1
    except PDFExtractionError as exc:
        logger.error("Extraction failed: %s", exc)
        print(f"Extraction failed: {exc}")
        return 1

    fields = extract_fields(text)
    validation_result = validate_fields(fields)

    saved = save_report_files(Path(pdf_path).name, fields, validation_result, reports_dir)
    print(saved["rendered_text"])
    print("\nSaved Reports:")
    print(f"- TXT : {saved['text']}")
    print(f"- JSON: {saved['json']}")
    logger.info("Audit completed with status: %s", validation_result.status)

    if validation_result.status == "FAIL" and notify_email:
        try:
            send_failure_email(
                subject=f"Doc-Auditor Compliance Alert: {Path(pdf_path).name}",
                body=saved["rendered_text"],
                recipient=notify_email,
            )
            logger.info("Failure notification sent to %s", notify_email)
        except Exception as exc:  # noqa: BLE001 - notifier errors should not crash audit
            logger.warning("Failed to send email notification: %s", exc)
            print(f"Warning: email notification failed: {exc}")

    return 0 if validation_result.status == "PASS" else 2



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Doc-Auditor: RPA + Compliance automation for invoice-like PDFs."
    )
    parser.add_argument("--file", required=True, help="Path to input PDF file")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR fallback for scanned PDFs")
    parser.add_argument("--ocr-lang", default="eng", help="OCR language code for pytesseract")
    parser.add_argument("--reports-dir", default="reports", help="Directory to store generated reports")
    parser.add_argument("--notify-email", help="Optional recipient email for FAIL notifications")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    sys.exit(
        run_audit(
            args.file,
            use_ocr=args.ocr,
            ocr_lang=args.ocr_lang,
            reports_dir=args.reports_dir,
            notify_email=args.notify_email,
        )
    )
