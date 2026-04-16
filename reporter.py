"""Compliance report generation utilities."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from validator import ValidationResult


def _fmt_field(value: Optional[str]) -> str:
    return value if value else "Not Found"



def _safe_file_stem(filename: str) -> str:
    stem = Path(filename).stem
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in stem)



def build_report_text(source_file: str, extracted_fields: Dict[str, Optional[str]], result: ValidationResult) -> str:
    lines = [
        "--- Compliance Report ---",
        f"Source File: {source_file}",
        f"Generated At: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"Status: {result.status}",
        "",
        "Field Summary:",
        f"- GST ID: {_fmt_field(extracted_fields.get('gst_id'))}",
        f"- Invoice Number: {_fmt_field(extracted_fields.get('invoice_number'))}",
        f"- Date: {_fmt_field(extracted_fields.get('invoice_date'))}",
        f"- Total Amount: {_fmt_field(extracted_fields.get('total_amount'))}",
        "",
        "Validation Checks:",
    ]

    for check in result.checks:
        prefix = "[OK]" if "Valid" in check or "Present" in check else "[FAIL]"
        lines.append(f"{prefix} {check}")

    lines.extend(["", "Reasons:"])
    if result.reasons:
        lines.extend([f"- {reason}" for reason in result.reasons])
    else:
        lines.append("- No compliance issues found.")

    return "\n".join(lines)



def save_report_files(
    source_file: str,
    extracted_fields: Dict[str, Optional[str]],
    result: ValidationResult,
    output_dir: str | Path = "reports",
) -> Dict[str, str]:
    """Save both TXT and JSON compliance reports."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    base_name = f"compliance_report_{_safe_file_stem(source_file)}_{timestamp}"

    text_report = build_report_text(source_file, extracted_fields, result)
    txt_file = out_path / f"{base_name}.txt"
    txt_file.write_text(text_report, encoding="utf-8")

    json_payload = {
        "source_file": source_file,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": result.status,
        "extracted_fields": extracted_fields,
        "checks": result.checks,
        "reasons": result.reasons,
    }
    json_file = out_path / f"{base_name}.json"
    json_file.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    return {"text": str(txt_file), "json": str(json_file), "rendered_text": text_report}
