from flask import render_template, abort
import os
from app import app, DB_PATH

@app.route('/')
def index():
    # First, check if the database exists
    if not os.path.exists(DB_PATH):
        app.logger.warning(f"Database not found at {DB_PATH}. Using default template.")
    
    return render_template('index.html')
