from flask import render_template, jsonify
import sqlite3
from app import app, DB_PATH
from app.utils import format_database_ids

@app.route('/view/orf/<orf_id>')
def view_orf(orf_id):
    """View details for a specific ORF"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get ORF details - use string comparison for text IDs
    c.execute('''
        SELECT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain,
               hgd.hgnc_approved_symbol as hgnc_symbol
        FROM orf_sequence os
        LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
        LEFT JOIN human_gene_data hgd ON os.orf_id = hgd.orf_id
        WHERE os.orf_id = ?
    ''', (str(orf_id),))
    
    orf_data = c.fetchone()
    
    if not orf_data:
        conn.close()
        return render_template('error.html', message='ORF not found')
    
    orf_data = format_database_ids(dict(orf_data))
    
    # Get position information - ensure string comparison for text IDs
    c.execute('''
        SELECT op.*, f.freezer_location, f.freezer_condition, p.plasmid_name, p.plasmid_type
        FROM orf_position op
        LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
        LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
        WHERE op.orf_id = ?
    ''', (str(orf_id),))
    
    positions = [dict(row) for row in c.fetchall()]
    orf_data['positions'] = positions
    
    conn.close()
    return render_template('detail_orf.html', data=orf_data)


@app.route('/view/plasmid/<plasmid_id>')
def view_plasmid(plasmid_id):
    """View details for a specific plasmid"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get plasmid details - ensure string comparison for text IDs
    c.execute('''
        SELECT p.*
        FROM plasmid p
        WHERE p.plasmid_id = ?
    ''', (str(plasmid_id),))
    
    plasmid_data = c.fetchone()
    
    if not plasmid_data:
        conn.close()
        return render_template('error.html', message='Plasmid not found')
    
    plasmid_data = dict(plasmid_data)
    
    # Get associated ORFs - ensure string comparison for text IDs
    c.execute('''
        SELECT os.orf_id, os.orf_name, os.orf_annotation, op.plate, op.well, 
               f.freezer_location, f.freezer_id
        FROM orf_position op
        JOIN orf_sequence os ON op.orf_id = os.orf_id
        LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
        WHERE op.plasmid_id = ?
    ''', (str(plasmid_id),))
    
    orfs = [dict(row) for row in c.fetchall()]
    plasmid_data['orfs'] = orfs
    
    conn.close()
    return render_template('detail_plasmid.html', data=plasmid_data)


@app.route('/view/freezer/<freezer_id>')
def view_freezer(freezer_id):
    """View details for a specific freezer location"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get freezer details - ensure string comparison for text IDs
    c.execute('''
        SELECT f.*
        FROM freezer f
        WHERE f.freezer_id = ?
    ''', (str(freezer_id),))
    
    freezer_data = c.fetchone()
    
    if not freezer_data:
        conn.close()
        return render_template('error.html', message='Freezer not found')
    
    freezer_data = dict(freezer_data)
    
    # Get contents of this freezer - ensure string comparison for text IDs
    c.execute('''
        SELECT op.plate, op.well, os.orf_id, os.orf_name, p.plasmid_id, p.plasmid_name
        FROM orf_position op
        LEFT JOIN orf_sequence os ON op.orf_id = os.orf_id
        LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
        WHERE op.freezer_id = ?
        ORDER BY op.plate, op.well
    ''', (str(freezer_id),))
    
    contents = [dict(row) for row in c.fetchall()]
    freezer_data['contents'] = contents
    
    conn.close()
    return render_template('detail_freezer.html', data=freezer_data)


@app.route('/view/organism/<organism_id>')
def view_organism(organism_id):
    """View details for a specific organism"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get organism details - ensure string comparison for text IDs
    c.execute('''
        SELECT o.*
        FROM organisms o
        WHERE o.organism_id = ?
    ''', (str(organism_id),))
    
    organism_data = c.fetchone()
    
    if not organism_data:
        conn.close()
        return render_template('error.html', message='Organism not found')
    
    organism_data = dict(organism_data)
    
    # Get ORFs for this organism - ensure string comparison for text IDs
    c.execute('''
        SELECT os.orf_id, os.orf_name, os.orf_annotation, os.orf_length_bp
        FROM orf_sequence os
        WHERE os.orf_organism_id = ?
    ''', (str(organism_id),))
    
    orfs = [dict(row) for row in c.fetchall()]
    organism_data['orfs'] = orfs
    
    conn.close()
    return render_template('detail_organism.html', data=organism_data)


@app.route('/api/detail/orf/<orf_id>')
def api_detail_orf(orf_id):
    """API endpoint for ORF details"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get ORF details - ensure string comparison for text IDs
    c.execute('''
        SELECT os.*, o.organism_name, o.organism_genus, o.organism_species,
               hgd.hgnc_approved_symbol as hgnc_symbol
        FROM orf_sequence os
        LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
        LEFT JOIN human_gene_data hgd ON os.orf_id = hgd.orf_id
        WHERE os.orf_id = ?
    ''', (str(orf_id),))
    
    orf_data = c.fetchone()
    
    if not orf_data:
        conn.close()
        return jsonify({'success': False, 'message': 'ORF not found'})
    
    orf_data = dict(orf_data)
    
    # Get position information - ensure string comparison for text IDs
    c.execute('''
        SELECT op.*, f.freezer_location, p.plasmid_name
        FROM orf_position op
        LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
        LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
        WHERE op.orf_id = ?
    ''', (str(orf_id),))
    
    positions = [dict(row) for row in c.fetchall()]
    orf_data['positions'] = positions
    
    conn.close()
    return jsonify({'success': True, 'data': orf_data})
