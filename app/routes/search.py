from flask import request, jsonify
import sqlite3
import re
from app import app, DB_PATH
from app.utils import format_database_ids

@app.route('/search', methods=['POST'])
def search():
    query_type = request.form.get('query_type')
    search_term = request.form.get('search_term')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    results = []
    
    if query_type == 'gene':
        # Search for gene (ORF) by name or annotation
        c.execute('''
            SELECT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain
            FROM orf_sequence os
            LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            WHERE os.orf_name LIKE ? OR os.orf_annotation LIKE ? OR os.orf_id LIKE ? 
            OR os.orf_entrez_id LIKE ? OR os.orf_ensembl_id LIKE ? OR os.orf_uniprot_id LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', 
              f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        
        results = [format_database_ids(dict(row)) for row in c.fetchall()]
        
        # For each ORF, get its position information
        for result in results:
            orf_id = result['orf_id']
            c.execute('''
                SELECT op.*, f.freezer_location, p.plasmid_name
                FROM orf_position op
                LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
                LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
                WHERE op.orf_id = ?
            ''', (orf_id,))
            
            position_data = [dict(row) for row in c.fetchall()]
            result['positions'] = position_data
    
    elif query_type == 'plasmid':
        # Search for plasmid by name or description
        c.execute('''
            SELECT p.*, COUNT(op.orf_id) as orf_count
            FROM plasmid p
            LEFT JOIN orf_position op ON p.plasmid_id = op.plasmid_id
            WHERE p.plasmid_name LIKE ? OR p.plasmid_description LIKE ?
            GROUP BY p.plasmid_id
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        results = [dict(row) for row in c.fetchall()]
        
        # For each plasmid, get associated ORFs
        for result in results:
            plasmid_id = result['plasmid_id']
            c.execute('''
                SELECT os.orf_id, os.orf_name, os.orf_annotation, op.plate, op.well
                FROM orf_position op
                JOIN orf_sequence os ON op.orf_id = os.orf_id
                WHERE op.plasmid_id = ?
            ''', (plasmid_id,))
            
            orf_data = [dict(row) for row in c.fetchall()]
            result['orfs'] = orf_data
    
    elif query_type == 'location':
        # Search by plate/well location
        parts = search_term.split('-')
        plate = parts[0] if len(parts) > 0 else ''
        well = parts[1] if len(parts) > 1 else ''
        
        c.execute('''
            SELECT op.*, os.orf_name, os.orf_annotation, f.freezer_location, p.plasmid_name
            FROM orf_position op
            LEFT JOIN orf_sequence os ON op.orf_id = os.orf_id
            LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
            LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
            WHERE op.plate LIKE ? AND op.well LIKE ?
        ''', (f'%{plate}%', f'%{well}%'))
        
        results = [dict(row) for row in c.fetchall()]
    
    elif query_type == 'organism':
        # Search by organism
        c.execute('''
            SELECT o.*, COUNT(os.orf_id) as orf_count
            FROM organisms o
            LEFT JOIN orf_sequence os ON o.organism_id = os.orf_organism_id
            WHERE o.organism_name LIKE ? OR o.organism_genus LIKE ? OR o.organism_species LIKE ?
            GROUP BY o.organism_id
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        
        results = [dict(row) for row in c.fetchall()]
        
        # For each organism, get associated ORFs
        for result in results:
            organism_id = result['organism_id']
            c.execute('''
                SELECT orf_id, orf_name, orf_annotation
                FROM orf_sequence
                WHERE orf_organism_id = ?
            ''', (organism_id,))
            
            orf_data = [dict(row) for row in c.fetchall()]
            result['orfs'] = orf_data
    
    conn.close()
    
    return jsonify({'results': results})

@app.route('/batch_search', methods=['POST'])
def batch_search():
    """Search for multiple genes/ORFs at once"""
    search_terms = request.form.get('search_terms', '')
    
    # Split the input by common separators (newline, comma, semicolon, tab)
    terms = [term.strip() for term in re.split(r'[\n,;\t]+', search_terms) if term.strip()]
    
    if not terms:
        return jsonify({'success': False, 'message': 'No search terms provided'})
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    results = []
    not_found = []
    
    for term in terms:
        # Search for exact matches first
        c.execute('''
            SELECT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain
            FROM orf_sequence os
            LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            WHERE os.orf_id = ? OR os.orf_name = ? OR os.orf_entrez_id = ? 
            OR os.orf_ensembl_id = ? OR os.orf_uniprot_id = ?
        ''', (term, term, term, term, term))
        
        exact_matches = [format_database_ids(dict(row)) for row in c.fetchall()]
        
        if not exact_matches:
            # If no exact matches, try partial matches
            c.execute('''
                SELECT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain
                FROM orf_sequence os
                LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                WHERE os.orf_name LIKE ? OR os.orf_annotation LIKE ?
            ''', (f'%{term}%', f'%{term}%'))
            
            partial_matches = [format_database_ids(dict(row)) for row in c.fetchall()]
            
            if partial_matches:
                results.extend(partial_matches)
            else:
                not_found.append(term)
        else:
            results.extend(exact_matches)
    
    # For each ORF, get its position information
    for result in results:
        orf_id = result['orf_id']
        c.execute('''
            SELECT op.*, f.freezer_location, p.plasmid_name
            FROM orf_position op
            LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
            LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
            WHERE op.orf_id = ?
        ''', (orf_id,))
        
        position_data = [dict(row) for row in c.fetchall()]
        result['positions'] = position_data
    
    conn.close()
    
    return jsonify({
        'success': True, 
        'results': results, 
        'count': len(results),
        'not_found': not_found,
        'terms_searched': len(terms)
    })

@app.route('/api/search_examples')
def get_search_examples():
    """Get search examples for the autocomplete/placeholder feature"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    examples = {
        'gene': [],
        'plasmid': [],
        'location': [],
        'organism': []
    }
    
    # Get gene examples
    c.execute('SELECT orf_name FROM orf_sequence ORDER BY RANDOM() LIMIT 5')
    examples['gene'] = [row[0] for row in c.fetchall()]
    
    # Get plasmid examples
    c.execute('SELECT plasmid_name FROM plasmid ORDER BY RANDOM() LIMIT 5')
    examples['plasmid'] = [row[0] for row in c.fetchall()]
    
    # Get location examples
    c.execute('SELECT plate || "-" || well FROM orf_position ORDER BY RANDOM() LIMIT 5')
    examples['location'] = [row[0] for row in c.fetchall()]
    
    # Get organism examples
    c.execute('SELECT organism_name FROM organisms ORDER BY RANDOM() LIMIT 5')
    examples['organism'] = [row[0] for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({'success': True, 'examples': examples})
