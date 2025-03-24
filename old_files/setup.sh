#!/bin/bash

# This script sets up the Reagent Database application with sample data

# Make the run script executable
chmod +x run.sh

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database directly instead of starting the app
echo "Initializing database..."
python -c "
import os
import sqlite3
from app import init_db, DB_PATH

# Make sure the database exists and tables are created
if not os.path.exists(DB_PATH):
    print(f'Creating database at {DB_PATH}')
    init_db()
else:
    print(f'Database already exists at {DB_PATH}')
"

# Insert sample data
echo "Inserting sample data..."
python insert_sample_data.py

echo "Setup complete! Run ./run.sh to start the application."
