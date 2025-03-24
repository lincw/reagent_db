from flask import render_template, jsonify, request
import sqlite3
import os
from app import app, DB_PATH

@app.route('/view/orf/<int:orf_id>')
def view_orf(orf_id):
    """View details for a specific ORF"""
    app.logger.info(f"Viewing ORF with ID: {orf_id}, DB Path: {DB_PATH}")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        app.logger.error(f"Database file not found at {DB_PATH}")
        return render_template('error.html', message=f'Database file not found at {DB_PATH}')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get ORF details
        c.execute('''
            SELECT os.*, o.organism_name, o.organism_genus, o.organism_species, o.organism_strain
            FROM orf_sequence os
            LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            WHERE os.orf_id = ?
        ''', (orf_id,))
        
        orf_data = c.fetchone()
        
        if not orf_data:
            conn.close()
            return render_template('error.html', message='ORF not found')
        
        orf_data = dict(orf_data)
        
        # Get position information
        c.execute('''
            SELECT op.*, f.freezer_location, f.freezer_temp, p.plasmid_name, p.plasmid_type
            FROM orf_position op
            LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
            LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
            WHERE op.orf_id = ?
        ''', (orf_id,))
        
        positions = [dict(row) for row in c.fetchall()]
        orf_data['positions'] = positions
        
        conn.close()
        return render_template('detail_orf.html', data=orf_data)
    
    except Exception as e:
        app.logger.error(f"Error viewing ORF {orf_id}: {str(e)}")
        return render_template('error.html', message=f'Error retrieving ORF data: {str(e)}')


@app.route('/view/plasmid/<int:plasmid_id>')
def view_plasmid(plasmid_id):
    """View details for a specific plasmid"""
    app.logger.info(f"Viewing plasmid with ID: {plasmid_id}, DB Path: {DB_PATH}")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        app.logger.error(f"Database file not found at {DB_PATH}")
        return render_template('error.html', message=f'Database file not found at {DB_PATH}')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get plasmid details
        c.execute('''
            SELECT p.*
            FROM plasmid p
            WHERE p.plasmid_id = ?
        ''', (plasmid_id,))
        
        plasmid_data = c.fetchone()
        
        if not plasmid_data:
            conn.close()
            return render_template('error.html', message='Plasmid not found')
        
        plasmid_data = dict(plasmid_data)
        
        # Get associated ORFs
        c.execute('''
            SELECT os.orf_id, os.orf_name, os.orf_annotation, op.plate, op.well, 
                   f.freezer_location, f.freezer_id
            FROM orf_position op
            JOIN orf_sequence os ON op.orf_id = os.orf_id
            LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
            WHERE op.plasmid_id = ?
        ''', (plasmid_id,))
        
        orfs = [dict(row) for row in c.fetchall()]
        plasmid_data['orfs'] = orfs
        
        conn.close()
        return render_template('detail_plasmid.html', data=plasmid_data)
    
    except Exception as e:
        app.logger.error(f"Error viewing plasmid {plasmid_id}: {str(e)}")
        return render_template('error.html', message=f'Error retrieving plasmid data: {str(e)}')


@app.route('/view/freezer/<int:freezer_id>')
def view_freezer(freezer_id):
    """View details for a specific freezer location"""
    app.logger.info(f"Viewing freezer with ID: {freezer_id}, DB Path: {DB_PATH}")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        app.logger.error(f"Database file not found at {DB_PATH}")
        return render_template('error.html', message=f'Database file not found at {DB_PATH}')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get freezer details
        c.execute('''
            SELECT f.*
            FROM freezer f
            WHERE f.freezer_id = ?
        ''', (freezer_id,))
        
        freezer_data = c.fetchone()
        
        if not freezer_data:
            conn.close()
            return render_template('error.html', message='Freezer not found')
        
        freezer_data = dict(freezer_data)
        
        # Get contents of this freezer
        c.execute('''
            SELECT op.plate, op.well, os.orf_id, os.orf_name, p.plasmid_id, p.plasmid_name
            FROM orf_position op
            LEFT JOIN orf_sequence os ON op.orf_id = os.orf_id
            LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
            WHERE op.freezer_id = ?
            ORDER BY op.plate, op.well
        ''', (freezer_id,))
        
        contents = [dict(row) for row in c.fetchall()]
        freezer_data['contents'] = contents
        
        conn.close()
        return render_template('detail_freezer.html', data=freezer_data)
    
    except Exception as e:
        app.logger.error(f"Error viewing freezer {freezer_id}: {str(e)}")
        return render_template('error.html', message=f'Error retrieving freezer data: {str(e)}')


@app.route('/view/organism/<int:organism_id>')
def view_organism(organism_id):
    """View details for a specific organism"""
    app.logger.info(f"Viewing organism with ID: {organism_id}, DB Path: {DB_PATH}")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        app.logger.error(f"Database file not found at {DB_PATH}")
        return render_template('error.html', message=f'Database file not found at {DB_PATH}')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get organism details
        c.execute('''
            SELECT o.*
            FROM organisms o
            WHERE o.organism_id = ?
        ''', (organism_id,))
        
        organism_data = c.fetchone()
        
        if not organism_data:
            conn.close()
            return render_template('error.html', message='Organism not found')
        
        organism_data = dict(organism_data)
        
        # Get ORFs for this organism
        c.execute('''
            SELECT os.orf_id, os.orf_name, os.orf_annotation, os.orf_length_bp
            FROM orf_sequence os
            WHERE os.orf_organism_id = ?
        ''', (organism_id,))
        
        orfs = [dict(row) for row in c.fetchall()]
        organism_data['orfs'] = orfs
        
        conn.close()
        return render_template('detail_organism.html', data=organism_data)
    
    except Exception as e:
        app.logger.error(f"Error viewing organism {organism_id}: {str(e)}")
        return render_template('error.html', message=f'Error retrieving organism data: {str(e)}')


@app.route('/api/detail/orf/<int:orf_id>')
def api_detail_orf(orf_id):
    """API endpoint for ORF details"""
    app.logger.info(f"API request for ORF with ID: {orf_id}, DB Path: {DB_PATH}")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        app.logger.error(f"Database file not found at {DB_PATH}")
        return jsonify({'success': False, 'message': f'Database file not found at {DB_PATH}'})
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get ORF details
        c.execute('''
            SELECT os.*, o.organism_name, o.organism_genus, o.organism_species
            FROM orf_sequence os
            LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            WHERE os.orf_id = ?
        ''', (orf_id,))
        
        orf_data = c.fetchone()
        
        if not orf_data:
            conn.close()
            return jsonify({'success': False, 'message': 'ORF not found'})
        
        orf_data = dict(orf_data)
        
        # Get position information
        c.execute('''
            SELECT op.*, f.freezer_location, p.plasmid_name
            FROM orf_position op
            LEFT JOIN freezer f ON op.freezer_id = f.freezer_id
            LEFT JOIN plasmid p ON op.plasmid_id = p.plasmid_id
            WHERE op.orf_id = ?
        ''', (orf_id,))
        
        positions = [dict(row) for row in c.fetchall()]
        orf_data['positions'] = positions
        
        conn.close()
        return jsonify({'success': True, 'data': orf_data})
    
    except Exception as e:
        app.logger.error(f"API error for ORF {orf_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error retrieving ORF data: {str(e)}'})
