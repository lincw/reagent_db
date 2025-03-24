from flask import render_template, request, jsonify
import sqlite3
from app import app, DB_PATH

@app.route('/add', methods=['GET'])
def add_entry():
    return render_template('add_entry.html')

@app.route('/add_form', methods=['POST'])
def add_form_entry():
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
