#!/bin/bash

# Run the updated insert_sample_data.py script to load toy examples
echo "Loading toy examples into the database..."
python insert_sample_data.py

echo "Toy examples loaded successfully!"
echo "Run ./run.sh to start the application and explore the examples."
