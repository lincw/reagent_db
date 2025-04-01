#!/usr/bin/env python3
"""
Check the organisms in the database
"""

import sqlite3
from config import get_db_path

def check_organisms():
    """Check the organisms in the database"""
    DB_PATH = get_db_path()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all organisms
    print("All organisms in the database:")
    cursor.execute('SELECT organism_id, organism_name, organism_genus, organism_species, organism_strain FROM organisms')
    organisms = cursor.fetchall()
    for org in organisms:
        print(f"ID: {org[0]}, Name: {org[1]}, Genus: {org[2]}, Species: {org[3]}, Strain: {org[4]}")
    
    # Count total organisms
    cursor.execute('SELECT COUNT(*) FROM organisms')
    total = cursor.fetchone()[0]
    print(f"\nTotal organisms: {total}")
    
    # Count unique organism names
    cursor.execute('SELECT COUNT(DISTINCT organism_name) FROM organisms')
    unique_names = cursor.fetchone()[0]
    print(f"Unique organism names: {unique_names}")
    
    # Count unique genus-species combinations
    cursor.execute('SELECT COUNT(DISTINCT organism_genus || organism_species) FROM organisms')
    unique_species = cursor.fetchone()[0]
    print(f"Unique genus-species combinations: {unique_species}")
    
    conn.close()

if __name__ == "__main__":
    check_organisms()
