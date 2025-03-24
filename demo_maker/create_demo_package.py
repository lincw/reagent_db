#!/usr/bin/env python3
"""
Script to create a fully self-contained demo package of the Reagent Database application
that includes sample data and can be run anywhere with Python installed.
"""

import os
import sys
import shutil
import sqlite3
import json
from pathlib import Path
import datetime

def create_demo_package():
    print("Creating portable demo package...")
    
    # Get the base directory of the application
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Create a demo directory
    demo_dir = os.path.join(base_dir, "ReagentDB_Demo")
    if os.path.exists(demo_dir):
        shutil.rmtree(demo_dir)
    os.makedirs(demo_dir)
    
    # Files and directories to copy
    to_copy = [
        "app",
        "templates",
        "config.py",
        "run.py",
        "setup_db.py"
    ]
    
    # Copy necessary files
    for item in to_copy:
        src = os.path.join(base_dir, item)
        dst = os.path.join(demo_dir, item)
        
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    
    # Create empty directories
    for directory in ["uploads", "exports"]:
        os.makedirs(os.path.join(demo_dir, directory), exist_ok=True)
    
    # Create app_config.json with local storage
    config_content = '''{
    "db_path": "reagent_db.sqlite",
    "use_onedrive": false,
    "onedrive_path": "",
    "debug": true,
    "port": 5000
}'''
    with open(os.path.join(demo_dir, "app_config.json"), 'w') as f:
        f.write(config_content)
    
    # Create sample database with demo data
    create_sample_database(demo_dir)
    
    # Create demo launch scripts
    create_demo_scripts(demo_dir)
    
    # Create README
    create_demo_readme(demo_dir)
    
    print(f"Demo package created at: {demo_dir}")
    print("You can share this folder with colleagues. They only need Python 3.6+ installed to run it.")

