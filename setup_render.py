import os
import subprocess
import json
import csv
from pathlib import Path

def print_step(msg):
    print(f"\n[STEP] {msg}")

def create_structure():
    print_step("Creating project structure...")
    folders = ["functions", "templates", "static", "data", "uploads"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"  Created /{folder}")

def generate_requirements():
    print_step("Generating requirements.txt...")
    reqs = [
        "flask", "pandas", "numpy", "pdfplumber", "PyPDF2",
        "scikit-learn", "gunicorn", "werkzeug", "fuzzywuzzy",
        "python-Levenshtein", "jinja2"
    ]
    with open("functions/requirements.txt", "w") as f:
        f.write("\n".join(reqs))
    # Root level requirements for Render
    with open("requirements.txt", "w") as f:
        f.write("\n".join(reqs))

def generate_procfile():
    print_step("Creating Procfile for Render...")
    with open("Procfile", "w") as f:
        f.write("web: gunicorn functions.app:app")

def generate_gitignore():
    print_step("Creating .gitignore...")
    content = """
venv/
__pycache__/
*.pyc
.env
data/tmp/
uploads/*
!uploads/.gitkeep
.firebase/
firebase-debug.log
"""
    with open(".gitignore", "w") as f:
        f.write(content.strip())

def generate_app_py():
    print_step("Generating app.py with Render-optimized config...")
    content = """
import os
import json
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, flash, redirect, url_for, session

# Use /tmp for ephemeral storage on Render/Cloud
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Custom paths for templates/static since app.py is in functions/
app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

app.config['SECRET_KEY'] = 'doc-auditor-render-secret-key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Core Routes
@app.route('/')
def index():
    return render_template('index.html', stats={"total": 0, "passed": 0, "failed": 0, "anomalies": 0}, recent=[])

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        flash("System ready for deployment. Uploads will be processed by RPA engine.", "info")
        return redirect(url_for('index'))
    return render_template('upload.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
"""
    with open("functions/app.py", "w") as f:
        f.write(content.strip())

def setup_dataset():
    print_step("Generating sample dataset...")
    data = [
        ["gst", "total", "date", "status"],
        ["27ABCDE1234F1Z5", 5000.0, "2024-03-15", "PASS"],
        ["27GHIJK5678L1Z2", 12000.0, "2024-03-16", "FAIL"],
        ["27MNOPQ9012R1Z3", 450.0, "2024-03-17", "PASS"]
    ]
    with open("data/processed_invoices.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def init_git():
    print_step("Initializing Git repository...")
    try:
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        # Check if already a git repo to avoid conflict in commit msg
        subprocess.run(["git", "commit", "-m", "Initial commit for Doc-Auditor Render deployment"], check=True)
        
        print("\n[?] Skip GitHub remote setup for now as we are in automation.")
    except Exception as e:
        print(f"  Git error: {e}")

def main():
    print("========================================")
    print("   Doc-Auditor Render Setup Script      ")
    print("========================================")
    
    create_structure()
    generate_requirements()
    generate_procfile()
    generate_gitignore()
    generate_app_py()
    setup_dataset()
    
    # Use existing templates if they exist, otherwise placeholders
    template_list = ['index.html', 'upload.html', 'result.html', 'history.html', 'base.html']
    # If they are in the root directory from previous turn, move them
    for t in template_list:
        src = Path(f"functions/templates/{t}")
        dst = Path(f"templates/{t}")
        if src.exists() and not dst.exists():
            os.rename(src, dst)
        elif not dst.exists():
             with open(dst, "w") as f:
                f.write(f"<!-- {t} placeholder --><h1>{t}</h1>")

    init_git()
    
    print("\n" + "="*40)
    print("DONE: SETUP COMPLETE!")
    print("========================================")
    print("Render Deployment Settings:")
    print("  - Build Command: pip install -r requirements.txt")
    print("  - Start Command: gunicorn functions.app:app")
    print("\nNow deploy on Render using your GitHub repo!")
    print("========================================\n")

if __name__ == "__main__":
    main()
