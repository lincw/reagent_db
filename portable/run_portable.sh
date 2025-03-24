#!/bin/bash

echo "Starting Experimental Results Sharing Tool..."
echo "Database will be stored on OneDrive if available"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH"
    echo "Please install Python 3.6+ and try again"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed or not in PATH"
    echo "Please install pip3 and try again"
    exit 1
fi

# Check if requirements are installed
echo "Checking requirements..."
pip3 install -r requirements.txt

# Run the application
echo "Starting application..."
cd ..
python3 run.py

