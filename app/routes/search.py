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

@app.route('/api/search_sources')
def get_search_sources():
    """Get all unique source names in the database for search filtering"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check if orf_sources table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orf_sources'")
    sources_table_exists = c.fetchone()
    
    sources = []
    if sources_table_exists:
        # Get distinct source names
        c.execute("""
            SELECT DISTINCT source_name 
            FROM orf_sources 
            ORDER BY source_name
        """)
        sources = [{'source_name': row['source_name']} for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({'success': True, 'sources': sources})

# Check if a particular table exists (to handle optional tables)
def table_exists(conn, table_name):
    c = conn.cursor()
    c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return c.fetchone() is not None

# Add API endpoint to get ORF sources for dropdown
@app.route('/api/orf_sources', methods=['GET'])
def get_orf_sources():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check if orf_sources table exists
    if not table_exists(conn, 'orf_sources'):
        return jsonify({'success': False, 'sources': [], 'message': 'ORF sources table does not exist'})
    
    try:
        c.execute("SELECT DISTINCT source_name FROM orf_sources ORDER BY source_name")
        sources = [dict(row) for row in c.fetchall()]
        return jsonify({'success': True, 'sources': sources})
    except Exception as e:
        return jsonify({'success': False, 'sources': [], 'message': str(e)})
    finally:
        conn.close()

@app.route('/search', methods=['POST'])
def search():
    query_type = request.form.get('query_type')
    search_term = request.form.get('search_term')
    match_type = request.form.get('match_type', 'partial')  # Default to partial matching
    organism_id = request.form.get('organism_id', '')  # Optional organism filter
    source_name = request.form.get('source_name', '')  # Optional source filter
    
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
        # Check if human_gene_data table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='human_gene_data'")
        human_gene_table_exists = c.fetchone()
        
        # Check if orf_sources table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orf_sources'")
        sources_table_exists = c.fetchone()
        
        if human_gene_table_exists:
            query = f'''
                SELECT DISTINCT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                       COALESCE(hgd.hgnc_approved_symbol, os.orf_name) as display_name, 
                       hgd.hgnc_approved_symbol, 
                       os.orf_name as original_name
                FROM orf_sequence os
                LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                LEFT JOIN human_gene_data hgd ON os.orf_id = hgd.orf_id
            '''
            if sources_table_exists and source_name:
                query += ' LEFT JOIN orf_sources src ON os.orf_id = src.orf_id'
            
            query += f' WHERE (os.orf_name {operator} ? OR os.orf_id {operator} ? OR COALESCE(hgd.hgnc_approved_symbol, \'\') {operator} ?)'
        else:
            query = f'''
                SELECT DISTINCT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                       os.orf_name as display_name, 
                       NULL as hgnc_approved_symbol, 
                       os.orf_name as original_name
                FROM orf_sequence os
                LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            '''
            if sources_table_exists and source_name:
                query += ' LEFT JOIN orf_sources src ON os.orf_id = src.orf_id'
            
            query += f' WHERE (os.orf_name {operator} ? OR os.orf_id {operator} ?)'
        
        if human_gene_table_exists:
            params = [search_pattern, search_pattern, search_pattern]
        else:
            params = [search_pattern, search_pattern]
        
        # Add organism filter if provided
        if organism_id:
            query += f' AND os.orf_organism_id = ?'
            params.append(organism_id)
        
        # Add source filter if provided
        if sources_table_exists and source_name:
            query += f' AND src.source_name = ?'
            params.append(source_name)
        
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
            
            # Check if yeast_orf_position table exists and has position_type
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
            yeast_table_exists = c.fetchone()
            
            c.execute("PRAGMA table_info(yeast_orf_position)")
            columns = [column[1] for column in c.fetchall()]
            has_position_type = 'position_type' in columns
            
            yeast_position_data = []
            if yeast_table_exists:
                # Get yeast positions information
                if has_position_type:
                    c.execute('''
                        SELECT id, orf_id, plate, well, position_type 
                        FROM yeast_orf_position
                        WHERE orf_id = ?
                    ''', (orf_id,))
                else:
                    c.execute('''
                        SELECT id, orf_id, plate, well, 'AD' as position_type 
                        FROM yeast_orf_position
                        WHERE orf_id = ?
                    ''', (orf_id,))
                
                yeast_position_data = [dict(row) for row in c.fetchall()]
            result['yeast_positions'] = yeast_position_data
            
            # Check if orf_sources table exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orf_sources'")
            sources_table_exists = c.fetchone()
            
            source_data = []
            if sources_table_exists:
                # Get source information
                c.execute('''
                    SELECT * FROM orf_sources
                    WHERE orf_id = ?
                    ORDER BY submission_date DESC
                ''', (orf_id,))
                
                source_data = [dict(row) for row in c.fetchall()]
            result['sources'] = source_data
    
    # [rest of the function remains the same]
    
    conn.close()
    
    return jsonify({'results': results, 'organism_id': organism_id, 'source_name': source_name})

@app.route('/batch_search', methods=['POST'])
def batch_search():
    """Search for multiple genes/ORFs at once"""
    search_terms = request.form.get('search_terms', '')
    match_type = request.form.get('match_type', 'partial')  # Default to partial
    organism_id = request.form.get('organism_id', '')  # Optional organism filter
    source_name = request.form.get('source_name', '')  # Optional source filter
    
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
        # Check if human_gene_data table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='human_gene_data'")
        human_gene_table_exists = c.fetchone()
        
        # Check if orf_sources table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orf_sources'")
        sources_table_exists = c.fetchone()
        
        if match_type == 'exact':
            # For exact matches
            if human_gene_table_exists:
                query = '''
                    SELECT DISTINCT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                           COALESCE(hgd.hgnc_approved_symbol, os.orf_name) as display_name, 
                           hgd.hgnc_approved_symbol, 
                           os.orf_name as original_name
                    FROM orf_sequence os
                    LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                    LEFT JOIN human_gene_data hgd ON os.orf_id = hgd.orf_id
                '''
                if sources_table_exists and source_name:
                    query += ' LEFT JOIN orf_sources src ON os.orf_id = src.orf_id'
                
                query += ' WHERE (os.orf_id = ? OR os.orf_name = ? OR COALESCE(hgd.hgnc_approved_symbol, \'\') = ?)'
            else:
                query = '''
                    SELECT DISTINCT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                           os.orf_name as display_name, 
                           NULL as hgnc_approved_symbol, 
                           os.orf_name as original_name
                    FROM orf_sequence os
                    LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                '''
                if sources_table_exists and source_name:
                    query += ' LEFT JOIN orf_sources src ON os.orf_id = src.orf_id'
                
                query += ' WHERE (os.orf_id = ? OR os.orf_name = ?)'
        else:
            # For partial matches
            if human_gene_table_exists:
                query = '''
                    SELECT DISTINCT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                           COALESCE(hgd.hgnc_approved_symbol, os.orf_name) as display_name, 
                           hgd.hgnc_approved_symbol, 
                           os.orf_name as original_name
                    FROM orf_sequence os
                    LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                    LEFT JOIN human_gene_data hgd ON os.orf_id = hgd.orf_id
                '''
                if sources_table_exists and source_name:
                    query += ' LEFT JOIN orf_sources src ON os.orf_id = src.orf_id'
                
                query += ' WHERE (os.orf_id LIKE ? OR os.orf_name LIKE ? OR COALESCE(hgd.hgnc_approved_symbol, \'\') LIKE ?)'
            else:
                query = '''
                    SELECT DISTINCT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                           os.orf_name as display_name, 
                           NULL as hgnc_approved_symbol, 
                           os.orf_name as original_name
                    FROM orf_sequence os
                    LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                '''
                if sources_table_exists and source_name:
                    query += ' LEFT JOIN orf_sources src ON os.orf_id = src.orf_id'
                
                query += ' WHERE (os.orf_id LIKE ? OR os.orf_name LIKE ?)'
        
        # Set parameters based on match type and table existence
        if match_type == 'exact':
            if human_gene_table_exists:
                params = [term, term, term]
            else:
                params = [term, term]
        else:
            search_pattern = f'%{term}%'
            if human_gene_table_exists:
                params = [search_pattern, search_pattern, search_pattern]
            else:
                params = [search_pattern, search_pattern]
        
        # Add organism filter if provided
        if organism_id:
            query += ' AND os.orf_organism_id = ?'
            params.append(organism_id)
        
        # Add source filter if provided
        if sources_table_exists and source_name:
            query += ' AND src.source_name = ?'
            params.append(source_name)
        
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
        
        # Check if yeast_orf_position table exists and has position_type
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
        yeast_table_exists = c.fetchone()
        
        c.execute("PRAGMA table_info(yeast_orf_position)")
        columns = [column[1] for column in c.fetchall()]
        has_position_type = 'position_type' in columns
        
        yeast_position_data = []
        if yeast_table_exists:
            # Get yeast positions information
            if has_position_type:
                c.execute('''
                    SELECT id, orf_id, plate, well, position_type 
                    FROM yeast_orf_position
                    WHERE orf_id = ?
                ''', (orf_id,))
            else:
                c.execute('''
                    SELECT id, orf_id, plate, well, 'AD' as position_type 
                    FROM yeast_orf_position
                    WHERE orf_id = ?
                ''', (orf_id,))
            
            yeast_position_data = [dict(row) for row in c.fetchall()]
        result['yeast_positions'] = yeast_position_data
        
        # Check if orf_sources table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orf_sources'")
        sources_table_exists = c.fetchone()
        
        source_data = []
        if sources_table_exists:
            # Get source information
            c.execute('''
                SELECT * FROM orf_sources
                WHERE orf_id = ?
                ORDER BY submission_date DESC
            ''', (orf_id,))
            
            source_data = [dict(row) for row in c.fetchall()]
        result['sources'] = source_data
    
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
        'organism_id': organism_id,
        'source_name': source_name
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
    
    # Check if human_gene_data table exists before querying
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='human_gene_data'")
    human_gene_table_exists = c.fetchone()
    
    hgnc_examples = []
    if human_gene_table_exists:
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

@app.route('/api/search', methods=['GET'])
def api_search():
    """API endpoint for search functionality"""
    query_type = request.args.get('type')
    search_term = request.args.get('query')
    match_type = request.args.get('match', 'partial')  # Default to partial matching
    organism_id = request.args.get('organism', '')  # Optional organism filter
    source_name = request.args.get('source', '')  # Optional source filter
    
    # Debug logging
    print(f"API Search: type={query_type}, query={search_term}, match={match_type}, organism={organism_id}, source={source_name}")
    
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
    
    try:
        if query_type == 'gene' or query_type == 'orf':
            # Search for gene (ORF) by name, id, or HGNC symbol
            # Check if human_gene_data table exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='human_gene_data'")
            human_gene_table_exists = c.fetchone()
            
            # Check if orf_sources table exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orf_sources'")
            sources_table_exists = c.fetchone()
            
            if human_gene_table_exists:
                query = f'''
                    SELECT DISTINCT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                           COALESCE(hgd.hgnc_approved_symbol, os.orf_name) as display_name, 
                           hgd.hgnc_approved_symbol, 
                           os.orf_name as original_name
                    FROM orf_sequence os
                    LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                    LEFT JOIN human_gene_data hgd ON os.orf_id = hgd.orf_id
                '''
                if sources_table_exists and source_name:
                    query += ' LEFT JOIN orf_sources src ON os.orf_id = src.orf_id'
                
                query += f' WHERE (os.orf_name {operator} ? OR os.orf_id {operator} ? OR COALESCE(hgd.hgnc_approved_symbol, \'\') {operator} ?)'
                params = [search_pattern, search_pattern, search_pattern]
            else:
                query = f'''
                    SELECT DISTINCT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
                           os.orf_name as display_name, 
                           NULL as hgnc_approved_symbol, 
                           os.orf_name as original_name
                    FROM orf_sequence os
                    LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                '''
                if sources_table_exists and source_name:
                    query += ' LEFT JOIN orf_sources src ON os.orf_id = src.orf_id'
                
                query += f' WHERE (os.orf_name {operator} ? OR os.orf_id {operator} ?)'
                params = [search_pattern, search_pattern]
            
            # Add organism filter if provided
            if organism_id:
                query += f' AND os.orf_organism_id = ?'
                params.append(organism_id)
            
            # Add source filter if provided
            if sources_table_exists and source_name:
                query += f' AND src.source_name = ?'
                params.append(source_name)
            
            c.execute(query, params)
            
            # Only use format_database_ids for gene/orf search
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
                
                # Check if yeast_orf_position table exists and has position_type
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
                yeast_table_exists = c.fetchone()
                
                yeast_position_data = []
                if yeast_table_exists:
                    # Check if position_type column exists
                    c.execute("PRAGMA table_info(yeast_orf_position)")
                    columns = [column[1] for column in c.fetchall()]
                    has_position_type = 'position_type' in columns
                    
                    # Get yeast positions information
                    if has_position_type:
                        c.execute('''
                            SELECT id, orf_id, plate, well, position_type 
                            FROM yeast_orf_position
                            WHERE orf_id = ?
                        ''', (orf_id,))
                    else:
                        c.execute('''
                            SELECT id, orf_id, plate, well, 'AD' as position_type 
                            FROM yeast_orf_position
                            WHERE orf_id = ?
                        ''', (orf_id,))
                    
                    yeast_position_data = [dict(row) for row in c.fetchall()]
                result['yeast_positions'] = yeast_position_data
                
                # Check if orf_sources table exists
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orf_sources'")
                sources_table_exists = c.fetchone()
                
                source_data = []
                if sources_table_exists:
                    # Get source information
                    c.execute('''
                        SELECT * FROM orf_sources
                        WHERE orf_id = ?
                        ORDER BY submission_date DESC
                    ''', (orf_id,))
                    
                    source_data = [dict(row) for row in c.fetchall()]
                result['sources'] = source_data
        
        # [rest of the function remains the same]
        
        # Use a set to track unique IDs to prevent duplicate results
        unique_ids = set()
        unique_results = []
        
        for result in results:
            # Use the appropriate ID field based on query type
            if query_type in ['plasmid', 'organism']:
                id_field = f"{query_type}_id"
            else:
                id_field = 'orf_id'
            
            if id_field in result and result[id_field] not in unique_ids:
                unique_ids.add(result[id_field])
                unique_results.append(result)
        
        conn.close()
        
        print(f"Final results count: {len(unique_results)}")
        
        return jsonify({
            'success': True, 
            'results': unique_results, 
            'count': len(unique_results),
            'organism_id': organism_id,
            'source_name': source_name
        })
    
    except Exception as e:
        conn.close()
        import traceback
        print(f"Error in API search: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }), 500
