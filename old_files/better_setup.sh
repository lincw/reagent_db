#!/bin/bash

# This script provides a more reliable setup for the Reagent Database application

# Make run script executable
chmod +x run.sh

# Install Flask
echo "Installing Flask..."
pip install flask

# Create database using the Python script
echo "Setting up database..."
python setup_db.py

# Insert sample data
echo "Inserting sample data..."
python insert_sample_data.py

echo "Setup complete! Run ./run.sh to start the application."
