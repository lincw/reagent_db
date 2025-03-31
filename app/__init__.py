from flask import Flask
import os
import sys

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_db_path, load_config

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'reagent_db_secret_key'  # For flash messages

# Get database path from configuration
DB_PATH = get_db_path()

# Get app base directory
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create uploads directory
UPLOAD_FOLDER = os.path.join(current_dir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        print(f"Created upload directory at {UPLOAD_FOLDER}")
    except Exception as e:
        print(f"Error creating upload directory: {str(e)}")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
print(f"Upload folder set to: {UPLOAD_FOLDER}")

# Make sure uploads directory is writable
try:
    test_file = os.path.join(UPLOAD_FOLDER, 'test_write.txt')
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print("Upload directory is writable")
except Exception as e:
    print(f"WARNING: Upload directory may not be writable: {str(e)}")

# Exports directory
EXPORTS_FOLDER = os.path.join(current_dir, 'exports')
if not os.path.exists(EXPORTS_FOLDER):
    os.makedirs(EXPORTS_FOLDER)

# Import routes after app is created to avoid circular imports
from app.routes import *
