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

# Note: The search_examples and stats endpoints have been moved to other files
# to avoid route conflicts:
# - get_search_examples() is now in search.py
# - api_stats() is now in main.py
