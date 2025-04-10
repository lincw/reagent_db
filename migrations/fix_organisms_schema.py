"""
Migration script to fix the organisms table schema by adding an orf_id field
and correcting the relationship with the orf_sequence table.
"""

import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_db_path

def migrate():
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
        
        # Check if the organisms table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organisms'")
        if not c.fetchone():
            print("Error: organisms table does not exist")
            c.execute('ROLLBACK')
            return False
        
        # Rename the existing organisms table
        c.execute('ALTER TABLE organisms RENAME TO organisms_old')
        
        # Create a new organisms table with the correct schema
        c.execute('''
        CREATE TABLE organisms (
            organism_id TEXT PRIMARY KEY,
            organism_name TEXT,
            organism_genus TEXT,
            organism_species TEXT,
            organism_strain TEXT,
            orf_id TEXT,
            FOREIGN KEY (orf_id) REFERENCES orf_sequence (orf_id)
        )
        ''')
        
        # Copy data from the old table to the new one, setting orf_id to NULL initially
        c.execute('''
        INSERT INTO organisms (organism_id, organism_name, organism_genus, organism_species, organism_strain, orf_id)
        SELECT organism_id, organism_name, organism_genus, organism_species, organism_strain, NULL
        FROM organisms_old
        ''')
        
        # Create an index on orf_id for better performance
        c.execute('CREATE INDEX idx_organisms_orf_id ON organisms(orf_id)')
        
        # Update all orf_id values where we can find a matching organism_id in orf_sequence
        c.execute('''
        UPDATE organisms
        SET orf_id = (
            SELECT orf_id 
            FROM orf_sequence 
            WHERE orf_sequence.orf_organism_id = organisms.organism_id
            LIMIT 1
        )
        ''')
        
        # Drop the old table
        c.execute('DROP TABLE organisms_old')
        
        # Commit the transaction
        c.execute('COMMIT')
        
        print('Migration completed successfully')
        print('Added orf_id field to organisms table')
        
        # Count how many organisms have an orf_id set
        c.execute('SELECT COUNT(*) FROM organisms WHERE orf_id IS NOT NULL')
        with_orf_id = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM organisms')
        total = c.fetchone()[0]
        
        print(f'Updated {with_orf_id} out of {total} organisms with orf_id values')
        
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
    success = migrate()
    if success:
        print('Migration completed successfully!')
    else:
        print('Migration failed!')
