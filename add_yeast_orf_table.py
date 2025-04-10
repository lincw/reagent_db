"""
Migration script to add yeast_orf_position table to the Reagent Database
"""

import sqlite3
from config import get_db_path

def add_yeast_orf_table():
    # Get the database path from configuration
    DB_PATH = get_db_path()
    
    print(f'Updating database at {DB_PATH}')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if table already exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
    if c.fetchone() is None:
        # Create new yeast_orf_position table
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
        print('yeast_orf_position table created successfully')
    else:
        print('yeast_orf_position table already exists')
    
    conn.close()
    return True

if __name__ == "__main__":
    add_yeast_orf_table()
