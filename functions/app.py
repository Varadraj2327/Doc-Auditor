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