from flask import render_template, request, jsonify, send_from_directory
import sqlite3
import os
import csv
import pandas as pd
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename

from app import app, DB_PATH
from app.utils import allowed_file, create_template_dataframe

def map_column_names(df, import_type):
    """Map alternate column names to expected column names"""
    if import_type == 'orf_sequence' or import_type == 'unified_position':
        # Define mapping of commonly used alternate names
        column_mapping = {
            # Common alternate names for orf_id
            'gene_id': 'orf_id',
            'gene': 'orf_id',
            'id': 'orf_id',
            
            # Common alternate names for orf_name
            'gene_name': 'orf_name',
            'gene_symbol': 'orf_name', 
            'entrez_gene_symbol': 'orf_name',
            'name': 'orf_name',
            
            # Common alternate names for orf_sequence
            'sequence': 'orf_sequence',
            'dna_sequence': 'orf_sequence',
            'nucleotide_sequence': 'orf_sequence',
            'seq': 'orf_sequence',
            
            # Common alternate names for orf_organism_id
            'organism_id': 'orf_organism_id',
            'organism': 'orf_organism_id',
            'taxid': 'orf_organism_id',
            'species_id': 'orf_organism_id',
            
            # Common alternate names for boolean fields
            'stop': 'orf_with_stop',
            'with_stop': 'orf_with_stop',
            'has_stop': 'orf_with_stop',
            'is_open': 'orf_open',
            'open': 'orf_open',
            
            # Common alternate names for other fields
            'length': 'orf_length_bp',
            'bp': 'orf_length_bp',
            'entrez_id': 'orf_entrez_id',
            'ensembl_id': 'orf_ensembl_id',
            'uniprot_id': 'orf_uniprot_id',
            'ref_url': 'orf_ref_url',
            'reference_url': 'orf_ref_url',
            'url': 'orf_ref_url',
            'annotation': 'orf_annotation',
            
            # Position-related mappings
            'is_entry': 'entry_position',
            'entry': 'entry_position',
            'is_ad': 'yeast_ad_position',
            'ad': 'yeast_ad_position',
            'activation_domain': 'yeast_ad_position',
            'is_db': 'yeast_db_position',
            'db': 'yeast_db_position',
            'dna_binding': 'yeast_db_position',
            'binding_domain': 'yeast_db_position',
            
            # Source-related mappings
            'source': 'source_name',
            'lab': 'source_name',
            'provider': 'source_name',
            'details': 'source_details',
            'source_notes': 'source_details',
            'description': 'source_details'
        }

        # Create a copy of the dataframe
        new_df = df.copy()
        
        # Rename columns according to mapping
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in column_mapping:
                print(f"Mapping column '{col}' to '{column_mapping[col_lower]}'")
                new_df = new_df.rename(columns={col: column_mapping[col_lower]})
        
        return new_df
    
    # Add mappings for other import types if needed
    return df

@app.route('/import', methods=['GET'])
def import_form():
    return render_template('import.html')

