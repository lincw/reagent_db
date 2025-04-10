"""
Utility script to import yeast positions from a CSV file.
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

def import_yeast_positions(csv_path, dry_run=True, validate_orfs=True):
    """
    Import yeast positions from a CSV file
    
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
    
    print(f"{'Validating' if dry_run else 'Importing'} yeast positions from {csv_path}")
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Start a transaction
        if not dry_run:
            c.execute('BEGIN TRANSACTION')
        
        # Check if the yeast_orf_position table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
        if not c.fetchone():
            print("Error: yeast_orf_position table does not exist")
            print("Run the migrations/add_yeast_orf_position.py script first")
            return False
        
        # Check if the position_type column exists
        c.execute("PRAGMA table_info(yeast_orf_position)")
        columns = [column[1] for column in c.fetchall()]
        has_position_type = 'position_type' in columns
        
        if not has_position_type:
            print("Warning: position_type column does not exist in yeast_orf_position table")
            print("Run the migrations/update_yeast_orf_position.py script first")
            
            if not dry_run:
                print("Cannot import without position_type column")
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
            expected_columns = ['orf_id', 'plate', 'well']
            if has_position_type:
                expected_columns.append('position_type')
            
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
            
            if has_position_type:
                position_type_idx = header_lower.index('position_type')
            
            # Process the data rows
            valid_rows = 0
            invalid_rows = 0
            inserted_rows = 0
            errors = []
            
            for i, row in enumerate(reader, start=2):  # Start from 2 to account for header row
                if len(row) < len(header):
                    print(f"Warning: Row {i} has fewer columns than header, skipping")
                    invalid_rows += 1
                    continue
                
                orf_id = row[orf_id_idx].strip()
                plate = row[plate_idx].strip()
                well = row[well_idx].strip()
                
                # Skip empty rows
                if not orf_id or not plate or not well:
                    print(f"Warning: Row {i} has empty required fields, skipping")
                    invalid_rows += 1
                    continue
                
                # Get position type if the column exists
                position_type = None
                if has_position_type:
                    # Get the position type from the CSV, explicitly handle 'DB' case
                    position_type_value = row[position_type_idx].strip().upper()
                    if position_type_value == 'DB':
                        position_type = 'DB'
                    elif position_type_value == 'AD' or not position_type_value:
                        position_type = 'AD'
                    else:
                        print(f"Warning: Row {i} has invalid position_type '{position_type_value}', defaulting to 'AD'")
                        position_type = 'AD'
                else:
                    position_type = 'AD'  # Default to AD if the column doesn't exist
                
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
                        if has_position_type:
                            # Print debug info to verify the position_type value
                            print(f"Inserting row {i}: ORF={orf_id}, Plate={plate}, Well={well}, Type={position_type}")
                            
                            # Use explicit SQL with no defaults to ensure position_type is set correctly
                            insert_sql = "INSERT INTO yeast_orf_position (orf_id, plate, well, position_type) VALUES (?, ?, ?, ?)"
                            c.execute(insert_sql, (orf_id, plate, well, position_type))
                            
                            # Verify the insert worked correctly by querying the last inserted row
                            last_id = c.lastrowid
                            c.execute("SELECT position_type FROM yeast_orf_position WHERE id = ?", (last_id,))
                            actual_type = c.fetchone()[0]
                            print(f"Verification - Row {i}: ID={last_id}, Actual Type={actual_type}")
                            
                            # If the position_type doesn't match what we tried to insert, try a direct update
                            if actual_type != position_type:
                                print(f"Warning: Position type mismatch! Attempting direct update...")
                                c.execute("UPDATE yeast_orf_position SET position_type = ? WHERE id = ?", 
                                          (position_type, last_id))
                                
                                # Verify the update
                                c.execute("SELECT position_type FROM yeast_orf_position WHERE id = ?", (last_id,))
                                updated_type = c.fetchone()[0]
                                print(f"After update: ID={last_id}, Updated Type={updated_type}")
                        else:
                            c.execute(
                                "INSERT INTO yeast_orf_position (orf_id, plate, well) VALUES (?, ?, ?)",
                                (orf_id, plate, well)
                            )
                        inserted_rows += 1
                    except sqlite3.Error as e:
                        print(f"Error inserting row {i}: {e}")
                        errors.append(f"Row {i}: {e}")
                        invalid_rows += 1
            
            # Summary
            print(f"\nSummary:")
            print(f"  Valid rows: {valid_rows}")
            print(f"  Invalid rows: {invalid_rows}")
            if not dry_run:
                print(f"  Inserted rows: {inserted_rows}")
            
            if errors:
                print(f"\nErrors ({len(errors)}):")
                for error in errors[:10]:  # Show only the first 10 errors
                    print(f"  {error}")
                if len(errors) > 10:
                    print(f"  ... and {len(errors) - 10} more errors")
            
            # Commit the transaction if not a dry run
            if not dry_run:
                if inserted_rows > 0:
                    c.execute('COMMIT')
                    print("\nSuccessfully imported yeast positions")
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
    parser = argparse.ArgumentParser(description='Import yeast positions from a CSV file')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--dry-run', action='store_true', help='Validate the file without making changes')
    parser.add_argument('--no-validate', action='store_true', help='Skip ORF ID validation')
    
    args = parser.parse_args()
    
    success = import_yeast_positions(
        csv_path=args.csv_file,
        dry_run=args.dry_run,
        validate_orfs=not args.no_validate
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
