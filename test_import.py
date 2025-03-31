#!/usr/bin/env python3
"""
Test script for Reagent Database import functionality
This script creates a test CSV file and verifies the import process
"""

import os
import pandas as pd
import sqlite3
from config import get_db_path

def create_test_csv():
    """Create a test CSV file for ORF sequence import"""
    print("Creating test ORF sequence CSV file...")
    
    # Define test data
    test_data = {
        'orf_id': ['TEST001', 'TEST002'],
        'orf_name': ['Test Gene 1', 'Test Gene 2'],
        'orf_sequence': ['ATGCTAGCTAGC', 'CGATCGATCGAT'],
        'orf_organism_id': ['ORG001', 'ORG001'],
        'orf_annotation': ['Test annotation 1', 'Test annotation 2'],
        'orf_with_stop': [1, 0],
        'orf_open': [1, 1],
        'orf_length_bp': [12, 12],
        'orf_entrez_id': ['12345', '67890'],
        'orf_ensembl_id': ['ENSG0001', 'ENSG0002'],
        'orf_uniprot_id': ['P12345', 'P67890'],
        'orf_ref_url': ['http://example.com/1', 'http://example.com/2']
    }
    
    # Create DataFrame
    df = pd.DataFrame(test_data)
    
    # Create exports directory if it doesn't exist
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
    
    # Save to CSV
    csv_path = os.path.join(exports_dir, 'test_import.csv')
    df.to_csv(csv_path, index=False)
    
    print(f"Test CSV created at: {csv_path}")
    return csv_path

def verify_database_entries():
    """Check if the test entries exist in the database"""
    print("\nVerifying database entries...")
    
    DB_PATH = get_db_path()
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check for test entries
    cursor.execute("SELECT orf_id, orf_name FROM orf_sequence WHERE orf_id LIKE 'TEST%'")
    results = cursor.fetchall()
    
    if results:
        print("Found test entries in database:")
        for row in results:
            print(f"  - {row[0]}: {row[1]}")
        return True
    else:
        print("No test entries found in database.")
        return False

def instructions():
    """Print instructions for manual testing"""
    print("\n" + "="*70)
    print("MANUAL IMPORT TEST INSTRUCTIONS")
    print("="*70)
    print("1. Start the Reagent Database application (python run.py)")
    print("2. Go to the Import page")
    print("3. Select 'ORF Sequence' as the import type")
    print("4. Upload the test file from the exports directory:")
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports', 'test_import.csv')
    print(f"   {csv_path}")
    print("5. Click 'Upload & Import'")
    print("6. Check if you get a success message")
    print("7. Run this script again with --verify flag to check the database")
    print("="*70)

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_database_entries()
        return
    
    # Create test CSV file
    create_test_csv()
    
    # Print instructions
    instructions()

if __name__ == "__main__":
    main()
