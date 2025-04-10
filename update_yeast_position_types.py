"""
Script to update existing yeast positions with appropriate AD/DB types
"""

import sqlite3
import os
import sys
from config import get_db_path

def update_position_types():
    # Get the database path from configuration
    DB_PATH = get_db_path()
    
    if not os.path.exists(DB_PATH):
        print(f'Error: Database does not exist at {DB_PATH}')
        return False
    
    print(f'Updating yeast position types in database: {DB_PATH}')
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Start a transaction
        c.execute('BEGIN TRANSACTION')
        
        # Check if the yeast_orf_position table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
        if not c.fetchone():
            print("Error: yeast_orf_position table does not exist")
            return False
        
        # Check if the position_type column exists
        c.execute("PRAGMA table_info(yeast_orf_position)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'position_type' not in columns:
            print("Error: position_type column does not exist in yeast_orf_position table")
            return False
        
        # Get all yeast positions
        c.execute("SELECT id, orf_id, plate, well FROM yeast_orf_position")
        positions = c.fetchall()
        
        if not positions:
            print("No yeast positions found in the database")
            return False
        
        print(f"Found {len(positions)} yeast positions")
        
        # Split positions to set some as DB
        # We'll designate positions with 'DB' in the plate name as DB
        # and those with odd-numbered IDs as DB (just for demonstration)
        updates_ad = 0
        updates_db = 0
        
        for position in positions:
            id, orf_id, plate, well = position
            
            # Logic to assign position type
            # Example: Plates containing 'DB' in name, or with 'D' wells, or odd IDs
            set_db = False
            
            # Safely check plate name - handle None values
            if plate and isinstance(plate, str) and 'DB' in plate:
                set_db = True
            
            # Safely check well name - handle None values
            elif well and isinstance(well, str) and well.startswith('D'):
                set_db = True
            
            # Use ID as a fallback criterion 
            elif id % 2 == 1:
                set_db = True
            
            # Update the position type
            if set_db:
                c.execute(
                    "UPDATE yeast_orf_position SET position_type = 'DB' WHERE id = ?",
                    (id,)
                )
                updates_db += 1
            else:
                c.execute(
                    "UPDATE yeast_orf_position SET position_type = 'AD' WHERE id = ?",
                    (id,)
                )
                updates_ad += 1
        
        # Get counts of each type after updates
        c.execute("SELECT COUNT(*) FROM yeast_orf_position WHERE position_type = 'AD'")
        ad_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM yeast_orf_position WHERE position_type = 'DB'")
        db_count = c.fetchone()[0]
        
        print(f"Updated {updates_ad} positions to AD type")
        print(f"Updated {updates_db} positions to DB type")
        print(f"Final counts: {ad_count} AD and {db_count} DB positions")
        
        # Commit the transaction
        c.execute('COMMIT')
        
        print("Successfully updated yeast position types")
        return True
        
    except Exception as e:
        # If anything goes wrong, roll back the transaction
        c.execute('ROLLBACK')
        print(f'Error updating position types: {str(e)}')
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Close the database connection
        conn.close()

if __name__ == "__main__":
    success = update_position_types()
    sys.exit(0 if success else 1)
