class DocumentClassifier:
    def __init__(self):
        self.categories = {
            "invoice": ["invoice", "tax invoice", "bill to", "purchase order"],
            "receipt": ["receipt", "cash memo", "transaction", "paid"],
            "contract": ["agreement", "contract", "terms", "hereby", "undersigned"]
        }

    def classify(self, text):
        text_lower = text.lower()
        scores = {}
        
        for cat, keywords in self.categories.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[cat] = score

        best_cat = max(scores, key=scores.get)
        if scores[best_cat] == 0:
            return "Unknown"
        return best_cat.capitalize()
