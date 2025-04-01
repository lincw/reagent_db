#!/usr/bin/env python3
"""
Debug script to check why organism filtering is not working
"""

import sqlite3
from config import get_db_path

def debug_organisms_table():
    """Check the structure and content of the organisms table"""
    DB_PATH = get_db_path()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get table structure
    print("Organisms table structure:")
    cursor.execute("PRAGMA table_info(organisms)")
    columns = cursor.fetchall()
    for column in columns:
        print(f"  {column['name']} ({column['type']})")
    
    # Count organisms
    cursor.execute("SELECT COUNT(*) FROM organisms")
    count = cursor.fetchone()[0]
    print(f"\nTotal organisms in table: {count}")
    
    # Get distinct organism names
    cursor.execute("SELECT COUNT(DISTINCT organism_name) FROM organisms")
    unique_count = cursor.fetchone()[0]
    print(f"Unique organism names: {unique_count}")
    
    # Sample organism records
    print("\nSample organisms:")
    cursor.execute("SELECT organism_id, organism_name FROM organisms LIMIT 5")
    organisms = cursor.fetchall()
    for org in organisms:
        print(f"  ID: {org['organism_id']}, Name: {org['organism_name']}")
    
    # Check if 'Homo sapiens' exists
    print("\nSearching for 'Homo sapiens':")
    cursor.execute("SELECT organism_id, organism_name FROM organisms WHERE organism_name = 'Homo sapiens'")
    homo_sapiens = cursor.fetchall()
    if homo_sapiens:
        print(f"  Found {len(homo_sapiens)} records:")
        for org in homo_sapiens:
            print(f"  ID: {org['organism_id']}, Name: {org['organism_name']}")
    else:
        print("  Not found in database")
    
    # Check orf_sequence table for organism references
    print("\nChecking ORF sequences with organism references:")
    cursor.execute("""
        SELECT COUNT(*) FROM orf_sequence 
        WHERE orf_organism_id IS NOT NULL AND orf_organism_id != ''
    """)
    orfs_with_organism = cursor.fetchone()[0]
    print(f"ORFs with organism references: {orfs_with_organism}")
    
    # Sample ORF records with organism
    print("\nSample ORFs with organism references:")
    cursor.execute("""
        SELECT os.orf_id, os.orf_name, os.orf_organism_id, o.organism_name
        FROM orf_sequence os
        LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
        WHERE os.orf_organism_id IS NOT NULL AND os.orf_organism_id != ''
        LIMIT 5
    """)
    orfs = cursor.fetchall()
    for orf in orfs:
        print(f"  ORF: {orf['orf_name']} (ID: {orf['orf_id']}), Organism ID: {orf['orf_organism_id']}, Organism Name: {orf['organism_name']}")
    
    # Check specific gene
    print("\nLooking for 'TP53':")
    cursor.execute("""
        SELECT os.orf_id, os.orf_name, os.orf_organism_id, o.organism_name
        FROM orf_sequence os
        LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
        WHERE os.orf_name LIKE '%TP53%'
    """)
    tp53_orfs = cursor.fetchall()
    if tp53_orfs:
        print(f"  Found {len(tp53_orfs)} TP53 records:")
        for orf in tp53_orfs:
            print(f"  ORF: {orf['orf_name']} (ID: {orf['orf_id']}), Organism ID: {orf['orf_organism_id']}, Organism Name: {orf['organism_name']}")
    else:
        print("  No TP53 records found")
    
    conn.close()

if __name__ == "__main__":
    debug_organisms_table()
