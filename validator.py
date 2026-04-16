"""Field extraction and compliance validation for Doc-Auditor."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


# Indian GSTIN pattern: 15 chars, state+PAN+entity+Z+checksum
GST_PATTERN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]\b")
INVOICE_PATTERN = re.compile(
    r"(?:invoice\s*(?:number|no|#)\s*[:\-]?\s*)([A-Z0-9\-/]+)",
    re.IGNORECASE,
)
INVOICE_FALLBACK_PATTERN = re.compile(r"\b(INV[-/]?[A-Z0-9-]{3,})\b", re.IGNORECASE)
DATE_PATTERNS = [
    re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b"),
    re.compile(r"\b(\d{4}[/-]\d{2}[/-]\d{2})\b"),
    re.compile(r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b"),
]
TOTAL_PATTERN = re.compile(
    r"(?:total\s*(?:amount)?|grand\s*total|amount\s*due)\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


@dataclass
class ValidationResult:
    status: str
    reasons: List[str]
    checks: List[str]



def _safe_find(pattern: re.Pattern, text: str) -> Optional[str]:
    match = pattern.search(text)
    if not match:
        return None
    if match.lastindex:
        return match.group(1).strip()
    return match.group(0).strip()



def _extract_date(text: str) -> Optional[str]:
    for pattern in DATE_PATTERNS:
        found = _safe_find(pattern, text)
        if found:
            return found
    return None



def _parse_amount(amount_raw: Optional[str]) -> Optional[float]:
    if not amount_raw:
        return None
    cleaned = amount_raw.replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None



def extract_fields(text: str) -> Dict[str, Optional[str]]:
    """Extract key invoice fields from text using regex heuristics."""
    gst_id = _safe_find(GST_PATTERN, text)
    invoice_no = _safe_find(INVOICE_PATTERN, text)
    if not invoice_no:
        invoice_no = _safe_find(INVOICE_FALLBACK_PATTERN, text)
    invoice_date = _extract_date(text)

    total_raw = _safe_find(TOTAL_PATTERN, text)
    total_amount = _parse_amount(total_raw)

    return {
        "gst_id": gst_id,
        "invoice_number": invoice_no,
        "invoice_date": invoice_date,
        "total_amount": str(total_amount) if total_amount is not None else None,
    }



def _is_date_valid(date_str: str) -> bool:
    date_formats = ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d", "%d %B %Y", "%d %b %Y")
    for fmt in date_formats:
        try:
            datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    return False



def validate_fields(fields: Dict[str, Optional[str]]) -> ValidationResult:
    """Validate extracted fields with compliance rules."""
    reasons: List[str] = []
    checks: List[str] = []

    gst_id = fields.get("gst_id")
    if not gst_id:
        reasons.append("GST ID is missing.")
        checks.append("GST ID: Missing")
    elif not GST_PATTERN.fullmatch(gst_id):
        reasons.append("GST ID format is invalid.")
        checks.append("GST ID: Invalid format")
    else:
        checks.append("GST ID: Valid")

    invoice_number = fields.get("invoice_number")
    if not invoice_number:
        reasons.append("Invoice number is missing.")
        checks.append("Invoice Number: Missing")
    else:
        checks.append("Invoice Number: Present")

    invoice_date = fields.get("invoice_date")
    if not invoice_date:
        reasons.append("Invoice date is missing.")
        checks.append("Date: Missing")
    elif not _is_date_valid(invoice_date):
        reasons.append("Invoice date format is invalid.")
        checks.append("Date: Invalid format")
    else:
        checks.append("Date: Valid")

    amount_raw = fields.get("total_amount")
    amount_value = _parse_amount(amount_raw)
    if amount_raw is None:
        reasons.append("Total amount is missing.")
        checks.append("Total Amount: Missing")
    elif amount_value is None:
        reasons.append("Total amount is not a valid number.")
        checks.append("Total Amount: Invalid number")
    elif amount_value <= 0:
        reasons.append("Total amount must be greater than 0.")
        checks.append("Total Amount: Invalid value")
    else:
        checks.append("Total Amount: Valid")

    status = "PASS" if not reasons else "FAIL"
    return ValidationResult(status=status, reasons=reasons, checks=checks)
