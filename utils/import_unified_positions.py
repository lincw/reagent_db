"""
Utility script to import unified position data from a CSV file.
This handles entry positions, yeast AD positions, and yeast DB positions in a single import,
along with source attribution.
"""

import csv
import sqlite3
import os
import sys
import argparse
from datetime import datetime

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_db_path

def import_unified_positions(csv_path, dry_run=True, validate_orfs=True):
    """
    Import unified position data from a CSV file
    
    Args:
        csv_path: Path to the CSV file
        dry_run: If True, only validate the file without making changes
        validate_orfs: If True, check that all ORF IDs exist in the database
    """
    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return False
    
    # Get the database path
    DB_PATH = get_db_path()
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return False
    
    print(f"{'Validating' if dry_run else 'Importing'} unified position data from {csv_path}")
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Start a transaction
        if not dry_run:
            c.execute('BEGIN TRANSACTION')
        
        # Check if the required tables exist
        for table in ['orf_position', 'yeast_orf_position', 'orf_sources']:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not c.fetchone():
                print(f"Error: {table} table does not exist")
                return False
        
        # Check if the position_type column exists in yeast_orf_position
        c.execute("PRAGMA table_info(yeast_orf_position)")
        columns = [column[1] for column in c.fetchall()]
        has_position_type = 'position_type' in columns
        
        if not has_position_type:
            print("Error: position_type column does not exist in yeast_orf_position table")
            print("Run the migrations/update_yeast_orf_position.py script first")
            return False
        
        # Read the CSV file
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            
            # Get the header row
            try:
                header = next(reader)
            except StopIteration:
                print("Error: CSV file is empty")
                return False
            
            # Check if the header has the expected columns
            expected_columns = [
                'orf_id', 'plate', 'well', 
                'entry_position', 'yeast_ad_position', 'yeast_db_position',
                'source_name', 'source_details'
            ]
            
            # Check if all required columns are present (case-insensitive)
            header_lower = [col.lower() for col in header]
            missing_columns = [col for col in expected_columns if col.lower() not in header_lower]
            
            if missing_columns:
                print(f"Error: CSV file is missing required columns: {', '.join(missing_columns)}")
                print(f"Expected columns: {', '.join(expected_columns)}")
                print(f"Found columns: {', '.join(header)}")
                return False
            
            # Get the column indices
            orf_id_idx = header_lower.index('orf_id')
            plate_idx = header_lower.index('plate')
            well_idx = header_lower.index('well')
            entry_position_idx = header_lower.index('entry_position')
            yeast_ad_position_idx = header_lower.index('yeast_ad_position')
            yeast_db_position_idx = header_lower.index('yeast_db_position')
            source_name_idx = header_lower.index('source_name')
            source_details_idx = header_lower.index('source_details')
            
            # Process the data rows
            valid_rows = 0
            invalid_rows = 0
            inserted_rows = {
                'entry': 0,
                'yeast_ad': 0,
                'yeast_db': 0,
                'source': 0
            }
            errors = []
            
            for i, row in enumerate(reader, start=2):  # Start from 2 to account for header row
                if len(row) < len(header):
                    print(f"Warning: Row {i} has fewer columns than header, skipping")
                    invalid_rows += 1
                    continue
                
                orf_id = row[orf_id_idx].strip()
                plate = row[plate_idx].strip()
                well = row[well_idx].strip()
                
                # Parse position flags (Yes/No/True/False)
                def parse_boolean(value):
                    if not value:
                        return False
                    value = value.strip().lower()
                    return value in ['yes', 'true', '1', 'y', 't']
                
                entry_position = parse_boolean(row[entry_position_idx])
                yeast_ad_position = parse_boolean(row[yeast_ad_position_idx])
                yeast_db_position = parse_boolean(row[yeast_db_position_idx])
                
                # Get source information
                source_name = row[source_name_idx].strip()
                source_details = row[source_details_idx].strip()
                
                # Skip empty rows
                if not orf_id or not plate or not well:
                    print(f"Warning: Row {i} has empty required fields, skipping")
                    invalid_rows += 1
                    continue
                
                # Skip rows with no positions
                if not (entry_position or yeast_ad_position or yeast_db_position):
                    print(f"Warning: Row {i} has no positions enabled, skipping")
                    invalid_rows += 1
                    continue
                
                # Skip rows with no source information
                if not source_name:
                    print(f"Warning: Row {i} has no source name, skipping")
                    invalid_rows += 1
                    continue
                
                # Validate ORF ID if requested
                if validate_orfs:
                    c.execute("SELECT 1 FROM orf_sequence WHERE orf_id = ?", (orf_id,))
                    if not c.fetchone():
                        print(f"Warning: Row {i} has unknown ORF ID '{orf_id}', skipping")
                        errors.append(f"Row {i}: Unknown ORF ID '{orf_id}'")
                        invalid_rows += 1
                        continue
                
                valid_rows += 1
                
                # Insert the data if not a dry run
                if not dry_run:
                    try:
                        # 1. Insert entry position if enabled
                        if entry_position:
                            try:
                                c.execute(
                                    "INSERT INTO orf_position (orf_id, plate, well) VALUES (?, ?, ?)",
                                    (orf_id, plate, well)
                                )
                                inserted_rows['entry'] += 1
                            except sqlite3.Error as e:
                                print(f"Warning: Failed to insert entry position in row {i}: {e}")
                                errors.append(f"Row {i}: Entry position error: {e}")
                        
                        # 2. Insert yeast AD position if enabled
                        if yeast_ad_position:
                            try:
                                c.execute(
                                    "INSERT INTO yeast_orf_position (orf_id, plate, well, position_type) VALUES (?, ?, ?, ?)",
                                    (orf_id, plate, well, 'AD')
                                )
                                inserted_rows['yeast_ad'] += 1
                            except sqlite3.Error as e:
                                print(f"Warning: Failed to insert yeast AD position in row {i}: {e}")
                                errors.append(f"Row {i}: Yeast AD position error: {e}")
                        
                        # 3. Insert yeast DB position if enabled
                        if yeast_db_position:
                            try:
                                c.execute(
                                    "INSERT INTO yeast_orf_position (orf_id, plate, well, position_type) VALUES (?, ?, ?, ?)",
                                    (orf_id, plate, well, 'DB')
                                )
                                inserted_rows['yeast_db'] += 1
                            except sqlite3.Error as e:
                                print(f"Warning: Failed to insert yeast DB position in row {i}: {e}")
                                errors.append(f"Row {i}: Yeast DB position error: {e}")
                        
                        # 4. Insert the source information
                        try:
                            submission_date = datetime.now().strftime("%Y-%m-%d")
                            c.execute(
                                "INSERT INTO orf_sources (orf_id, source_name, source_details, submission_date) VALUES (?, ?, ?, ?)",
                                (orf_id, source_name, source_details, submission_date)
                            )
                            inserted_rows['source'] += 1
                        except sqlite3.Error as e:
                            print(f"Warning: Failed to insert source information in row {i}: {e}")
                            errors.append(f"Row {i}: Source information error: {e}")
                    
                    except Exception as e:
                        print(f"Error processing row {i}: {e}")
                        errors.append(f"Row {i}: {e}")
                        invalid_rows += 1
                        continue
            
            # Summary
            print(f"\nSummary:")
            print(f"  Valid rows: {valid_rows}")
            print(f"  Invalid rows: {invalid_rows}")
            if not dry_run:
                print(f"  Inserted rows:")
                print(f"    Entry positions: {inserted_rows['entry']}")
                print(f"    Yeast AD positions: {inserted_rows['yeast_ad']}")
                print(f"    Yeast DB positions: {inserted_rows['yeast_db']}")
                print(f"    Source attributions: {inserted_rows['source']}")
            
            if errors:
                print(f"\nErrors ({len(errors)}):")
                for error in errors[:10]:  # Show only the first 10 errors
                    print(f"  {error}")
                if len(errors) > 10:
                    print(f"  ... and {len(errors) - 10} more errors")
            
            # Commit the transaction if not a dry run
            if not dry_run:
                if sum(inserted_rows.values()) > 0:
                    c.execute('COMMIT')
                    print("\nSuccessfully imported unified positions")
                    return True
                else:
                    c.execute('ROLLBACK')
                    print("\nNo valid rows to import, rolling back")
                    return False
            else:
                print("\nDry run completed, no changes made to the database")
                if valid_rows > 0:
                    print(f"Would have imported {valid_rows} rows")
                    return True
                else:
                    print("No valid rows to import")
                    return False
    
    except Exception as e:
        # Roll back the transaction if not a dry run
        if not dry_run:
            c.execute('ROLLBACK')
        
        print(f"Error during import: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Close the database connection
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Import unified position data from a CSV file')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--dry-run', action='store_true', help='Validate the file without making changes')
    parser.add_argument('--no-validate', action='store_true', help='Skip ORF ID validation')
    
    args = parser.parse_args()
    
    success = import_unified_positions(
        csv_path=args.csv_file,
        dry_run=args.dry_run,
        validate_orfs=not args.no_validate
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()