#!/bin/bash

# This script sets up the Reagent Database application

# Make run script executable
chmod +x run.sh

# Install dependencies
echo "Installing dependencies..."
pip install flask pandas openpyxl

# Initialize database and load sample data
echo "Setting up database..."
python setup_db.py

echo "Loading sample data..."
python insert_sample_data.py

echo "Setup complete! Run ./run.sh to start the application."
