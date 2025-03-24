from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import csv
from datetime import datetime

app = Flask(__name__)

# Database path - using absolute path to avoid issues
current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, 'reagent_db.sqlite')

@app.route('/')
def index():
    return render_template('index.html')

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
            SELECT os.*, o.organism_name
            FROM orf_sequence os
            LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            WHERE os.orf_name LIKE ? OR os.orf_annotation LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        results = [dict(row) for row in c.fetchall()]
        
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

@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if request.method == 'GET':
        return render_template('add_entry.html')
    
    # Handle form submission for adding entries
    entry_type = request.form.get('entry_type')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        if entry_type == 'orf':
            # Add new ORF entry
            orf_id = request.form.get('orf_id')
            orf_name = request.form.get('orf_name')
            orf_annotation = request.form.get('orf_annotation')
            orf_sequence = request.form.get('orf_sequence')
            orf_with_stop = 1 if request.form.get('orf_with_stop') == 'on' else 0
            orf_open = 1 if request.form.get('orf_open') == 'on' else 0
            orf_organism_id = request.form.get('orf_organism_id')
            orf_length_bp = request.form.get('orf_length_bp', 0)
            orf_entrez_id = request.form.get('orf_entrez_id', '')
            orf_ensembl_id = request.form.get('orf_ensembl_id', '')
            orf_uniprot_id = request.form.get('orf_uniprot_id', '')
            orf_ref_url = request.form.get('orf_ref_url', '')
            
            # Insert ORF sequence
            c.execute('''
                INSERT INTO orf_sequence (
                    orf_id, orf_name, orf_annotation, orf_sequence, orf_with_stop, orf_open,
                    orf_organism_id, orf_length_bp, orf_entrez_id, orf_ensembl_id, orf_uniprot_id, orf_ref_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                orf_id, orf_name, orf_annotation, orf_sequence, orf_with_stop, orf_open,
                orf_organism_id, orf_length_bp, orf_entrez_id, orf_ensembl_id, orf_uniprot_id, orf_ref_url
            ))
            
            # Insert ORF position if provided
            plate = request.form.get('plate', '')
            well = request.form.get('well', '')
            freezer_id = request.form.get('freezer_id', '')
            plasmid_id = request.form.get('plasmid_id', '')
            orf_create_date = request.form.get('orf_create_date', '')
            
            if plate and well:
                c.execute('''
                    INSERT INTO orf_position (
                        orf_id, plate, well, freezer_id, plasmid_id, orf_create_date
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    orf_id, plate, well, freezer_id, plasmid_id, orf_create_date
                ))
        
        elif entry_type == 'plasmid':
            # Add new plasmid entry
            plasmid_id = request.form.get('plasmid_id')
            plasmid_name = request.form.get('plasmid_name')
            plasmid_type = request.form.get('plasmid_type', '')
            plasmid_express_organism = request.form.get('plasmid_express_organism', '')
            plasmid_description = request.form.get('plasmid_description', '')
            
            c.execute('''
                INSERT INTO plasmid (
                    plasmid_id, plasmid_name, plasmid_type, plasmid_express_organism, plasmid_description
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                plasmid_id, plasmid_name, plasmid_type, plasmid_express_organism, plasmid_description
            ))
        
        elif entry_type == 'organism':
            # Add new organism entry
            organism_id = request.form.get('organism_id')
            organism_name = request.form.get('organism_name')
            organism_genus = request.form.get('organism_genus', '')
            organism_species = request.form.get('organism_species', '')
            organism_strain = request.form.get('organism_strain', '')
            
            c.execute('''
                INSERT INTO organisms (
                    organism_id, organism_name, organism_genus, organism_species, organism_strain
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                organism_id, organism_name, organism_genus, organism_species, organism_strain
            ))
        
        elif entry_type == 'freezer':
            # Add new freezer entry
            freezer_id = request.form.get('freezer_id')
            freezer_location = request.form.get('freezer_location')
            freezer_condition = request.form.get('freezer_condition', '')
            freezer_date = request.form.get('freezer_date', '')
            
            c.execute('''
                INSERT INTO freezer (
                    freezer_id, freezer_location, freezer_condition, freezer_date
                ) VALUES (?, ?, ?, ?)
            ''', (
                freezer_id, freezer_location, freezer_condition, freezer_date
            ))
        
        conn.commit()
        message = f'{entry_type.upper()} entry added successfully'
        success = True
    except Exception as e:
        conn.rollback()
        message = f'Error: {str(e)}'
        success = False
    finally:
        conn.close()
    
    return jsonify({'success': success, 'message': message})

@app.route('/export', methods=['GET'])
def export_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Create export directory within the project for better permission management
    export_dir = os.path.join(current_dir, 'exports')
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    try:
        # Export freezer data
        c.execute('SELECT * FROM freezer')
        freezer_data = c.fetchall()
        with open(os.path.join(export_dir, 'freezer.csv'), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['freezer_id', 'freezer_location', 'freezer_condition', 'freezer_date'])
            for row in freezer_data:
                writer.writerow(row)
        
        # Export organisms data
        c.execute('SELECT * FROM organisms')
        organisms_data = c.fetchall()
        with open(os.path.join(export_dir, 'organisms.csv'), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['organism_id', 'organism_name', 'organism_genus', 'organism_species', 'organism_strain'])
            for row in organisms_data:
                writer.writerow(row)
        
        # Export plasmid data
        c.execute('SELECT * FROM plasmid')
        plasmid_data = c.fetchall()
        with open(os.path.join(export_dir, 'plasmid.csv'), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['plasmid_id', 'plasmid_name', 'plasmid_type', 'plasmid_express_organism', 'plasmid_description'])
            for row in plasmid_data:
                writer.writerow(row)
        
        # Export orf_sequence data
        c.execute('SELECT * FROM orf_sequence')
        orf_sequence_data = c.fetchall()
        with open(os.path.join(export_dir, 'orf_sequence.csv'), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['orf_id', 'orf_name', 'orf_annotation', 'orf_sequence', 'orf_with_stop', 
                             'orf_open', 'orf_organism_id', 'orf_length_bp', 'orf_entrez_id', 
                             'orf_ensembl_id', 'orf_uniprot_id', 'orf_ref_url'])
            for row in orf_sequence_data:
                writer.writerow(row)
        
        # Export orf_position data (excluding the id column)
        c.execute('SELECT orf_id, plate, well, freezer_id, plasmid_id, orf_create_date FROM orf_position')
        orf_position_data = c.fetchall()
        with open(os.path.join(export_dir, 'orf_position.csv'), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['orf_id', 'plate', 'well', 'freezer_id', 'plasmid_id', 'orf_create_date'])
            for row in orf_position_data:
                writer.writerow(row)
        
        success = True
        message = f'Data exported successfully to {export_dir}'
    except Exception as e:
        success = False
        message = f'Error exporting data: {str(e)}'
    finally:
        conn.close()
    
    return jsonify({'success': success, 'message': message})

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

if __name__ == '__main__':
    # Create the exports directory if it doesn't exist
    exports_dir = os.path.join(current_dir, 'exports')
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
        
    app.run(debug=True)
