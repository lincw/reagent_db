"""
Export database data to CSV files
This script exports all data from the SQLite database to CSV files
"""

import sqlite3
import os
import pandas as pd

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'reagent_db.sqlite')
# Export directory
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'results')

def export_data():
    """Export all database tables to CSV files"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run the application first to create it.")
        return
    
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        print(f"Created export directory: {EXPORT_DIR}")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Export freezer data
    freezer_df = pd.read_sql('SELECT * FROM freezer', conn)
    freezer_df.to_csv(os.path.join(EXPORT_DIR, 'freezer.csv'), index=False)
    print(f"Exported {len(freezer_df)} freezer records")
    
    # Export organisms data
    organisms_df = pd.read_sql('SELECT * FROM organisms', conn)
    organisms_df.to_csv(os.path.join(EXPORT_DIR, 'organisms.csv'), index=False)
    print(f"Exported {len(organisms_df)} organism records")
    
    # Export plasmid data
    plasmid_df = pd.read_sql('SELECT * FROM plasmid', conn)
    plasmid_df.to_csv(os.path.join(EXPORT_DIR, 'plasmid.csv'), index=False)
    print(f"Exported {len(plasmid_df)} plasmid records")
    
    # Export orf_sequence data
    orf_sequence_df = pd.read_sql('SELECT * FROM orf_sequence', conn)
    orf_sequence_df.to_csv(os.path.join(EXPORT_DIR, 'orf_sequence.csv'), index=False)
    print(f"Exported {len(orf_sequence_df)} ORF sequence records")
    
    # Export orf_position data
    orf_position_df = pd.read_sql('SELECT * FROM orf_position', conn)
    # Remove the id column which is auto-generated
    if 'id' in orf_position_df.columns:
        orf_position_df = orf_position_df.drop('id', axis=1)
    orf_position_df.to_csv(os.path.join(EXPORT_DIR, 'orf_position.csv'), index=False)
    print(f"Exported {len(orf_position_df)} ORF position records")
    
    conn.close()
    
    print("All data exported successfully!")

if __name__ == "__main__":
    export_data()
