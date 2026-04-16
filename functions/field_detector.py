import re
import json
from pathlib import Path
from fuzzywuzzy import process, fuzz

class FieldDetector:
    def __init__(self, pattern_path="data/patterns.json"):
        self.pattern_path = Path(pattern_path)
        self.patterns = self.load_patterns()

    def load_patterns(self):
        if self.pattern_path.exists():
            with open(self.pattern_path, "r") as f:
                return json.load(f)
        return {
            "gst": ["gst", "gstin", "gst no"],
            "total": ["total", "amount", "grand total"],
            "date": ["date", "dated"],
            "invoice_no": ["invoice", "inv #"]
        }

    def find_value_near_keyword(self, text, keywords, value_pattern, window=30):
        """Find a pattern (like a date or amount) near a dynamic keyword."""
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            # Check if any keyword is in the line
            for kw in keywords:
                if kw in line_lower:
                    # Look for the value pattern in the same line or nearby context
                    match = re.search(value_pattern, line, re.IGNORECASE)
                    if match:
                        return match.group(0).strip()
        return None

    def extract_intelligent(self, text):
        results = {}
        
        # Regexes for values
        regexes = {
            "gst": r"\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]",
            "total": r"(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)",
            "date": r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})\b",
            "invoice_no": r"(?:INV|No|#)?[A-Z0-9\-/]+"
        }

        for field, keywords in self.patterns.items():
            val = self.find_value_near_keyword(text, keywords, regexes.get(field, r".*"))
            results[field] = val

        # Fallback to pure regex if keyword matching failed
        for field, pattern in regexes.items():
            if not results.get(field):
                match = re.search(pattern, text)
                if match:
                    results[field] = match.group(0)

        return results

    def add_learned_keyword(self, field, new_keyword):
        if field in self.patterns:
            if new_keyword.lower() not in self.patterns[field]:
                self.patterns[field].append(new_keyword.lower())
                with open(self.pattern_path, "w") as f:
                    json.dump(self.patterns, f)
