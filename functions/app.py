import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.utils import secure_filename

# Import Intelligent Modules
from extractor import extract_all
from validator import validate_compliance
from field_detector import extract_intelligent
from anomaly import detect_amount_anomaly, check_duplicate
from classifier import classify_doc
from dataset_manager import DatasetManager

# Configurations
UPLOAD_FOLDER = '/tmp/uploads'
DATABASE = '/tmp/doc_auditor.db'  # Persistent data should usually go to external DB, but /tmp is okay for demo history
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'doc-auditor-secret-prod')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
DatasetManager().download_datasets()

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
            # 1. Extraction
            full_text = extract_all(filepath)
            
            # 2. Classification
            doc_type = classify_doc(full_text)
            
            # 3. Intelligent Detection
            extracted_fields = extract_intelligent(full_text)
            
            # 4. Compliance Check
            compliance_results = validate_compliance(extracted_fields, doc_type)
            
            # 5. Anomaly Detection
            history_info = {"total_amount": extracted_fields.get("total", 0)}
            is_anomaly, z_score = detect_amount_anomaly(extracted_fields.get("total", 0), history_info)
            is_duplicate = check_duplicate(extracted_fields.get("total", 0), extracted_fields.get("date", ""), [])

            anomalies = []
            if is_anomaly: anomalies.append(f"Amount Anomaly (Z:{z_score:.1f})")
            if is_duplicate: anomalies.append("Duplicate Entry Detected")

            # 6. Final Status
            status = "PASS" if not compliance_results["failures"] else "FAIL"
            
            # 7. Persistence
            conn = sqlite3.connect(DATABASE)
            conn.execute('INSERT INTO history (filename, date, doc_type, total, status, anomalies) VALUES (?,?,?,?,?,?)',
                      (filename, extracted_fields.get("date", ""), doc_type, 
                       extracted_fields.get("total", 0), status, ", ".join(anomalies)))
            conn.commit()
            conn.close()

            flash(f"Successfully audited {filename} with status: {status}", "success")
            return render_template('result.html', 
                                 filename=filename, 
                                 doc_type=doc_type,
                                 fields=extracted_fields,
                                 compliance=compliance_results,
                                 anomalies=anomalies)

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