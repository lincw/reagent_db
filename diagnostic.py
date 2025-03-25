#!/usr/bin/env python3
"""
Diagnostic tool for the Reagent Database Application
This script checks the database for issues that might cause OperationalErrors
"""

import os
import sqlite3
import sys
from config import get_db_path, load_config

def print_header(title):
    """Print a section title in a formatted way"""
    print("\n" + "="*70)
    print(" " + title)
    print("="*70)

def check_database_structure():
    """Check the database structure and content"""
    print_header("DATABASE STRUCTURE CHECK")
    
    # Get database path from configuration
    DB_PATH = get_db_path()
    
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file not found at {DB_PATH}")
        print("Please run setup_db.py to create the database.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if tables exist
    print("Checking database tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_names = [table[0] for table in tables]
    
    required_tables = ["freezer", "organisms", "plasmid", "orf_sequence", "orf_position"]
    missing_tables = []
    
    for table in required_tables:
        if table not in table_names:
            missing_tables.append(table)
    
    if missing_tables:
        print(f"ERROR: Missing tables: {', '.join(missing_tables)}")
        return False
    else:
        print("✓ All required tables exist")
    
    # Check data in each table
    for table in required_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Table '{table}' has {count} records")
    
    # Sample ORF data
    print("\nSample ORF data:")
    cursor.execute("SELECT orf_id, orf_name, orf_annotation FROM orf_sequence LIMIT 3")
    orfs = cursor.fetchall()
    for orf in orfs:
        print(f"  ID: {orf[0]}, Name: {orf[1]}, Annotation: {orf[2]}")
    
    return True

def test_detail_views():
    """Test the detail view queries to check for issues"""
    print_header("DETAIL VIEW TEST")
    
    # Get database path from configuration
    DB_PATH = get_db_path()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Use row factory for named columns
    cursor = conn.cursor()
    
    # Get a sample ORF ID
    cursor.execute("SELECT orf_id FROM orf_sequence LIMIT 1")
    result = cursor.fetchone()
    if not result:
        print("No ORF records found in database")
        return False
    
    sample_orf_id = result["orf_id"]
    print(f"Testing detail view with ORF ID: {sample_orf_id}")
    
    # Test the exact SQL query used in the ORF detail view
    try:
        print("Testing ORF detail SQL query...")
        cursor.execute('''
            SELECT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain
            FROM orf_sequence os
            LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            WHERE os.orf_id = ?
        ''', (str(sample_orf_id),))
        
        orf_data = cursor.fetchone()
        if orf_data:
            print(f"✓ ORF detail query successful: found {orf_data['orf_name']}")
        else:
            print(f"ERROR: ORF detail query returned no results for ID {sample_orf_id}")
        
        # Test position query
        print("Testing ORF position SQL query...")
        cursor.execute('''
            SELECT op.*, f.freezer_location, f.freezer_condition, p.plasmid_name, p.plasmid_type
            FROM orf_position op
            LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
            LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
            WHERE op.orf_id = ?
        ''', (str(sample_orf_id),))
        
        positions = cursor.fetchall()
        if positions:
            print(f"✓ ORF position query successful: found {len(positions)} positions")
        else:
            print(f"NOTE: No positions found for ORF {sample_orf_id}")
        
    except Exception as e:
        print(f"ERROR running queries: {str(e)}")
        return False
    
    return True

def verify_data_references():
    """Verify that all foreign key references are valid"""
    print_header("DATA REFERENCE CHECK")
    
    # Get database path from configuration
    DB_PATH = get_db_path()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check orf_position foreign keys
    print("Checking ORF position references...")
    
    # Check orf_id references
    cursor.execute('''
        SELECT op.orf_id
        FROM orf_position op
        LEFT JOIN orf_sequence os ON op.orf_id = os.orf_id
        WHERE os.orf_id IS NULL
    ''')
    invalid_orfs = cursor.fetchall()
    if invalid_orfs:
        print(f"ERROR: Found {len(invalid_orfs)} orf_position records with invalid orf_id references")
    else:
        print("✓ All orf_position.orf_id references are valid")
    
    # Check freezer_id references
    cursor.execute('''
        SELECT op.freezer_id
        FROM orf_position op
        LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
        WHERE op.freezer_id IS NOT NULL AND f.freezer_id IS NULL
    ''')
    invalid_freezers = cursor.fetchall()
    if invalid_freezers:
        print(f"ERROR: Found {len(invalid_freezers)} orf_position records with invalid freezer_id references")
    else:
        print("✓ All orf_position.freezer_id references are valid")
    
    # Check plasmid_id references
    cursor.execute('''
        SELECT op.plasmid_id
        FROM orf_position op
        LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
        WHERE op.plasmid_id IS NOT NULL AND p.plasmid_id IS NULL
    ''')
    invalid_plasmids = cursor.fetchall()
    if invalid_plasmids:
        print(f"ERROR: Found {len(invalid_plasmids)} orf_position records with invalid plasmid_id references")
    else:
        print("✓ All orf_position.plasmid_id references are valid")
    
    # Check orf_sequence organism references
    print("\nChecking ORF organism references...")
    cursor.execute('''
        SELECT os.orf_id, os.orf_organism_id
        FROM orf_sequence os
        LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
        WHERE os.orf_organism_id IS NOT NULL AND o.organism_id IS NULL
    ''')
    invalid_organisms = cursor.fetchall()
    if invalid_organisms:
        print(f"ERROR: Found {len(invalid_organisms)} orf_sequence records with invalid orf_organism_id references")
    else:
        print("✓ All orf_sequence.orf_organism_id references are valid")
    
    return True

def main():
    """Run all diagnostic checks"""
    print_header("REAGENT DATABASE DIAGNOSTIC TOOL")
    
    # Run checks
    db_structure_ok = check_database_structure()
    if not db_structure_ok:
        print("\nDatabase structure check failed. Skipping further tests.")
        return
    
    detail_view_ok = test_detail_views()
    if not detail_view_ok:
        print("\nDetail view test failed.")
    
    data_ref_ok = verify_data_references()
    if not data_ref_ok:
        print("\nData reference check failed.")
    
    if db_structure_ok and detail_view_ok and data_ref_ok:
        print_header("ALL TESTS PASSED")
        print("""
The database appears to be correctly structured and all queries are working.
If you're still experiencing issues with the detail views:

1. Make sure all links are using string IDs (not integers)
2. Try clearing your browser cache
3. Check that the Flask server has been restarted
        """)
    else:
        print_header("ISSUES DETECTED")
        print("Please fix the issues reported above and re-run this diagnostic tool.")

if __name__ == "__main__":
    main()
