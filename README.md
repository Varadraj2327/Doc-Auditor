# Doc-Auditor (RPA + Compliance Automation)

Doc-Auditor is a beginner-to-intermediate Python project that automates invoice PDF compliance checks using rule-based validation, with optional OCR, web upload, logging, and email alerts.

## Project Objective

The system:
- Accepts PDF input (CLI or Flask upload)
- Extracts text from single/multi-page PDFs
- Detects key invoice fields
- Validates fields using compliance rules
- Generates readable PASS/FAIL reports with reasons

## Folder Structure

```text
doc-auditor/
├── main.py                 # CLI entry point
├── app.py                  # Optional Flask web app
├── extractor.py            # PDF + OCR text extraction
├── validator.py            # Field extraction + validation engine
├── reporter.py             # TXT/JSON compliance report generator
├── audit_logger.py         # Audit trail logging setup
├── notifier.py             # Optional SMTP failure notifications
├── ai_enhancer.py          # Optional natural-language explanation helper
├── requirements.txt        # Dependencies
├── templates/
│   └── index.html          # Upload and results page
├── static/
│   └── style.css           # Basic UI styling
├── sample_docs/
│   ├── invoice_pass.pdf    # Demo input that should PASS
│   └── invoice_fail.pdf    # Demo input that should FAIL
├── uploads/                # Web-uploaded files (auto-created)
└── reports/                # Generated TXT/JSON reports + audit.log
```

## Key Compliance Rules

- GST ID must exist and match GSTIN format
- Invoice Number must be present
- Date must be present and parseable
- Total Amount must be present and greater than 0

## Installation

1. Open terminal in `doc-auditor` directory.
2. Create virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run CLI Version

```powershell
python main.py --file sample_docs\invoice_pass.pdf
python main.py --file sample_docs\invoice_fail.pdf
```

Optional flags:

```powershell
python main.py --file sample_docs\invoice_fail.pdf --ocr
python main.py --file sample_docs\invoice_fail.pdf --notify-email yourmail@example.com
python main.py --file sample_docs\invoice_pass.pdf --reports-dir reports
```

CLI exit codes:
- `0` = PASS
- `2` = FAIL (validation errors)
- `1` = processing/extraction error

## Run Web Interface (Flask)

```powershell
python app.py
```

Then open: `http://127.0.0.1:5000`

Features:
- Upload one or many PDFs in one run
- Optional OCR fallback checkbox
- Optional AI-style compliance summary
- Optional extracted-text preview
- View extracted fields, checks, reasons per file
- Download generated TXT and JSON reports from the browser

## Optional OCR Setup Notes

OCR path requires:
- `pytesseract`
- `pdf2image`
- Tesseract OCR installed on your system and accessible in PATH

## Optional Email Alert Setup

Set environment variables before running:

```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="your_user"
$env:SMTP_PASS="your_password"
$env:SMTP_FROM="your_email@example.com"
```

Then use:

```powershell
python main.py --file sample_docs\invoice_fail.pdf --notify-email recipient@example.com
```

## Functional Flow

User Upload/Input -> Text Extraction -> Field Detection -> Validation -> Report Generation -> Output Display

## Notes for College Demo

- Start with `invoice_pass.pdf` and `invoice_fail.pdf`
- Show CLI and web interface in one demo
- Explain modular code (extractor/validator/reporter separation)
- Mention optional OCR and email features as scalability points

## Future Improvements

- Plug LLM API for stronger field extraction on unstructured layouts
- Add dashboard with historical report trends
- Add batch folder processing + scheduler for RPA-style automation
- Add unit tests for validation rules
