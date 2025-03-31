#!/usr/bin/env python3
"""
Debug launcher for the Reagent Database Application
This script runs the app with extra debugging enabled
"""

import sys
import os
import logging
from app import app, DB_PATH
from flask.cli import show_server_banner

def setup_debugging():
    """Configure extensive debugging"""
    # Set up console logging
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    
    # Add the handler to the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console)
    
    # Set up Flask and Werkzeug loggers
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)
    logging.getLogger('flask').setLevel(logging.DEBUG)
    
    # Set Flask debug config
    app.config['DEBUG'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Suppress the ASCII art banner
    show_server_banner = lambda *args, **kwargs: None
    
    logging.info("Debug mode enabled with verbose logging")

def print_app_info():
    """Print application configuration info"""
    print("\n" + "="*70)
    print("REAGENT DATABASE - DEBUG MODE")
    print("="*70)
    print(f"Database path: {DB_PATH}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Static folder: {app.static_folder}")
    print(f"Template folder: {app.template_folder}")
    print(f"Port: 5000")
    print(f"Debug: {app.debug}")
    
    # Check if database exists
    if os.path.exists(DB_PATH):
        print(f"Database size: {os.path.getsize(DB_PATH) / 1024:.2f} KB")
    else:
        print("WARNING: Database file not found!")
    
    # Check uploads and exports directories
    uploads_dir = app.config['UPLOAD_FOLDER']
    if os.path.exists(uploads_dir) and os.access(uploads_dir, os.W_OK):
        print("Uploads directory: OK (writable)")
    else:
        print("WARNING: Uploads directory is not writable!")
    
    exports_dir = os.path.join(os.path.dirname(uploads_dir), 'exports')
    if os.path.exists(exports_dir) and os.access(exports_dir, os.W_OK):
        print("Exports directory: OK (writable)")
    else:
        print("WARNING: Exports directory is not writable!")
    
    print("\nAccess the application at: http://127.0.0.1:5000")
    print("="*70)

if __name__ == '__main__':
    # Set up debugging
    setup_debugging()
    
    # Print application info
    print_app_info()
    
    # Run the application
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=True)
