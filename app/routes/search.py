from flask import request, jsonify
import sqlite3
import re
from app import app, DB_PATH
from app.utils import format_database_ids

@app.route('/api/search_organisms')
def get_search_organisms():
    """Get all unique organisms in the database for search filtering"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get distinct organisms (only unique organism names)
    c.execute("""
        SELECT organism_id, organism_name 
        FROM organisms 
        GROUP BY organism_name 
        ORDER BY organism_name
    """)
    organisms = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({'success': True, 'organisms': organisms})

@app.route('/search', methods=['POST'])
def search():
    query_type = request.form.get('query_type')
    search_term = request.form.get('search_term')
    match_type = request.form.get('match_type', 'partial')  # Default to partial matching
    organism_id = request.form.get('organism_id', '')  # Optional organism filter
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    results = []
    
    # Prepare search patterns based on match type
    if match_type == 'exact':
        # For exact matching, don't use wildcards
        search_pattern = search_term
        operator = '='
    else:
        # For partial matching, use wildcards
        search_pattern = f'%{search_term}%'
        operator = 'LIKE'
    
    if query_type == 'gene':
        # Search for gene (ORF) by name, id, or HGNC symbol
        query = f'''
            SELECT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                   COALESCE(hgd.hgnc_approved_symbol, os.orf_name) as display_name, 
                   hgd.hgnc_approved_symbol, 
                   os.orf_name as original_name
            FROM orf_sequence os
            LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            LEFT JOIN human_gene_data hgd ON os.orf_id = hgd.orf_id
            WHERE (os.orf_name {operator} ? OR os.orf_id {operator} ? OR COALESCE(hgd.hgnc_approved_symbol, '') {operator} ?)
        '''
        params = [search_pattern, search_pattern, search_pattern]
        
        # Add organism filter if provided
        if organism_id:
            query += f' AND o.organism_name = (SELECT organism_name FROM organisms WHERE organism_id = ?)'
            params.append(organism_id)
        
        c.execute(query, params)
        
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
    
    # [rest of the function remains the same]
    
    conn.close()
    
    return jsonify({'results': results})

@app.route('/batch_search', methods=['POST'])
def batch_search():
    """Search for multiple genes/ORFs at once"""
    search_terms = request.form.get('search_terms', '')
    match_type = request.form.get('match_type', 'partial')  # Default to partial
    organism_id = request.form.get('organism_id', '')  # Optional organism filter
    
    # Split the input by common separators (newline, comma, semicolon, tab)
    # Remove duplicates while preserving order
    terms = list(dict.fromkeys(term.strip() for term in re.split(r'[\n,;\t]+', search_terms) if term.strip()))
    
    if not terms:
        return jsonify({'success': False, 'message': 'No search terms provided'})
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    results = []
    not_found = []
    
    for term in terms:
        # Define base query based on match type
        if match_type == 'exact':
            # For exact matches
            query = '''
                SELECT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                       COALESCE(hgd.hgnc_approved_symbol, os.orf_name) as display_name, 
                       hgd.hgnc_approved_symbol, 
                       os.orf_name as original_name
                FROM orf_sequence os
                LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                LEFT JOIN human_gene_data hgd ON os.orf_id = hgd.orf_id
                WHERE (os.orf_id = ? OR os.orf_name = ? OR COALESCE(hgd.hgnc_approved_symbol, '') = ?)
            '''
        else:
            # For partial matches
            query = '''
                SELECT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                       COALESCE(hgd.hgnc_approved_symbol, os.orf_name) as display_name, 
                       hgd.hgnc_approved_symbol, 
                       os.orf_name as original_name
                FROM orf_sequence os
                LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                LEFT JOIN human_gene_data hgd ON os.orf_id = hgd.orf_id
                WHERE (os.orf_id LIKE ? OR os.orf_name LIKE ? OR COALESCE(hgd.hgnc_approved_symbol, '') LIKE ?)
            '''
        
        # Set parameters based on match type
        if match_type == 'exact':
            params = [term, term, term]
        else:
            search_pattern = f'%{term}%'
            params = [search_pattern, search_pattern, search_pattern]
            
        # Add organism filter if provided
        if organism_id:
            query += ' AND o.organism_name = (SELECT organism_name FROM organisms WHERE organism_id = ?)'
            params.append(organism_id)
        
        c.execute(query, params)
        matches = [format_database_ids(dict(row)) for row in c.fetchall()]
        
        if matches:
            results.extend(matches)
        else:
            not_found.append(term)
    
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
    
    # Use a set to track unique ORF IDs to prevent duplicate results
    unique_orf_ids = set()
    unique_results = []
    
    for result in results:
        if result['orf_id'] not in unique_orf_ids:
            unique_orf_ids.add(result['orf_id'])
            unique_results.append(result)
    
    conn.close()
    
    return jsonify({
        'success': True, 
        'results': unique_results, 
        'count': len(unique_results),
        'not_found': not_found,
        'terms_searched': len(terms),
        'match_type': match_type,
        'organism_id': organism_id
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
    
    # Get gene examples (including HGNC symbols)
    c.execute('''
        SELECT orf_name 
        FROM orf_sequence 
        ORDER BY RANDOM() 
        LIMIT 3
    ''')
    gene_examples = [row[0] for row in c.fetchall()]
    
    # Add HGNC symbols if available
    c.execute('''
        SELECT hgnc_approved_symbol 
        FROM human_gene_data 
        ORDER BY RANDOM() 
        LIMIT 2
    ''')
    hgnc_examples = [row[0] for row in c.fetchall() if row[0]]
    
    examples['gene'] = gene_examples + hgnc_examples
    
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
