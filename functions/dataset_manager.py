import os
import zipfile
import pandas as pd
import json
from pathlib import Path

DATA_DIR = Path("data")
KAGGLE_CONFIG_DIR = Path.home() / ".kaggle"

class DatasetManager:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def is_kaggle_configured(self):
        return (KAGGLE_CONFIG_DIR / "kaggle.json").exists()

    def download_datasets(self):
        """Programmatically download datasets using Kaggle API."""
        if not self.is_kaggle_configured():
            print("Kaggle API not configured. Please place kaggle.json in ~/.kaggle/")
            return False

        try:
            import kaggle
            # Example datasets
            datasets = [
                "abhisheksunil7/invoice-dataset",
                "vbookshelf/v2-sroie-dataset-for-receipt-ocr"
            ]

            for ds in datasets:
                print(f"Downloading {ds}...")
                kaggle.api.dataset_download_files(ds, path=self.data_dir, unzip=True)
            return True
        except Exception as e:
            print(f"Error downloading datasets: {e}")
            return False

    def preprocess_invoice_data(self):
        """Clean and normalize downloaded CSV data."""
        csv_files = list(self.data_dir.glob("*.csv"))
        all_data = []
        
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                # Normalize column names to lowercase
                df.columns = [c.lower() for c in df.columns]
                all_data.append(df)
            except Exception as e:
                print(f"Error processing {file.name}: {e}")

        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            combined.to_csv(self.data_dir / "processed_invoices.csv", index=False)
            return combined
        return None

    def build_pattern_dictionary(self):
        """Extract common field labels from data to build a keyword map."""
        # This would ideally learn from the dataset headers and content
        # For now, we return a base adaptive dictionary
        pattern_dict = {
            "gst": ["gst", "gstin", "gst no", "vat", "tax id"],
            "total": ["total", "amount", "grand total", "net amount", "total due"],
            "date": ["date", "dated", "invoice date", "billing date"],
            "invoice_no": ["invoice", "inv", "bill no", "receipt #"]
        }
        
        # Save for field_detector to use
        with open(self.data_dir / "patterns.json", "w") as f:
            json.dump(pattern_dict, f)
        
        return pattern_dict

if __name__ == "__main__":
    dm = DatasetManager()
    if dm.is_kaggle_configured():
        dm.download_datasets()
    dm.build_pattern_dictionary()
    print("Dataset Manager initialization complete.")
