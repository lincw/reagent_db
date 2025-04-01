#!/usr/bin/env python3
"""
Create the human_gene_data table extension for HGNC approved symbols
"""

import sqlite3
import os
from config import get_db_path

def create_human_gene_table():
    """Create the extension table for human gene data if it doesn't exist"""
    DB_PATH = get_db_path()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='human_gene_data'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        print("Creating human_gene_data table...")
        
        # Create the extension table for human-specific data
        cursor.execute('''
        CREATE TABLE human_gene_data (
            orf_id TEXT PRIMARY KEY,
            hgnc_approved_symbol TEXT,
            FOREIGN KEY (orf_id) REFERENCES orf_sequence (orf_id)
        )
        ''')
        
        # Create an index for faster searches
        cursor.execute('CREATE INDEX idx_hgnc_symbol ON human_gene_data (hgnc_approved_symbol)')
        
        conn.commit()
        print("Table created successfully")
    else:
        print("human_gene_data table already exists")
    
    conn.close()

if __name__ == "__main__":
    create_human_gene_table()
