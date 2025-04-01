#!/usr/bin/env python3
"""
Debug script to check why certain genes appear in p53 search results
"""

import sqlite3
import sys
from config import get_db_path

def debug_search(search_term):
    """Look for specific occurrences of the search term in annotations"""
    DB_PATH = get_db_path()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all genes that would match with the search term
    cursor.execute('''
        SELECT orf_id, orf_name, orf_annotation, orf_entrez_id, orf_ensembl_id, orf_uniprot_id
        FROM orf_sequence
        WHERE orf_name LIKE ? OR orf_annotation LIKE ? OR orf_id LIKE ? 
        OR orf_entrez_id LIKE ? OR orf_ensembl_id LIKE ? OR orf_uniprot_id LIKE ?
    ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', 
          f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
    
    results = cursor.fetchall()
    
    print(f"Search results for '{search_term}':")
    print("-" * 80)
    
    for result in results:
        print(f"Gene: {result['orf_name']}, ID: {result['orf_id']}")
        
        # Check which field(s) matched
        fields = []
        
        if search_term.lower() in str(result['orf_name']).lower():
            fields.append(f"Name: '{result['orf_name']}'")
            
        if search_term.lower() in str(result['orf_id']).lower():
            fields.append(f"ID: '{result['orf_id']}'")
            
        if search_term.lower() in str(result['orf_entrez_id']).lower():
            fields.append(f"Entrez ID: '{result['orf_entrez_id']}'")
            
        if search_term.lower() in str(result['orf_ensembl_id']).lower():
            fields.append(f"Ensembl ID: '{result['orf_ensembl_id']}'")
            
        if search_term.lower() in str(result['orf_uniprot_id']).lower():
            fields.append(f"UniProt ID: '{result['orf_uniprot_id']}'")
        
        # For annotations, show the context
        if result['orf_annotation'] and search_term.lower() in str(result['orf_annotation']).lower():
            annotation = str(result['orf_annotation'])
            # Find the position of the search term
            pos = annotation.lower().find(search_term.lower())
            # Extract a context snippet (50 chars before and after)
            start = max(0, pos - 50)
            end = min(len(annotation), pos + len(search_term) + 50)
            context = annotation[start:end]
            
            if start > 0:
                context = "..." + context
            if end < len(annotation):
                context = context + "..."
                
            fields.append(f"Annotation contains: '{context}'")
        
        print("  Matched in:", ", ".join(fields))
        print("-" * 80)
    
    print(f"Total matches: {len(results)}")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_term = sys.argv[1]
    else:
        search_term = "p53"
    
    debug_search(search_term)
