"""Logging utilities for audit trails."""

from __future__ import annotations

import logging
from pathlib import Path


def setup_logger(log_dir: str | Path = "reports") -> logging.Logger:
    """Create a reusable logger that writes to file and console."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("doc_auditor")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(log_path / "audit.log", encoding="utf-8")
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
