from flask import jsonify
import sqlite3
from app import app, DB_PATH

@app.route('/api/organisms', methods=['GET'])
def get_organisms():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM organisms')
    organisms = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({'organisms': organisms})

@app.route('/api/plasmids', methods=['GET'])
def get_plasmids():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM plasmid')
    plasmids = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({'plasmids': plasmids})

@app.route('/api/freezers', methods=['GET'])
def get_freezers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM freezer')
    freezers = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({'freezers': freezers})

@app.route('/api/orfs', methods=['GET'])
def get_orfs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT orf_id, orf_name, orf_annotation FROM orf_sequence')
    orfs = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({'orfs': orfs})

@app.route('/api/search_examples', methods=['GET'])
def get_search_examples():
    """Get example search terms from the database to suggest to users"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    examples = {
        'gene': [],
        'plasmid': [],
        'location': [],
        'organism': []
    }
    
    try:
        # Get gene examples (ORF names and annotations)
        c.execute('SELECT orf_name, orf_annotation FROM orf_sequence LIMIT 10')
        gene_rows = c.fetchall()
        examples['gene'] = [row['orf_name'] for row in gene_rows if row['orf_name']]
        
        # Get plasmid examples
        c.execute('SELECT plasmid_name FROM plasmid LIMIT 10')
        plasmid_rows = c.fetchall()
        examples['plasmid'] = [row['plasmid_name'] for row in plasmid_rows if row['plasmid_name']]
        
        # Get location examples (plate-well format)
        c.execute('SELECT plate, well FROM orf_position LIMIT 10')
        location_rows = c.fetchall()
        examples['location'] = [f"{row['plate']}-{row['well']}" for row in location_rows if row['plate'] and row['well']]
        
        # Get organism examples
        c.execute('SELECT organism_name FROM organisms LIMIT 10')
        organism_rows = c.fetchall()
        examples['organism'] = [row['organism_name'] for row in organism_rows if row['organism_name']]
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()
    
    return jsonify({'success': True, 'examples': examples})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get counts for each table
    c.execute('SELECT COUNT(*) FROM freezer')
    freezer_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM organisms')
    organism_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM plasmid')
    plasmid_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM orf_sequence')
    orf_sequence_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM orf_position')
    orf_position_count = c.fetchone()[0]
    
    conn.close()
    
    stats = {
        'freezers': freezer_count,
        'organisms': organism_count,
        'plasmids': plasmid_count,
        'orf_sequences': orf_sequence_count,
        'orf_positions': orf_position_count
    }
    
    return jsonify({'stats': stats})
