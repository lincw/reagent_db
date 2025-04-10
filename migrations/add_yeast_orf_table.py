"""
Migration script to add yeast_orf_position table to the existing database
"""

import sqlite3
from config import get_db_path

def migrate():
    # Get the database path from configuration
    DB_PATH = get_db_path()
    
    print(f'Migrating database at {DB_PATH}')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if yeast_orf_position table already exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
    if c.fetchone():
        print('Table yeast_orf_position already exists. Skipping migration.')
        conn.close()
        return False
    
    # Create the new yeast_orf_position table
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
    conn.close()
    print('Migration completed successfully - yeast_orf_position table created')
    return True

if __name__ == "__main__":
    migrate()
