"""
Migration script to add the yeast_orf_position table to an existing database.
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
    
    # Check if yeast_orf_position table already exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
    if c.fetchone():
        print('Yeast ORF position table already exists, no migration needed.')
        conn.close()
        return True
    
    # Create the yeast_orf_position table
    try:
        c.execute('''
        CREATE TABLE yeast_orf_position (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orf_id TEXT,
            plate TEXT,
            well TEXT,
            FOREIGN KEY (orf_id) REFERENCES orf_sequence (orf_id)
        )
        ''')
        
        conn.commit()
        print('Yeast ORF position table added successfully.')
        
        # Make sure directory for CSV template exists
        csv_template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'csv_templates')
        if not os.path.exists(csv_template_dir):
            os.makedirs(csv_template_dir)
        
        # Create a template CSV file for yeast ORF positions
        template_path = os.path.join(csv_template_dir, 'yeast_orf_positions.csv')
        if not os.path.exists(template_path):
            with open(template_path, 'w') as f:
                f.write("orf_id,plate,well\n")
                f.write("ORF001,Yeast Plate A,Y1\n")
                f.write("ORF002,Yeast Plate B,Y5\n")
            print(f'Created template CSV file at {template_path}')
        
        return True
    except Exception as e:
        conn.rollback()
        print(f'Error creating yeast ORF position table: {str(e)}')
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if run_migration():
        print('Migration completed successfully.')
    else:
        print('Migration failed.')
