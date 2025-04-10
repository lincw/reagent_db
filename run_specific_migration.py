"""
Run a specific migration script directly to ensure it's executed properly
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add parent directory to path so we can import config
from config import get_db_path

def run_yeast_position_migration():
    # Get the database path from configuration
    DB_PATH = get_db_path()
    
    if not os.path.exists(DB_PATH):
        print(f'Error: Database does not exist at {DB_PATH}')
        return False
    
    print(f'Migrating database at {DB_PATH}')
    
    # Create a backup of the database
    backup_path = os.path.join(
        os.path.dirname(DB_PATH),
        f'db_backups/reagent_db_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sqlite'
    )
    
    # Ensure the backup directory exists
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    # Copy the database file
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f'Created backup at {backup_path}')
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Start a transaction
        c.execute('BEGIN TRANSACTION')
        
        # Check if the yeast_orf_position table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
        if not c.fetchone():
            print("Creating new yeast_orf_position table with position_type column")
            c.execute('''
            CREATE TABLE yeast_orf_position (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                orf_id TEXT,
                plate TEXT,
                well TEXT,
                position_type TEXT DEFAULT 'AD',
                FOREIGN KEY (orf_id) REFERENCES orf_sequence (orf_id)
            )
            ''')
        else:
            # Check if the position_type column already exists
            c.execute("PRAGMA table_info(yeast_orf_position)")
            columns = [column[1] for column in c.fetchall()]
            
            if 'position_type' not in columns:
                print("Adding position_type column to yeast_orf_position table")
                # Add position_type column with default value 'AD' for existing records
                c.execute('ALTER TABLE yeast_orf_position ADD COLUMN position_type TEXT DEFAULT "AD"')
            else:
                print("position_type column already exists in yeast_orf_position table")
                
        # Commit the transaction
        c.execute('COMMIT')
        
        print('Migration completed successfully')
        return True
        
    except Exception as e:
        # If anything goes wrong, roll back the transaction
        c.execute('ROLLBACK')
        print(f'Error during migration: {str(e)}')
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Close the database connection
        conn.close()

if __name__ == "__main__":
    success = run_yeast_position_migration()
    if success:
        print('Migration completed successfully!')
    else:
        print('Migration failed!')
