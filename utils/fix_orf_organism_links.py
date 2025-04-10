"""
Utility script to check and fix relationships between organisms and ORF sequences
"""

import sqlite3
import os
import sys
import argparse
from datetime import datetime

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_db_path

def analyze_links():
    """Analyze the links between organisms and ORF sequences"""
    DB_PATH = get_db_path()
    
    if not os.path.exists(DB_PATH):
        print(f'Error: Database does not exist at {DB_PATH}')
        return False
    
    print(f'Analyzing database at {DB_PATH}')
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    c = conn.cursor()
    
    try:
        # 1. Check if the orf_id field exists in the organisms table
        c.execute("PRAGMA table_info(organisms)")
        columns = [column['name'] for column in c.fetchall()]
        
        if 'orf_id' not in columns:
            print("Error: orf_id column is missing from the organisms table.")
            print("Please run the fix_organisms_schema migration first.")
            return False
        
        # 2. Get statistics about the current state
        c.execute('''SELECT COUNT(*) FROM organisms''')
        total_organisms = c.fetchone()[0]
        
        c.execute('''SELECT COUNT(*) FROM organisms WHERE orf_id IS NOT NULL''')
        organisms_with_orf = c.fetchone()[0]
        
        c.execute('''SELECT COUNT(*) FROM orf_sequence''')
        total_orfs = c.fetchone()[0]
        
        c.execute('''SELECT COUNT(*) FROM orf_sequence WHERE orf_organism_id IS NOT NULL''')
        orfs_with_organism = c.fetchone()[0]
        
        # 3. Find organisms without linked ORFs
        c.execute('''
        SELECT organism_id, organism_name, organism_genus, organism_species, organism_strain
        FROM organisms
        WHERE orf_id IS NULL
        LIMIT 10
        ''')
        unlinked_organisms = c.fetchall()
        
        # 4. Find ORFs referring to non-existent organisms
        c.execute('''
        SELECT orf_id, orf_name, orf_organism_id
        FROM orf_sequence
        WHERE orf_organism_id IS NOT NULL 
        AND orf_organism_id NOT IN (SELECT organism_id FROM organisms)
        LIMIT 10
        ''')
        orphaned_orfs = c.fetchall()
        
        # 5. Find organisms with multiple ORFs
        c.execute('''
        SELECT o.organism_id, o.organism_name, COUNT(s.orf_id) as orf_count
        FROM organisms o
        JOIN orf_sequence s ON o.organism_id = s.orf_organism_id
        GROUP BY o.organism_id
        HAVING COUNT(s.orf_id) > 1
        LIMIT 10
        ''')
        multi_orf_organisms = c.fetchall()
        
        # Print the report
        print("\n===== DATABASE RELATIONSHIP ANALYSIS =====")
        print(f"Total organisms: {total_organisms}")
        print(f"Organisms with linked ORFs: {organisms_with_orf} ({organisms_with_orf/total_organisms*100:.1f}% if total_organisms > 0 else 0}%)")
        print(f"Total ORF sequences: {total_orfs}")
        print(f"ORFs with organism references: {orfs_with_organism} ({orfs_with_organism/total_orfs*100:.1f}% if total_orfs > 0 else 0}%)")
        
        print("\n----- ISSUES DETECTED -----")
        print(f"Organisms without linked ORFs: {total_organisms - organisms_with_orf}")
        if unlinked_organisms:
            print("Sample unlinked organisms:")
            for org in unlinked_organisms:
                print(f"  - {org['organism_id']}: {org['organism_name']} ({org['organism_genus']} {org['organism_species']})")
        
        print(f"\nORFs with invalid organism references: {len(orphaned_orfs)}")
        if orphaned_orfs:
            print("Sample orphaned ORFs:")
            for orf in orphaned_orfs:
                print(f"  - {orf['orf_id']}: {orf['orf_name']} (references unknown organism {orf['orf_organism_id']})")
        
        print(f"\nOrganisms with multiple ORFs: {len(multi_orf_organisms)}")
        if multi_orf_organisms:
            print("Sample multi-ORF organisms:")
            for org in multi_orf_organisms:
                print(f"  - {org['organism_id']}: {org['organism_name']} ({org['orf_count']} ORFs)")
        
        return True
        
    except Exception as e:
        print(f'Error during analysis: {str(e)}')
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()

