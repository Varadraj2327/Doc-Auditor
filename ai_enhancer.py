"""Optional AI-style helper utilities.

This module is intentionally lightweight so beginners can understand it,
while still showing where LLM APIs can plug into the pipeline.
"""

from __future__ import annotations

from typing import Dict, Optional

from validator import ValidationResult



def generate_natural_language_summary(fields: Dict[str, Optional[str]], result: ValidationResult) -> str:
    """Create a human-friendly explanation of compliance outcome."""
    if result.status == "PASS":
        return (
            "The document appears compliant. All required invoice fields were detected "
            "and passed the configured validation checks."
        )

    missing_or_invalid = ", ".join(result.reasons)
    return (
        "The document is not compliant based on current rules. "
        f"Key issues found: {missing_or_invalid} "
        "Please correct these fields and re-run the audit."
    )
