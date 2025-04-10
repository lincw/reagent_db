"""
Migration script to add the orf_sources table to an existing database.
"""

import sqlite3
import os
import sys

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_db_path

def run_migration():
    # Get the database path from configuration
    DB_PATH = get_db_path()
    
    if not os.path.exists(DB_PATH):
        print(f'Database does not exist at {DB_PATH}. Run setup_db.py first.')
        return False
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if orf_sources table already exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orf_sources'")
    if c.fetchone():
        print('ORF sources table already exists, no migration needed.')
        conn.close()
        return True
    
    # Create the orf_sources table
    try:
        c.execute('''
        CREATE TABLE orf_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orf_id TEXT,
            source_name TEXT,
            source_details TEXT,
            source_url TEXT,
            submission_date TEXT,
            submitter TEXT,
            notes TEXT,
            FOREIGN KEY (orf_id) REFERENCES orf_sequence (orf_id)
        )
        ''')
        
        conn.commit()
        print('ORF sources table added successfully.')
        
        # Make sure directory for CSV template exists
        csv_template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'csv_templates')
        if not os.path.exists(csv_template_dir):
            os.makedirs(csv_template_dir)
        
        # Create a template CSV file for ORF sources
        template_path = os.path.join(csv_template_dir, 'orf_sources.csv')
        if not os.path.exists(template_path):
            with open(template_path, 'w') as f:
                f.write("orf_id,source_name,source_details,source_url,submission_date,submitter,notes\n")
                f.write("ORF001,Commercial Vendor,Purchased from Vendor XYZ,https://vendor-xyz.com/orf001,2023-05-15,Jane Doe,Verified sequence matches published reference\n")
                f.write("ORF002,Academic Lab,Gift from Smith Lab,https://smith-lab.edu/plasmids,2023-06-20,John Smith,Original construct published in J. Biol. Chem. 2022\n")
            print(f'Created template CSV file at {template_path}')
        
        return True
    except Exception as e:
        conn.rollback()
        print(f'Error creating ORF sources table: {str(e)}')
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if run_migration():
        print('Migration completed successfully.')
    else:
        print('Migration failed.')