@app.route('/import_file', methods=['POST'])
def import_file():
    """Handle file uploads for data import"""
    import_type = request.form.get('import_type')
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Create upload directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the uploaded file
        file.save(file_path)
        
        try:
            # Handle different import types
            if import_type == 'orf_sequence':
                success, message = import_orf_sequences(file_path)
            elif import_type == 'orf_position':
                success, message = import_orf_positions(file_path)
            elif import_type == 'yeast_orf_position':
                success, message = import_yeast_orf_positions(file_path)
            elif import_type == 'unified_position':
                # Call the new unified positions import
                success, message = import_unified_positions_handler(file_path)
            elif import_type == 'orf_sources':
                success, message = import_orf_sources(file_path)
            elif import_type == 'plasmid':
                success, message = import_plasmids(file_path)
            elif import_type == 'organism':
                success, message = import_organisms(file_path)
            elif import_type == 'freezer':
                success, message = import_freezers(file_path)
            else:
                return jsonify({'success': False, 'message': f'Unknown import type: {import_type}'})
            
            return jsonify({'success': success, 'message': message})
            
        except Exception as e:
            app.logger.error(f"Error during import: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({'success': False, 'message': f'Error during import: {str(e)}'})
        
        finally:
            # Clean up the uploaded file
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    return jsonify({'success': False, 'message': 'Invalid file format. Please upload a CSV or Excel file.'})

def import_unified_positions_handler(file_path):
    """Import unified ORF data (sequences, positions, sources, and related entities)"""
    # Load the file as a DataFrame
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            return False, "Unsupported file format. Please upload a CSV or Excel file."
        
        # Apply column name mapping to handle alternate column names
        df = map_column_names(df, 'unified_position')
        
        # Validate at least minimal required columns
        required_columns = ['orf_id', 'orf_name', 'source_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Start a transaction
        c.execute('BEGIN TRANSACTION')
        
        # Processing stats
        stats = {
            'sequences': 0,
            'entry_positions': 0,
            'yeast_ad_positions': 0,
            'yeast_db_positions': 0,
            'sources': 0,
            'organisms': 0,
            'freezers': 0,
            'plasmids': 0,
            'errors': []
        }
        
        try:
            # Process each row
            for idx, row in df.iterrows():
                # Skip template header rows
                if row['orf_id'] == 'Required' or row['orf_id'] == 'ORF999' or \
                   str(row['orf_id']).lower() == 'orf_id':
                    continue
                
                orf_id = row['orf_id']
                
                # Verify each required field is present and not null
                if pd.isna(row['orf_id']) or pd.isna(row['orf_name']):
                    stats['errors'].append(f"Row {idx + 2}: Missing required value (orf_id, orf_name)")
                    continue
                
                # Helper function to parse position string in "Plate-Well" format
                def parse_position(position_str):
                    if pd.isna(position_str) or not position_str.strip():
                        return None, None
                    
                    position_str = position_str.strip()
                    parts = position_str.split('-')
                    
                    if len(parts) != 2:
                        # Try other common separators
                        if ':' in position_str:
                            parts = position_str.split(':')
                        elif '_' in position_str:
                            parts = position_str.split('_')
                        elif ' ' in position_str:
                            parts = position_str.split(' ', 1)
                        else:
                            # Try to intelligently split if no separator
                            # Find the position of the first digit
                            import re
                            match = re.search(r'\d', position_str)
                            if match:
                                digit_pos = match.start()
                                if digit_pos > 0:
                                    parts = [position_str[:digit_pos].strip(), position_str[digit_pos:].strip()]
                                else:
                                    return position_str, ''
                            else:
                                return position_str, ''
                    
                    if len(parts) == 2:
                        return parts[0].strip(), parts[1].strip()
                    else:
                        return position_str, ''
                
                # Helper function to safely get string value from DataFrame
                def safe_get(column, default=''):
                    if column in row and not pd.isna(row[column]):
                        return str(row[column]).strip()
                    return default
                
                # Helper function to parse boolean values
                def parse_boolean(value):
                    if pd.isna(value):
                        return 0
                    value = str(value).lower().strip()
                    return 1 if value in ['yes', 'true', '1', 'y', 't'] else 0
                
                # Determine which record types to create
                has_sequence = 'orf_sequence' in df.columns and not pd.isna(row.get('orf_sequence'))
                
                # Check if position fields are provided
                entry_position = not pd.isna(row.get('entry_position', '')) and row.get('entry_position', '').strip() != ''
                yeast_ad_position = not pd.isna(row.get('yeast_ad_position', '')) and row.get('yeast_ad_position', '').strip() != ''
                yeast_db_position = not pd.isna(row.get('yeast_db_position', '')) and row.get('yeast_db_position', '').strip() != ''
                
                # Parse position data
                entry_plate, entry_well = parse_position(row.get('entry_position', '')) if entry_position else (None, None)
                ad_plate, ad_well = parse_position(row.get('yeast_ad_position', '')) if yeast_ad_position else (None, None)
                db_plate, db_well = parse_position(row.get('yeast_db_position', '')) if yeast_db_position else (None, None)
                
                # Check for related entity data
                has_source = safe_get('source_name') != ''
                has_organism = safe_get('organism_id') != '' or safe_get('organism_name') != ''
                has_freezer = safe_get('freezer_id') != '' or safe_get('freezer_location') != ''
                has_plasmid = safe_get('plasmid_id') != '' or safe_get('plasmid_name') != ''
                
                # 1. Create/update organism if provided
                organism_id = safe_get('organism_id')
                if has_organism:
                    try:
                        if organism_id:
                            # Check if organism exists
                            c.execute("SELECT 1 FROM organisms WHERE organism_id = ?", (organism_id,))
                            organism_exists = c.fetchone() is not None
                            
                            # Either update existing or create new
                            organism_name = safe_get('organism_name')
                            organism_genus = safe_get('organism_genus')
                            organism_species = safe_get('organism_species')
                            organism_strain = safe_get('organism_strain')
                            
                            if organism_exists:
                                c.execute('''
                                    UPDATE organisms 
                                    SET organism_name = ?, organism_genus = ?, organism_species = ?, organism_strain = ?
                                    WHERE organism_id = ?
                                ''', (organism_name, organism_genus, organism_species, organism_strain, organism_id))
                            else:
                                c.execute('''
                                    INSERT INTO organisms (organism_id, organism_name, organism_genus, organism_species, organism_strain)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (organism_id, organism_name, organism_genus, organism_species, organism_strain))
                            stats['organisms'] += 1
                    except Exception as e:
                        stats['errors'].append(f"Row {idx + 2}: Error with organism data: {str(e)}")
                
                # 2. Create/update freezer if provided
                freezer_id = safe_get('freezer_id')
                if has_freezer:
                    try:
                        if freezer_id:
                            # Check if freezer exists
                            c.execute("SELECT 1 FROM freezer WHERE freezer_id = ?", (freezer_id,))
                            freezer_exists = c.fetchone() is not None
                            
                            # Either update existing or create new
                            freezer_location = safe_get('freezer_location')
                            freezer_condition = safe_get('freezer_condition')
                            freezer_date = safe_get('freezer_date', datetime.now().strftime('%Y-%m-%d'))
                            
                            if freezer_exists:
                                c.execute('''
                                    UPDATE freezer 
                                    SET freezer_location = ?, freezer_condition = ?, freezer_date = ?
                                    WHERE freezer_id = ?
                                ''', (freezer_location, freezer_condition, freezer_date, freezer_id))
                            else:
                                c.execute('''
                                    INSERT INTO freezer (freezer_id, freezer_location, freezer_condition, freezer_date)
                                    VALUES (?, ?, ?, ?)
                                ''', (freezer_id, freezer_location, freezer_condition, freezer_date))
                            stats['freezers'] += 1
                    except Exception as e:
                        stats['errors'].append(f"Row {idx + 2}: Error with freezer data: {str(e)}")
                
                # 3. Create/update plasmid if provided
                plasmid_id = safe_get('plasmid_id')
                if has_plasmid:
                    try:
                        if plasmid_id:
                            # Check if plasmid exists
                            c.execute("SELECT 1 FROM plasmid WHERE plasmid_id = ?", (plasmid_id,))
                            plasmid_exists = c.fetchone() is not None
                            
                            # Either update existing or create new
                            plasmid_name = safe_get('plasmid_name')
                            plasmid_type = safe_get('plasmid_type')
                            plasmid_express_organism = safe_get('plasmid_express_organism')
                            plasmid_description = safe_get('plasmid_description')
                            
                            if plasmid_exists:
                                c.execute('''
                                    UPDATE plasmid 
                                    SET plasmid_name = ?, plasmid_type = ?, plasmid_express_organism = ?, plasmid_description = ?
                                    WHERE plasmid_id = ?
                                ''', (plasmid_name, plasmid_type, plasmid_express_organism, plasmid_description, plasmid_id))
                            else:
                                c.execute('''
                                    INSERT INTO plasmid (plasmid_id, plasmid_name, plasmid_type, plasmid_express_organism, plasmid_description)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (plasmid_id, plasmid_name, plasmid_type, plasmid_express_organism, plasmid_description))
                            stats['plasmids'] += 1
                    except Exception as e:
                        stats['errors'].append(f"Row {idx + 2}: Error with plasmid data: {str(e)}")
                
                # 4. Insert/update ORF sequence if provided
                if has_sequence:
                    try:
                        orf_sequence = row['orf_sequence']
                        orf_name = row['orf_name']
                        orf_annotation = safe_get('orf_annotation')
                        
                        # Handle boolean fields
                        orf_with_stop = parse_boolean(row.get('orf_with_stop', 0))
                        orf_open = parse_boolean(row.get('orf_open', 0))
                        
                        # Handle potentially missing fields
                        orf_organism_id = safe_get('organism_id')
                        orf_length_bp = int(row.get('orf_length_bp', 0)) if not pd.isna(row.get('orf_length_bp', 0)) else 0
                        orf_entrez_id = safe_get('orf_entrez_id')
                        orf_ensembl_id = safe_get('orf_ensembl_id')
                        orf_uniprot_id = safe_get('orf_uniprot_id')
                        orf_ref_url = safe_get('orf_ref_url')
                        
                        # Insert or update the sequence
                        c.execute('''
                            INSERT OR REPLACE INTO orf_sequence (
                                orf_id, orf_name, orf_annotation, orf_sequence, orf_with_stop, orf_open,
                                orf_organism_id, orf_length_bp, orf_entrez_id, orf_ensembl_id, orf_uniprot_id, orf_ref_url
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            orf_id, orf_name, orf_annotation, orf_sequence, 
                            orf_with_stop, orf_open, orf_organism_id, orf_length_bp, 
                            orf_entrez_id, orf_ensembl_id, orf_uniprot_id, orf_ref_url
                        ))
                        stats['sequences'] += 1
                    except Exception as e:
                        stats['errors'].append(f"Row {idx + 2}: Error inserting sequence: {str(e)}")
                
                # 5. Insert entry position if provided
                if entry_position and entry_plate and entry_well:
                    try:
                        c.execute('''
                            INSERT INTO orf_position (
                                orf_id, plate, well, freezer_id, plasmid_id, orf_create_date
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            orf_id, entry_plate, entry_well, freezer_id, plasmid_id, 
                            datetime.now().strftime('%Y-%m-%d')
                        ))
                        stats['entry_positions'] += 1
                    except sqlite3.IntegrityError:
                        stats['errors'].append(f"Row {idx + 2}: Entry position already exists (orf_id: {orf_id}, plate: {entry_plate}, well: {entry_well})")
                    except Exception as e:
                        stats['errors'].append(f"Row {idx + 2}: Error inserting entry position: {str(e)}")
                
                # 6. Insert yeast AD position if provided
                if yeast_ad_position and ad_plate and ad_well:
                    try:
                        c.execute('''
                            INSERT INTO yeast_orf_position (
                                orf_id, plate, well, position_type
                            ) VALUES (?, ?, ?, ?)
                        ''', (
                            orf_id, ad_plate, ad_well, 'AD'
                        ))
                        stats['yeast_ad_positions'] += 1
                    except sqlite3.IntegrityError:
                        stats['errors'].append(f"Row {idx + 2}: Yeast AD position already exists (orf_id: {orf_id}, plate: {ad_plate}, well: {ad_well})")
                    except Exception as e:
                        stats['errors'].append(f"Row {idx + 2}: Error inserting yeast AD position: {str(e)}")
                
                # 7. Insert yeast DB position if provided
                if yeast_db_position and db_plate and db_well:
                    try:
                        c.execute('''
                            INSERT INTO yeast_orf_position (
                                orf_id, plate, well, position_type
                            ) VALUES (?, ?, ?, ?)
                        ''', (
                            orf_id, db_plate, db_well, 'DB'
                        ))
                        stats['yeast_db_positions'] += 1
                    except sqlite3.IntegrityError:
                        stats['errors'].append(f"Row {idx + 2}: Yeast DB position already exists (orf_id: {orf_id}, plate: {db_plate}, well: {db_well})")
                    except Exception as e:
                        stats['errors'].append(f"Row {idx + 2}: Error inserting yeast DB position: {str(e)}")
                
                # 8. Insert source information for traceability
                if has_source:
                    try:
                        source_name = safe_get('source_name', 'Unknown Source')
                        source_details = safe_get('source_details')
                        source_url = safe_get('source_url')
                        submission_date = safe_get('submission_date', datetime.now().strftime('%Y-%m-%d'))
                        submitter = safe_get('submitter')
                        notes = safe_get('notes')
                        
                        # Create a source attribution
                        c.execute('''
                            INSERT INTO orf_sources (
                                orf_id, source_name, source_details, source_url, submission_date, submitter, notes
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            orf_id, source_name, source_details, source_url, submission_date, submitter, notes
                        ))
                        stats['sources'] += 1
                    except Exception as e:
                        stats['errors'].append(f"Row {idx + 2}: Error inserting source information: {str(e)}")
            
            # Check if we have successfully imported anything
            total_imports = sum([stats['sequences'], stats['entry_positions'], 
                               stats['yeast_ad_positions'], stats['yeast_db_positions'], 
                               stats['sources'], stats['organisms'], stats['freezers'], 
                               stats['plasmids']])
            
            if total_imports > 0:
                c.execute('COMMIT')
                
                # Generate success message
                success_details = []
                if stats['sequences'] > 0:
                    success_details.append(f"{stats['sequences']} ORF sequences")
                if stats['entry_positions'] > 0:
                    success_details.append(f"{stats['entry_positions']} entry positions")
                if stats['yeast_ad_positions'] > 0:
                    success_details.append(f"{stats['yeast_ad_positions']} yeast AD positions")
                if stats['yeast_db_positions'] > 0:
                    success_details.append(f"{stats['yeast_db_positions']} yeast DB positions")
                if stats['organisms'] > 0:
                    success_details.append(f"{stats['organisms']} organisms")
                if stats['freezers'] > 0:
                    success_details.append(f"{stats['freezers']} freezers")
                if stats['plasmids'] > 0:
                    success_details.append(f"{stats['plasmids']} plasmids")
                if stats['sources'] > 0:
                    success_details.append(f"{stats['sources']} source records")
                
                success_message = f"Successfully imported {', '.join(success_details)}"
                
                # Add warning about errors if any occurred
                if stats['errors']:
                    error_count = len(stats['errors'])
                    success_message += f". Warning: {error_count} error(s) occurred during import."
                    if error_count <= 5:
                        success_message += " Errors: " + "; ".join(stats['errors'])
                    else:
                        success_message += " First 5 errors: " + "; ".join(stats['errors'][:5]) + "..."
                
                return True, success_message
            else:
                c.execute('ROLLBACK')
                return False, f"No records were imported. Check for errors: {'; '.join(stats['errors'][:5])}"
                
        except Exception as e:
            c.execute('ROLLBACK')
            return False, f"Error during import: {str(e)}"
            
        finally:
            conn.close()
            
    except Exception as e:
        return False, f"Error processing file: {str(e)}"

@app.route('/export', methods=['GET'])
def export_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Create export directory for better permission management
    export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'exports')
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
        
        # Export yeast_orf_position data (excluding the id column)
        c.execute('SELECT orf_id, plate, well FROM yeast_orf_position')
        yeast_orf_position_data = c.fetchall()
        with open(os.path.join(export_dir, 'yeast_orf_position.csv'), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['orf_id', 'plate', 'well'])
            for row in yeast_orf_position_data:
                writer.writerow(row)
        
        # Export orf_sources data
        c.execute('SELECT orf_id, source_name, source_details, source_url, submission_date, submitter, notes FROM orf_sources')
        orf_sources_data = c.fetchall()
        with open(os.path.join(export_dir, 'orf_sources.csv'), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['orf_id', 'source_name', 'source_details', 'source_url', 'submission_date', 'submitter', 'notes'])
            for row in orf_sources_data:
                writer.writerow(row)
        
        # Also export to Excel format
        with pd.ExcelWriter(os.path.join(export_dir, 'reagent_database_export.xlsx')) as writer:
            pd.DataFrame(freezer_data, columns=['freezer_id', 'freezer_location', 'freezer_condition', 'freezer_date']).to_excel(writer, sheet_name='Freezers', index=False)
            pd.DataFrame(organisms_data, columns=['organism_id', 'organism_name', 'organism_genus', 'organism_species', 'organism_strain']).to_excel(writer, sheet_name='Organisms', index=False)
            pd.DataFrame(plasmid_data, columns=['plasmid_id', 'plasmid_name', 'plasmid_type', 'plasmid_express_organism', 'plasmid_description']).to_excel(writer, sheet_name='Plasmids', index=False)
            
            # For ORF sequences, limit the sequence length in Excel to prevent large files
            orf_sequence_df = pd.DataFrame(orf_sequence_data, columns=['orf_id', 'orf_name', 'orf_annotation', 'orf_sequence', 'orf_with_stop', 
                             'orf_open', 'orf_organism_id', 'orf_length_bp', 'orf_entrez_id', 
                             'orf_ensembl_id', 'orf_uniprot_id', 'orf_ref_url'])
            # Truncate sequences longer than 100 characters for Excel display
            orf_sequence_df['orf_sequence'] = orf_sequence_df['orf_sequence'].apply(lambda x: x[:100] + '...' if len(str(x)) > 100 else x)
            orf_sequence_df.to_excel(writer, sheet_name='ORF Sequences', index=False)
            
            pd.DataFrame(orf_position_data, columns=['orf_id', 'plate', 'well', 'freezer_id', 'plasmid_id', 'orf_create_date']).to_excel(writer, sheet_name='ORF Positions', index=False)
            
            pd.DataFrame(yeast_orf_position_data, columns=['orf_id', 'plate', 'well']).to_excel(writer, sheet_name='Yeast ORF Positions', index=False)
            
            # Add ORF sources to the Excel export
            pd.DataFrame(orf_sources_data, columns=['orf_id', 'source_name', 'source_details', 'source_url', 'submission_date', 'submitter', 'notes']).to_excel(writer, sheet_name='ORF Sources', index=False)
        
        success = True
        message = f'Data exported successfully to CSV files and Excel in {export_dir}'
    except Exception as e:
        success = False
        message = f'Error exporting data: {str(e)}'
    finally:
        conn.close()
    
    return jsonify({'success': success, 'message': message})

@app.route('/template/<import_type>', methods=['GET'])
def get_template(import_type):
    """Generate and return a template CSV file for the specified import type"""
    export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'exports')
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    template_file = os.path.join(export_dir, f'{import_type}_template.csv')
    template_xlsx = os.path.join(export_dir, f'{import_type}_template.xlsx')
    
    # Create template DataFrame
    template_df = create_template_dataframe(import_type)
    if template_df is None:
        return jsonify({'success': False, 'message': f'Unknown import type: {import_type}'})
    
    # Save as CSV and Excel
    template_df.to_csv(template_file, index=False)
    template_df.to_excel(template_xlsx, index=False)
    
    return jsonify({
        'success': True, 
        'message': f'Templates generated', 
        'csv_path': f'/download/{import_type}_template.csv',
        'xlsx_path': f'/download/{import_type}_template.xlsx'
    })

@app.route('/download/<filename>')
def download_file(filename):
    """Download a file from the exports directory"""
    export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'exports')
    return send_from_directory(export_dir, filename, as_attachment=True)
