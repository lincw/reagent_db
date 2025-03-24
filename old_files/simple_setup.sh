#!/bin/bash

# This script sets up the simplified Reagent Database application with sample data

# Make the run script executable
chmod +x run.sh

# Install dependencies (minimal requirements)
echo "Installing dependencies..."
pip install flask

# Create the database directly
echo "Creating database..."
python -c "
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'reagent_db.sqlite')

if not os.path.exists(DB_PATH):
    print(f'Creating database at {DB_PATH}')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create tables
    c.execute('''
    CREATE TABLE freezer (
        freezer_id TEXT PRIMARY KEY,
        freezer_location TEXT,
        freezer_condition TEXT,
        freezer_date TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE organisms (
        organism_id TEXT PRIMARY KEY,
        organism_name TEXT,
        organism_genus TEXT,
        organism_species TEXT,
        organism_strain TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE plasmid (
        plasmid_id TEXT PRIMARY KEY,
        plasmid_name TEXT,
        plasmid_type TEXT,
        plasmid_express_organism TEXT,
        plasmid_description TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE orf_sequence (
        orf_id TEXT PRIMARY KEY,
        orf_name TEXT,
        orf_annotation TEXT,
        orf_sequence TEXT,
        orf_with_stop INTEGER,
        orf_open INTEGER,
        orf_organism_id TEXT,
        orf_length_bp INTEGER,
        orf_entrez_id TEXT,
        orf_ensembl_id TEXT,
        orf_uniprot_id TEXT,
        orf_ref_url TEXT,
        FOREIGN KEY (orf_organism_id) REFERENCES organisms (organism_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE orf_position (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orf_id TEXT,
        plate TEXT,
        well TEXT,
        freezer_id TEXT,
        plasmid_id TEXT,
        orf_create_date TEXT,
        FOREIGN KEY (orf_id) REFERENCES orf_sequence (orf_id),
        FOREIGN KEY (freezer_id) REFERENCES freezer (freezer_id),
        FOREIGN KEY (plasmid_id) REFERENCES plasmid (plasmid_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print('Database schema created successfully')
else:
    print(f'Database already exists at {DB_PATH}')
"

# Insert sample data
echo "Inserting sample data..."
python insert_sample_data.py

# Create results directory if it doesn't exist
RESULTS_DIR=$(dirname $(dirname $(dirname $(pwd))))/results
if [ ! -d "$RESULTS_DIR" ]; then
    echo "Creating results directory..."
    mkdir -p "$RESULTS_DIR"
fi

echo "Setup complete! Run ./run.sh to start the application."