def fix_links(dry_run=True):
    """Fix broken links between organisms and ORF sequences"""
    DB_PATH = get_db_path()
    
    if not os.path.exists(DB_PATH):
        print(f'Error: Database does not exist at {DB_PATH}')
        return False
    
    mode = "Analyzing" if dry_run else "Fixing"
    print(f'{mode} database at {DB_PATH}')
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    c = conn.cursor()
    
    try:
        if not dry_run:
            # Create a backup first
            backup_path = os.path.join(
                os.path.dirname(DB_PATH),
                f'db_backups/reagent_db_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sqlite'
            )
            
            # Ensure the backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy the database file
            import shutil
            shutil.copy2(DB_PATH, backup_path)
            print(f'Created backup at {backup_path}')
            
            # Start a transaction
            c.execute('BEGIN TRANSACTION')
        
        # 1. Update organisms.orf_id where it's missing but a matching ORF exists
        c.execute('''
        SELECT organism_id 
        FROM organisms 
        WHERE orf_id IS NULL 
        AND organism_id IN (
            SELECT orf_organism_id 
            FROM orf_sequence 
            WHERE orf_organism_id IS NOT NULL
        )
        ''')
        missing_orf_ids = [row[0] for row in c.fetchall()]
        
        print(f"Found {len(missing_orf_ids)} organisms missing orf_id that have matching ORFs")
        
        fixed_count = 0
        for organism_id in missing_orf_ids:
            # Get the first ORF associated with this organism
            c.execute('''
            SELECT orf_id 
            FROM orf_sequence 
            WHERE orf_organism_id = ?
            LIMIT 1
            ''', (organism_id,))
            orf_id = c.fetchone()[0]
            
            if dry_run:
                print(f"Would link organism {organism_id} to ORF {orf_id}")
            else:
                c.execute('''
                UPDATE organisms
                SET orf_id = ?
                WHERE organism_id = ?
                ''', (orf_id, organism_id))
                fixed_count += 1
        
        if not dry_run:
            print(f"Fixed {fixed_count} organism-ORF links")
        
        # 2. Create missing organisms for orphaned ORFs
        c.execute('''
        SELECT orf_id, orf_name, orf_organism_id
        FROM orf_sequence
        WHERE orf_organism_id IS NOT NULL 
        AND orf_organism_id NOT IN (SELECT organism_id FROM organisms)
        ''')
        orphaned_orfs = c.fetchall()
        
        print(f"Found {len(orphaned_orfs)} ORFs with missing organism references")
        
        created_count = 0
        for orf in orphaned_orfs:
            # Construct an organism name from the ORF info
            organism_name = f"Unknown ({orf['orf_name']})"
            
            if dry_run:
                print(f"Would create organism {orf['orf_organism_id']} for ORF {orf['orf_id']}")
            else:
                c.execute('''
                INSERT INTO organisms (organism_id, organism_name, organism_genus, organism_species, organism_strain, orf_id)
                VALUES (?, ?, 'Unknown', 'Unknown', 'Unknown', ?)
                ''', (orf['orf_organism_id'], organism_name, orf['orf_id']))
                created_count += 1
        
        if not dry_run:
            print(f"Created {created_count} missing organisms")
            c.execute('COMMIT')
            print("Changes committed to database")
        else:
            print("\nThis was a dry run. No changes were made to the database.")
            print("Run with --fix to apply these changes.")
        
        return True
        
    except Exception as e:
        if not dry_run:
            c.execute('ROLLBACK')
            print("Changes rolled back due to error")
        
        print(f'Error during operation: {str(e)}')
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix relationships between organisms and ORF sequences')
    parser.add_argument('--fix', action='store_true', help='Actually make changes (default is dry run)')
    parser.add_argument('--analyze', action='store_true', help='Just analyze relationships without fixing')
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_links()
    else:
        fix_links(dry_run=not args.fix)
