import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.utils import secure_filename

# Import Intelligent Modules (Using Absolute Package Imports)
from functions.extractor import extract_text_from_pdf
from functions.validator import validate_fields
from functions.field_detector import FieldDetector
from functions.anomaly import AnomalyDetector
from functions.classifier import DocumentClassifier
from functions.dataset_manager import DatasetManager

# Configurations
UPLOAD_FOLDER = '/tmp/uploads'
DATABASE = '/tmp/doc_auditor.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'doc-auditor-secret-prod')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Instantiate Intelligence Engines
field_detector = FieldDetector()
anomaly_detector = AnomalyDetector()
classifier = DocumentClassifier()

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  filename TEXT, date TEXT, doc_type TEXT, 
                  total REAL, status TEXT, anomalies TEXT)''')
    conn.commit()
    conn.close()

# Initialize on startup
init_db()
try:
    DatasetManager().download_datasets()
except:
    pass # Handle cases where Kaggle keys are missing during early build

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    recent = conn.execute('SELECT * FROM history ORDER BY id DESC LIMIT 5').fetchall()
    
    # Calculate stats
    stats = {
        "total": conn.execute('SELECT COUNT(*) FROM history').fetchone()[0],
        "passed": conn.execute('SELECT COUNT(*) FROM history WHERE status="PASS"').fetchone()[0],
        "failed": conn.execute('SELECT COUNT(*) FROM history WHERE status="FAIL"').fetchone()[0],
        "anomalies": conn.execute('SELECT COUNT(*) FROM history WHERE anomalies != ""').fetchone()[0]
    }
    conn.close()
    return render_template('index.html', stats=stats, recent=recent)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # 🛠 RPA PIPELINE
            try:
                # 1. Extraction (Using pdf-only path for now)
                full_text = extract_text_from_pdf(filepath, use_ocr=True)
                
                # 2. Classification
                doc_type = classifier.classify(full_text)
                
                # 3. Intelligent Detection
                extracted_fields = field_detector.extract_intelligent(full_text)
                
                # 4. Compliance Check
                # Map field_detector keys to validator keys
                # field_detector keys: 'gst', 'total', 'date', 'invoice_no'
                # validator keys: 'gst_id', 'invoice_number', 'invoice_date', 'total_amount'
                val_fields = {
                    "gst_id": extracted_fields.get("gst"),
                    "invoice_number": extracted_fields.get("invoice_no"),
                    "invoice_date": extracted_fields.get("date"),
                    "total_amount": extracted_fields.get("total")
                }
                compliance_results = validate_fields(val_fields)
                
                # 5. Anomaly Detection
                total_val = str(extracted_fields.get("total", "0")).replace(',', '').strip()
                try:
                    amount_float = float(total_val)
                except:
                    amount_float = 0
                
                is_anomaly, z_score = anomaly_detector.detect_amount_anomaly(amount_float)
                is_duplicate = anomaly_detector.check_duplicate(extracted_fields)

                anomalies_list = []
                if is_anomaly: anomalies_list.append(f"Amount Anomaly (Z:{z_score:.1f})")
                if is_duplicate: anomalies_list.append("Potential Duplicate")

                # 6. Persistence
                conn = sqlite3.connect(DATABASE)
                conn.execute('INSERT INTO history (filename, date, doc_type, total, status, anomalies) VALUES (?,?,?,?,?,?)',
                          (filename, extracted_fields.get("date", ""), doc_type, 
                           amount_float, compliance_results.status, ", ".join(anomalies_list)))
                conn.commit()
                conn.close()

                flash(f"Successfully audited {filename}", "success")
                return render_template('result.html', 
                                     filename=filename, 
                                     doc_type=doc_type,
                                     fields=val_fields,
                                     compliance=compliance_results,
                                     anomalies=anomalies_list)
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return redirect(url_for('upload'))

    return render_template('upload.html')

@app.route('/history')
def history():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    items = conn.execute('SELECT * FROM history ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('history.html', history=items)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)