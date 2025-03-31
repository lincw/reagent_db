from app import app
import os
import webbrowser
import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(console_level=logging.ERROR):
    """Set up logging to file while suppressing console output"""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create a formatted log filename with date
    log_filename = os.path.join(logs_dir, f'reagent_db_{datetime.now().strftime("%Y-%m-%d")}.log')
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]: 
        root_logger.removeHandler(handler)
    
    # File handler with rotation (max 5MB, keep 5 backup files)
    file_handler = RotatingFileHandler(log_filename, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler with minimal output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)  # Only show errors in console
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Set Werkzeug logger to use these handlers
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.propagate = True
    
    return log_filename

def print_banner(log_file):
    print("\n" + "=" * 60)
    print("Reagent Database Application")
    print("=" * 60)
    print("Starting server at http://127.0.0.1:5000")
    print("Press CTRL+C to stop the server")
    print(f"Logs are being saved to: {log_file}")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    # Setup logging to file
    log_file = setup_logging()
    
    # Print banner with app information
    print_banner(log_file)
    
    # Log the start of the application
    logging.info("Application starting")
    
    # Run the app with minimal console output
    app.run(debug=True, use_reloader=True)
