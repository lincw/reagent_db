"""
A simple script to check database connectivity and verify table contents
"""

import sqlite3
import os
import sys
from config import get_db_path

def check_database():
    # Get the database path from configuration
    DB_PATH = get_db_path()
    
    print(f"Checking database at: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file does not exist at {DB_PATH}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        print("Successfully connected to database")
        
        # Get list of tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"Database contains {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"  - {table_name}: {row_count} rows")
        
        # Check specific tables important for the database summary
        important_tables = ['orf_sequence', 'plasmid', 'organisms', 'freezer', 'orf_position']
        for table in important_tables:
            if (table,) in tables:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"\nTable {table} has {len(columns)} columns: {', '.join(column_names)}")
                
                # Get a sample row
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    print(f"Sample row from {table}:")
                    for i, col in enumerate(columns):
                        col_name = col[1]
                        value = sample[i]
                        print(f"  {col_name}: {value}")
                else:
                    print(f"No data in {table}")
            else:
                print(f"\nIMPORTANT: Table {table} is missing from the database!")
        
        # Close the connection
        conn.close()
        print("\nDatabase check completed successfully")
        return True
        
    except Exception as e:
        print(f"ERROR during database check: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_database()
