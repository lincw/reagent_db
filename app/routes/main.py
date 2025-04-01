from flask import render_template, jsonify
import sqlite3

from app import app, DB_PATH

def get_database_stats():
    """Get statistics about the database collections"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # Count ORF sequences
    cursor.execute('SELECT COUNT(*) FROM orf_sequence')
    stats['orf_sequences'] = cursor.fetchone()[0]
    
    # Include these for backward compatibility
    cursor.execute('SELECT COUNT(*) FROM orf_position')
    stats['orf_positions'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT orf_id) FROM orf_position')
    stats['unique_positioned_orfs'] = cursor.fetchone()[0]
    
    # Count plasmids
    cursor.execute('SELECT COUNT(*) FROM plasmid')
    stats['plasmids'] = cursor.fetchone()[0]
    
    # Count unique organisms
    cursor.execute('SELECT COUNT(DISTINCT organism_name) FROM organisms')
    stats['organisms'] = cursor.fetchone()[0]
    
    # Count unique freezers
    cursor.execute('SELECT COUNT(DISTINCT freezer_location) FROM freezer')
    stats['freezers'] = cursor.fetchone()[0]
    
    # Get last update timestamp
    cursor.execute("SELECT datetime('now')")
    stats['current_time'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

@app.route('/')
def index():
    stats = get_database_stats()
    return render_template('index.html', stats=stats)

@app.route('/batch_search')
def batch_search_page():
    """Render the batch search page"""
    return render_template('batch_search.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint to get current database statistics"""
    return jsonify(get_database_stats())

@app.route('/gene-nomenclature')
def gene_nomenclature():
    """Render the gene nomenclature explanation page"""
    return render_template('gene_nomenclature.html')
