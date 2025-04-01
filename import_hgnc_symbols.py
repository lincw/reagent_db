#!/usr/bin/env python3
"""
Import HGNC approved symbols from a CSV file
"""

import csv
import sqlite3
import sys
import os
from config import get_db_path

def import_hgnc_symbols(csv_file):
    """Import HGNC approved symbols from CSV file"""
    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        return False
    
    # Create the human_gene_data table if it doesn't exist
    try:
        from create_human_gene_table import create_human_gene_table
        create_human_gene_table()
    except ImportError:
        print("Warning: Could not import create_human_gene_table. Make sure the table exists.")
    
    # Connect to database
    DB_PATH = get_db_path()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='human_gene_data'")
    if not cursor.fetchone():
        print("Error: human_gene_data table does not exist. Please run create_human_gene_table.py first.")
        conn.close()
        return False
    
    # Read CSV file and import data
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check if required columns exist
            required_columns = ['orf_id', 'hgnc_approved_symbol']
            missing_columns = [col for col in required_columns if col not in reader.fieldnames]
            
            if missing_columns:
                print(f"Error: Missing required columns in CSV: {', '.join(missing_columns)}")
                conn.close()
                return False
            
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Clear existing data if requested
            clear_existing = input("Clear existing HGNC data before import? (y/N): ").lower() == 'y'
            if clear_existing:
                cursor.execute("DELETE FROM human_gene_data")
                print("Cleared existing HGNC data.")
            
            # Import data
            for row in reader:
                orf_id = row['orf_id'].strip()
                hgnc_symbol = row['hgnc_approved_symbol'].strip()
                
                # Skip empty entries
                if not orf_id or not hgnc_symbol:
                    skipped_count += 1
                    continue
                
                # Verify orf_id exists in orf_sequence table
                cursor.execute("SELECT COUNT(*) FROM orf_sequence WHERE orf_id = ?", (orf_id,))
                if cursor.fetchone()[0] == 0:
                    print(f"Warning: ORF ID {orf_id} not found in orf_sequence table. Skipping.")
                    skipped_count += 1
                    continue
                
                try:
                    # Check if entry already exists
                    cursor.execute("SELECT COUNT(*) FROM human_gene_data WHERE orf_id = ?", (orf_id,))
                    if cursor.fetchone()[0] > 0:
                        if clear_existing:
                            # Should be cleared already, but just in case
                            cursor.execute("DELETE FROM human_gene_data WHERE orf_id = ?", (orf_id,))
                        else:
                            # Update existing entry
                            cursor.execute(
                                "UPDATE human_gene_data SET hgnc_approved_symbol = ? WHERE orf_id = ?",
                                (hgnc_symbol, orf_id)
                            )
                            imported_count += 1
                            continue
                    
                    # Insert new entry
                    cursor.execute(
                        "INSERT INTO human_gene_data (orf_id, hgnc_approved_symbol) VALUES (?, ?)",
                        (orf_id, hgnc_symbol)
                    )
                    imported_count += 1
                    
                except sqlite3.Error as e:
                    print(f"Error importing ORF ID {orf_id}: {e}")
                    error_count += 1
            
            # Commit transaction
            conn.commit()
            
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        conn.rollback()
        conn.close()
        return False
    
    # Print summary
    print(f"\nImport summary:")
    print(f"  Imported/updated: {imported_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    
    conn.close()
    return True

def main():
    """Main entry point"""
    print("\n===== HGNC APPROVED SYMBOL IMPORT =====\n")
    
    if len(sys.argv) != 2:
        print("Usage: python import_hgnc_symbols.py <csv_file>")
        print("\nThe CSV file should contain at least these columns:")
        print("  - orf_id: The ORF ID matching entries in the orf_sequence table")
        print("  - hgnc_approved_symbol: The HGNC approved symbol for the gene")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    if import_hgnc_symbols(csv_file):
        print("\nImport completed successfully.")
    else:
        print("\nImport failed.")

if __name__ == "__main__":
    main()
