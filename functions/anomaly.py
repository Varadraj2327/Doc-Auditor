import numpy as np
import pandas as pd
from pathlib import Path

class AnomalyDetector:
    def __init__(self, data_file="data/processed_invoices.csv"):
        self.data_file = Path(data_file)
        self.stats = self.calculate_baseline()

    def calculate_baseline(self):
        if self.data_file.exists():
            df = pd.read_csv(self.data_file)
            if 'total' in df.columns:
                return {
                    "mean": df['total'].mean(),
                    "std": df['total'].std()
                }
        return {"mean": 1000, "std": 500} # Default fallback

    def detect_amount_anomaly(self, amount):
        try:
            val = float(str(amount).replace(',', ''))
            z_score = (val - self.stats['mean']) / self.stats['std'] if self.stats['std'] > 0 else 0
            
            is_anomaly = abs(z_score) > 3 # Threshold for anomaly
            return is_anomaly, z_score
        except:
            return False, 0

    def check_duplicate(self, current_doc, history_file="data/history.csv"):
        """Check if GST + Total + Date combination exists."""
        history_path = Path(history_file)
        if not history_path.exists():
            return False

        try:
            df = pd.read_csv(history_path)
            # Match strictly
            mask = (
                (df['gst'] == current_doc.get('gst')) & 
                (df['total'] == current_doc.get('total')) & 
                (df['date'] == current_doc.get('date'))
            )
            return mask.any()
        except:
            return False
