#!/usr/bin/env python3
"""
Database cleanup script for the Reagent Database application
This script:
1. Makes a backup of the existing database (if it exists)
2. Creates a fresh, empty database with the correct schema
"""

import os
import shutil
import sqlite3
import sys
from datetime import datetime
import setup_db
from config import get_db_path

def backup_database():
    """Create a backup of the existing database"""
    DB_PATH = get_db_path()
    
    if os.path.exists(DB_PATH):
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(DB_PATH), 'db_backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create a backup file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'reagent_db_backup_{timestamp}.sqlite')
        
        print(f"Creating backup at: {backup_path}")
        shutil.copy2(DB_PATH, backup_path)
        return True
    else:
        print("No existing database found to backup")
        return False

def clean_database():
    """Reset the database to a clean, empty state"""
    DB_PATH = get_db_path()
    
    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        print(f"Removing existing database at: {DB_PATH}")
        os.remove(DB_PATH)
    
    # Create new database with schema
    print("Creating new empty database...")
    setup_db.init_db()
    
    # Verify that the database exists and is empty
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ["freezer", "organisms", "plasmid", "orf_sequence", "orf_position"]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Table '{table}' has {count} records (should be 0)")
    
    conn.close()
    return True

def main():
    """Run the database cleanup process"""
    print("\n===== REAGENT DATABASE CLEANUP TOOL =====\n")
    
    # Confirm with user
    print("This will reset the database to a clean, empty state.")
    print("A backup of the existing database will be created.")
    confirm = input("Continue? (y/N): ")
    
    if confirm.lower() != 'y':
        print("Database cleanup cancelled")
        return
    
    # Backup existing database
    backup_database()
    
    # Clean database
    if clean_database():
        print("\nDatabase cleanup completed successfully!")
        print("The database is now empty and ready for importing data.")
        print("You can now run the application with 'python run.py'")
    else:
        print("\nError cleaning database")

if __name__ == "__main__":
    main()
