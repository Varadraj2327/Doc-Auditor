import os
import json
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, flash, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extractor import extract_text_from_pdf
from validator import extract_fields, validate_fields

# Configure Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minimal-saas-doc-auditor-super-secret'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
DATABASE = os.path.join(BASE_DIR, 'database.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                details_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        db.commit()

# Require Login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

# Routes
@app.route('/')
def index():
    if getattr(g, 'user', None):
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        
        flash("Invalid username or password.", "error")
    return render_template('login.html', is_signup=False)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                       (username, generate_password_hash(password)))
            db.commit()
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")
    return render_template('login.html', is_signup=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    total = db.execute('SELECT COUNT(*) as c FROM documents WHERE user_id = ?', (g.user['id'],)).fetchone()['c']
    passed = db.execute('SELECT COUNT(*) as c FROM documents WHERE user_id = ? AND status = ?', (g.user['id'], 'PASS')).fetchone()['c']
    failed = db.execute('SELECT COUNT(*) as c FROM documents WHERE user_id = ? AND status = ?', (g.user['id'], 'FAIL')).fetchone()['c']
    recent = db.execute('SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', (g.user['id'],)).fetchall()
    
    return render_template('dashboard.html', total=total, passed=passed, failed=failed, recent=recent)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('No file part submitted.', 'error')
            return redirect(url_for('upload'))
        
        file = request.files['pdf_file']
        if file.filename == '':
            flash('No selected file.', 'error')
            return redirect(url_for('upload'))
        
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                text = extract_text_from_pdf(filepath)
                fields = extract_fields(text)
                validation = validate_fields(fields)
                
                # Save to database
                db = get_db()
                details = json.dumps({
                    'fields': fields,
                    'checks': validation.checks,
                    'reasons': validation.reasons
                })
                cursor = db.execute(
                    'INSERT INTO documents (user_id, filename, status, details_json) VALUES (?, ?, ?, ?)',
                    (g.user['id'], filename, validation.status, details)
                )
                db.commit()
                doc_id = cursor.lastrowid
                return redirect(url_for('result', doc_id=doc_id))
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(url_for('upload'))
        else:
            flash('Invalid file. Only PDFs are allowed.', 'error')
            
    return render_template('upload.html')

@app.route('/result/<int:doc_id>')
@login_required
def result(doc_id):
    db = get_db()
    doc = db.execute('SELECT * FROM documents WHERE id = ? AND user_id = ?', (doc_id, g.user['id'])).fetchone()
    if not doc:
        flash("Result not found.", "error")
        return redirect(url_for('dashboard'))
    
    details = json.loads(doc['details_json'])
    return render_template('result.html', doc=doc, details=details)

@app.route('/history')
@login_required
def history():
    q = request.args.get('q', '')
    status_filter = request.args.get('status', 'ALL')
    
    query = 'SELECT * FROM documents WHERE user_id = ?'
    params = [g.user['id']]
    
    if q:
        query += ' AND filename LIKE ?'
        params.append(f'%{q}%')
    if status_filter in ('PASS', 'FAIL'):
        query += ' AND status = ?'
        params.append(status_filter)
        
    query += ' ORDER BY created_at DESC'
    
    db = get_db()
    documents = db.execute(query, params).fetchall()
    
    return render_template('history.html', documents=documents, q=q, status_filter=status_filter)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
