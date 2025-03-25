#!/usr/bin/env python3
"""
Database reset script for the Reagent Database application
This script:
1. Makes a backup of the existing database (if it exists)
2. Creates a fresh database with the correct schema
3. Inserts sample data for testing
"""

import os
import shutil
import sqlite3
import sys
from datetime import datetime
import setup_db
import insert_sample_data
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

def reset_database():
    """Reset the database to a clean state with sample data"""
    DB_PATH = get_db_path()
    
    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        print(f"Removing existing database at: {DB_PATH}")
        os.remove(DB_PATH)
    
    # Create new database with schema
    print("Creating new database...")
    setup_db.init_db()
    
    # Insert sample data
    print("Inserting sample data...")
    insert_sample_data.insert_sample_data()
    
    return True

def main():
    """Run the database reset process"""
    print("\n===== REAGENT DATABASE RESET TOOL =====\n")
    
    # Confirm with user
    print("This will reset the database to a clean state with sample data.")
    print("A backup of the existing database will be created if it exists.")
    confirm = input("Continue? (y/N): ")
    
    if confirm.lower() != 'y':
        print("Database reset cancelled")
        return
    
    # Backup existing database
    backup_database()
    
    # Reset database
    if reset_database():
        print("\nDatabase reset completed successfully!")
        print("The database now contains fresh sample data.")
        print("You can now run the application with 'python run.py'")
    else:
        print("\nError resetting database")

if __name__ == "__main__":
    main()