def create_sample_database(demo_dir):
    """Create a sample database with demo data"""
    db_path = os.path.join(demo_dir, "reagent_db.sqlite")
    
    # Initialize database schema
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create tables
    c.execute('''
    CREATE TABLE organisms (
        organism_id INTEGER PRIMARY KEY,
        organism_name TEXT NOT NULL,
        organism_genus TEXT,
        organism_species TEXT,
        organism_strain TEXT,
        organism_description TEXT,
        organism_source TEXT,
        organism_growth TEXT,
        organism_comments TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE orf_sequence (
        orf_id INTEGER PRIMARY KEY,
        orf_name TEXT NOT NULL,
        orf_annotation TEXT,
        orf_sequence TEXT,
        orf_length_bp INTEGER,
        orf_organism_id INTEGER,
        orf_function TEXT,
        orf_comments TEXT,
        FOREIGN KEY (orf_organism_id) REFERENCES organisms(organism_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE plasmid (
        plasmid_id INTEGER PRIMARY KEY,
        plasmid_name TEXT NOT NULL,
        plasmid_type TEXT,
        plasmid_description TEXT,
        plasmid_selection TEXT,
        plasmid_express_organism TEXT,
        plasmid_source TEXT,
        plasmid_comments TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE freezer (
        freezer_id INTEGER PRIMARY KEY,
        freezer_location TEXT NOT NULL,
        freezer_temp INTEGER,
        freezer_description TEXT,
        freezer_responsible TEXT,
        freezer_comments TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE orf_position (
        position_id INTEGER PRIMARY KEY,
        orf_id INTEGER,
        plasmid_id INTEGER,
        freezer_id INTEGER,
        plate TEXT NOT NULL,
        well TEXT NOT NULL,
        date_added TEXT,
        comments TEXT,
        FOREIGN KEY (orf_id) REFERENCES orf_sequence(orf_id),
        FOREIGN KEY (plasmid_id) REFERENCES plasmid(plasmid_id),
        FOREIGN KEY (freezer_id) REFERENCES freezer(freezer_id)
    )
    ''')
    
    # Insert sample data - Organisms
    organisms = [
        (1, "E. coli", "Escherichia", "coli", "DH5α", "Common lab strain for cloning", "Lab stock", "LB media, 37°C", "Standard cloning strain"),
        (2, "S. cerevisiae", "Saccharomyces", "cerevisiae", "BY4741", "Standard yeast lab strain", "ATCC", "YPD media, 30°C", "Commonly used for protein expression"),
        (3, "A. thaliana", "Arabidopsis", "thaliana", "Col-0", "Model plant organism", "ABRC", "MS media, 22°C, long day", "Standard wild-type ecotype")
    ]
    
    c.executemany('''
    INSERT INTO organisms (organism_id, organism_name, organism_genus, organism_species, organism_strain, 
                          organism_description, organism_source, organism_growth, organism_comments)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', organisms)
    
    # Insert sample data - ORFs
    orfs = [
        (1, "ORF001", "Hypothetical protein", "ATGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGC", 36, 1, "Unknown function", "Identified in genomic screen"),
        (2, "ORF002", "Heat shock protein", "ATGGCATGCATGCATGCATGCATGCATGCATGCATGC", 36, 1, "Stress response", "Upregulated under heat stress"),
        (3, "GFP", "Green fluorescent protein", "ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGG", 33, 2, "Fluorescent reporter", "Commonly used reporter gene"),
        (4, "RFP", "Red fluorescent protein", "ATGGCCTCCTCCGAGGACGTCATCAAGGAGTTC", 33, 2, "Fluorescent reporter", "Red variant reporter gene"),
        (5, "ORF005", "DNA binding protein", "ATGGCGGCAGCATCGGCATCAGCAGCAGGCGGC", 33, 3, "Transcription factor", "Binds to promoter regions"),
        (6, "ORF006", "Membrane transporter", "ATGGCTGCTGCTGCTGCTGCTGCTGCTGCTGCT", 33, 3, "Transport", "Localized to plasma membrane")
    ]
    
    c.executemany('''
    INSERT INTO orf_sequence (orf_id, orf_name, orf_annotation, orf_sequence, orf_length_bp, 
                             orf_organism_id, orf_function, orf_comments)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', orfs)
    
    # Insert sample data - Plasmids
    plasmids = [
        (1, "pUC19-Amp", "Cloning vector", "Standard cloning vector with ampicillin resistance", "Ampicillin", "E. coli", "Lab stock", "High copy number"),
        (2, "pET28a-Kan", "Expression vector", "T7 promoter expression vector", "Kanamycin", "E. coli", "Novagen", "Adds N-terminal His tag"),
        (3, "pYES2-Ura", "Yeast expression vector", "Galactose-inducible expression in yeast", "URA3", "S. cerevisiae", "Invitrogen", "2 micron origin"),
        (4, "pCambia1301", "Plant transformation vector", "Plant binary vector for Agrobacterium-mediated transformation", "Hygromycin", "A. thaliana", "Cambia", "Contains GUS reporter"),
        (5, "pGEX-GST", "GST fusion vector", "Expresses proteins with GST tag", "Ampicillin", "E. coli", "GE Healthcare", "IPTG inducible")
    ]
    
    c.executemany('''
    INSERT INTO plasmid (plasmid_id, plasmid_name, plasmid_type, plasmid_description, plasmid_selection,
                        plasmid_express_organism, plasmid_source, plasmid_comments)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', plasmids)
    
    # Insert sample data - Freezers
    freezers = [
        (1, "Lab 20, -80°C", -80, "Main lab freezer", "Dr. Smith", "Contains most bacterial stocks"),
        (2, "Lab 20, -20°C", -20, "Everyday freezer", "Lab Manager", "For frequent use items"),
        (3, "Cold Room, 4°C", 4, "Cold room storage", "Lab Manager", "For short-term storage")
    ]
    
    c.executemany('''
    INSERT INTO freezer (freezer_id, freezer_location, freezer_temp, freezer_description,
                        freezer_responsible, freezer_comments)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', freezers)
    
    # Insert sample data - Positions
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    positions = [
        (1, 1, 1, 1, "P01", "A1", today, "Original stock"),
        (2, 2, 1, 1, "P01", "A2", today, "Original stock"),
        (3, 3, 2, 1, "P02", "B1", today, "Expression ready"),
        (4, 4, 2, 1, "P02", "B2", today, "Expression ready"),
        (5, 5, 3, 2, "P03", "C1", today, "Fresh transformation"),
        (6, 6, 4, 2, "P03", "C2", today, "Fresh transformation"),
        (7, 1, 5, 3, "P04", "D1", today, "Backup copy"),
        (8, 2, 5, 3, "P04", "D2", today, "Backup copy")
    ]
    
    c.executemany('''
    INSERT INTO orf_position (position_id, orf_id, plasmid_id, freezer_id, plate, well,
                             date_added, comments)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', positions)
    
    conn.commit()
    conn.close()
    
    print(f"Sample database created at {db_path}")

def create_demo_scripts(demo_dir):
    """Create launch scripts for the demo"""
    # Windows batch file
    bat_content = '''@echo off
echo Starting Reagent Database Demo...

rem Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.6+ and try again
    pause
    exit /b 1
)

rem Install required packages
echo Installing required packages...
python -m pip install flask

rem Run the application
echo Starting application...
python run.py

pause
'''
    
    with open(os.path.join(demo_dir, "run_demo.bat"), 'w') as f:
        f.write(bat_content)
    
    # macOS/Linux shell script
    sh_content = '''#!/bin/bash
echo "Starting Reagent Database Demo..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH"
    echo "Please install Python 3.6+ and try again"
    exit 1
fi

# Install required packages
echo "Installing required packages..."
python3 -m pip install flask

# Run the application
echo "Starting application..."
python3 run.py
'''
    
    sh_path = os.path.join(demo_dir, "run_demo.sh")
    with open(sh_path, 'w') as f:
        f.write(sh_content)
    
    # Make the shell script executable
    try:
        os.chmod(sh_path, 0o755)
    except:
        print("Could not make shell script executable - user may need to do this manually")

def create_demo_readme(demo_dir):
    """Create a README file for the demo package"""
    readme_content = '''# Reagent Database Demo

This is a self-contained demo of the Reagent Database application with sample data included.

## Running the Demo

### On Windows:
1. Make sure you have Python 3.6 or higher installed
2. Double-click `run_demo.bat`
3. The script will install required packages and start the application

### On macOS or Linux:
1. Make sure you have Python 3.6 or higher installed
2. Open Terminal in this directory
3. Run: `chmod +x run_demo.sh` (to make the script executable)
4. Run: `./run_demo.sh`
5. The script will install required packages and start the application

## Accessing the Application

Once running, open your web browser and go to:
```
http://localhost:5000
```

## Sample Data Included

This demo comes with pre-populated sample data:

* **Organisms**: E. coli, S. cerevisiae, A. thaliana
* **ORFs**: Various genes and fluorescent proteins
* **Plasmids**: Common cloning and expression vectors
* **Freezers**: Sample storage locations

## Demo Search Examples

Try these sample searches:

* Search for Gene/ORF: "GFP" or "ORF00"
* Search for Plasmid: "pUC19" or "pET28a"
* Search for Location: "P01" or "A1"
* Search for Organism: "E. coli" or "thaliana"

## Features to Explore

1. Search for any item and click on the results to view detailed information
2. Navigate between related items using the links in detail pages
3. Try adding new entries
4. Export the database

## Limitations of the Demo

* Data is stored locally and will persist between sessions on the same computer
* Some features may be limited compared to the full application

## For Full Deployment

Contact the development team for information on deploying the full application with:
* Multi-user access
* Cloud database storage
* Advanced features
'''
    
    with open(os.path.join(demo_dir, "README.md"), 'w') as f:
        f.write(readme_content)

if __name__ == "__main__":
    create_demo_package()
