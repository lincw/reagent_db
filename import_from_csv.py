#!/usr/bin/env python3
"""
Import data from CSV files into the Reagent Database
"""

import sqlite3
import os
import csv
import sys
from config import get_db_path

def read_csv(file_path):
    """Read data from a CSV file"""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        return data
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}")
        return None

def import_freezers(cursor, file_path):
    """Import freezer data from CSV"""
    if not os.path.exists(file_path):
        print(f"Freezer CSV file not found: {file_path}")
        return 0
    
    data = read_csv(file_path)
    if not data:
        return 0
    
    count = 0
    for row in data:
        try:
            cursor.execute('''
                INSERT INTO freezer (freezer_id, freezer_location, freezer_condition, freezer_date)
                VALUES (?, ?, ?, ?)
            ''', (
                row.get('freezer_id', '').strip(),
                row.get('freezer_location', '').strip(),
                row.get('freezer_condition', '').strip(),
                row.get('freezer_date', '').strip()
            ))
            count += 1
        except sqlite3.Error as e:
            print(f"Error importing freezer record: {e}")
            print(f"Record data: {row}")
    
    return count

def import_organisms(cursor, file_path):
    """Import organism data from CSV"""
    if not os.path.exists(file_path):
        print(f"Organism CSV file not found: {file_path}")
        return 0
    
    data = read_csv(file_path)
    if not data:
        return 0
    
    count = 0
    for row in data:
        try:
            cursor.execute('''
                INSERT INTO organisms (organism_id, organism_name, organism_genus, organism_species, organism_strain)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                row.get('organism_id', '').strip(),
                row.get('organism_name', '').strip(),
                row.get('organism_genus', '').strip(),
                row.get('organism_species', '').strip(),
                row.get('organism_strain', '').strip()
            ))
            count += 1
        except sqlite3.Error as e:
            print(f"Error importing organism record: {e}")
            print(f"Record data: {row}")
    
    return count

def import_plasmids(cursor, file_path):
    """Import plasmid data from CSV"""
    if not os.path.exists(file_path):
        print(f"Plasmid CSV file not found: {file_path}")
        return 0
    
    data = read_csv(file_path)
    if not data:
        return 0
    
    count = 0
    for row in data:
        try:
            cursor.execute('''
                INSERT INTO plasmid (plasmid_id, plasmid_name, plasmid_type, plasmid_express_organism, plasmid_description)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                row.get('plasmid_id', '').strip(),
                row.get('plasmid_name', '').strip(),
                row.get('plasmid_type', '').strip(),
                row.get('plasmid_express_organism', '').strip(),
                row.get('plasmid_description', '').strip()
            ))
            count += 1
        except sqlite3.Error as e:
            print(f"Error importing plasmid record: {e}")
            print(f"Record data: {row}")
    
    return count

def import_orf_sequences(cursor, file_path):
    """Import ORF sequence data from CSV"""
    if not os.path.exists(file_path):
        print(f"ORF sequence CSV file not found: {file_path}")
        return 0
    
    data = read_csv(file_path)
    if not data:
        return 0
    
    count = 0
    for row in data:
        try:
            cursor.execute('''
                INSERT INTO orf_sequence (
                    orf_id, orf_name, orf_annotation, orf_sequence, 
                    orf_with_stop, orf_open, orf_organism_id, 
                    orf_length_bp, orf_entrez_id, orf_ensembl_id, 
                    orf_uniprot_id, orf_ref_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('orf_id', '').strip(),
                row.get('orf_name', '').strip(),
                row.get('orf_annotation', '').strip(),
                row.get('orf_sequence', '').strip(),
                int(row.get('orf_with_stop', '0')),
                int(row.get('orf_open', '0')),
                row.get('orf_organism_id', '').strip(),
                int(row.get('orf_length_bp', '0')),
                row.get('orf_entrez_id', '').strip(),
                row.get('orf_ensembl_id', '').strip(),
                row.get('orf_uniprot_id', '').strip(),
                row.get('orf_ref_url', '').strip()
            ))
            count += 1
        except sqlite3.Error as e:
            print(f"Error importing ORF sequence record: {e}")
            print(f"Record data: {row}")
    
    return count

def import_orf_positions(cursor, file_path):
    """Import ORF position data from CSV"""
    if not os.path.exists(file_path):
        print(f"ORF position CSV file not found: {file_path}")
        return 0
    
    data = read_csv(file_path)
    if not data:
        return 0
    
    count = 0
    for row in data:
        try:
            cursor.execute('''
                INSERT INTO orf_position (orf_id, plate, well, freezer_id, plasmid_id, orf_create_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                row.get('orf_id', '').strip(),
                row.get('plate', '').strip(),
                row.get('well', '').strip(),
                row.get('freezer_id', '').strip(),
                row.get('plasmid_id', '').strip(),
                row.get('orf_create_date', '').strip()
            ))
            count += 1
        except sqlite3.Error as e:
            print(f"Error importing ORF position record: {e}")
            print(f"Record data: {row}")
    
    return count

def import_data(csv_dir):
    """Import data from CSV files in the specified directory"""
    DB_PATH = get_db_path()
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        print("Please run setup_db.py first to create the database")
        return False
    
    # Check if CSV directory exists
    if not os.path.exists(csv_dir):
        print(f"CSV directory not found: {csv_dir}")
        return False
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Import data from each CSV file
        freezer_count = import_freezers(cursor, os.path.join(csv_dir, 'freezers.csv'))
        print(f"Imported {freezer_count} freezer records")
        
        organism_count = import_organisms(cursor, os.path.join(csv_dir, 'organisms.csv'))
        print(f"Imported {organism_count} organism records")
        
        plasmid_count = import_plasmids(cursor, os.path.join(csv_dir, 'plasmids.csv'))
        print(f"Imported {plasmid_count} plasmid records")
        
        orf_sequence_count = import_orf_sequences(cursor, os.path.join(csv_dir, 'orf_sequences.csv'))
        print(f"Imported {orf_sequence_count} ORF sequence records")
        
        orf_position_count = import_orf_positions(cursor, os.path.join(csv_dir, 'orf_positions.csv'))
        print(f"Imported {orf_position_count} ORF position records")
        
        # Commit changes
        conn.commit()
        print("All data imported successfully")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def main():
    """Run the import process"""
    print("\n===== REAGENT DATABASE CSV IMPORT =====\n")
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python import_from_csv.py <csv_directory>")
        print("\nThe CSV directory should contain the following files:")
        print("  - freezers.csv")
        print("  - organisms.csv")
        print("  - plasmids.csv")
        print("  - orf_sequences.csv")
        print("  - orf_positions.csv")
        return
    
    csv_dir = sys.argv[1]
    
    # Confirm with user
    print(f"This will import data from CSV files in: {csv_dir}")
    confirm = input("Continue? (y/N): ")
    
    if confirm.lower() != 'y':
        print("Import cancelled")
        return
    
    # Import data
    if import_data(csv_dir):
        print("\nData import completed successfully!")
    else:
        print("\nError importing data")

if __name__ == "__main__":
    main()
