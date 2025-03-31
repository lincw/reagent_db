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
    if import_type == 'orf_sequence':
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
            'annotation': 'orf_annotation'
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
    print("Import file request received")
    # Check if a file was uploaded
    if 'file' not in request.files:
        print("Error: No file part in request")
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    print(f"File received: {file.filename}")
    
    # Check if the file is empty
    if file.filename == '':
        print("Error: Empty filename")
        return jsonify({'success': False, 'message': 'No selected file'})
    
    # Check if the file is allowed
    if not allowed_file(file.filename):
        print(f"Error: File type not allowed for {file.filename}")
        return jsonify({'success': False, 'message': 'File type not allowed. Please upload CSV or XLSX files.'})
    
    # Get import type
    import_type = request.form.get('import_type')
    print(f"Import type specified: {import_type}")
    if not import_type:
        print("Error: No import type specified")
        return jsonify({'success': False, 'message': 'No import type specified'})
        
    # Normalize import type (in case there are case differences or spaces)
    if import_type.lower().replace(' ', '_') == 'orf_sequence':
        import_type = 'orf_sequence'
    elif import_type.lower().replace(' ', '_') == 'orf_position':
        import_type = 'orf_position'
    print(f"Normalized import type: {import_type}")
    
    # Save the file temporarily
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        file.save(filepath)
        print(f"File saved to {filepath}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return jsonify({'success': False, 'message': f'Error saving file: {str(e)}'})
    
    try:
        # Process the file based on its type
        if filename.endswith('.csv'):
            print("Reading CSV file")
            df = pd.read_csv(filepath)
        else:  # xlsx
            print("Reading Excel file")
            df = pd.read_excel(filepath)
        
        print(f"File read successfully with {len(df)} rows and columns: {df.columns.tolist()}")
        
        # Check for column name mapping (handle alternate column names)
        df = map_column_names(df, import_type)
        print(f"After column mapping: {df.columns.tolist()}")
        
        # Process based on import type
        result = process_import(df, import_type)
        
        if result['success']:
            return jsonify({'success': True, 'message': f'Successfully imported {result["count"]} {import_type} entries'})
        else:
            # Add code to log the error for debugging
            print(f"Import failed: {result['message']}")
            return jsonify({'success': False, 'message': result['message']})
        
    except Exception as e:
        print(f"Exception during file processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'})
    finally:
        # Clean up the uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

def process_import(df, import_type):
    """Process the imported dataframe based on the import type"""
    print(f"Processing import type: {import_type}")
    print(f"DataFrame columns: {df.columns.tolist()}")
    print(f"First row data: {df.iloc[0].to_dict()}")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    count = 0
    
    try:
        if import_type == 'orf_sequence':
            print("Processing ORF sequence import")
            # Validate required columns (updated requirements)
            required_columns = ['orf_id', 'orf_name', 'orf_sequence']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f'Missing required columns: {", ".join(missing_columns)}'
                print(f"Validation error: {error_msg}")
                return {'success': False, 'message': error_msg}
            
            # Process each row
            for _, row in df.iterrows():
                # Skip example rows or header rows that look like headers
                if row['orf_id'] == 'Required' or row['orf_id'] == 'ORF999' or \
                   str(row['orf_id']).lower() == 'orf_id':
                    continue
                
                # Set default values for optional columns
                orf_annotation = row.get('orf_annotation', '')
                
                # Handle orf_with_stop conversion more carefully
                orf_with_stop = 0
                if pd.notna(row.get('orf_with_stop')):
                    stop_val = str(row.get('orf_with_stop')).lower()
                    if stop_val in ['1', 'true', 'yes', 'y', 'stop']:
                        orf_with_stop = 1
                    else:
                        try:
                            orf_with_stop = int(stop_val)
                            if orf_with_stop != 0:
                                orf_with_stop = 1
                        except (ValueError, TypeError):
                            orf_with_stop = 0
                
                # Handle orf_open conversion carefully
                orf_open = 0
                if pd.notna(row.get('orf_open')):
                    open_val = str(row.get('orf_open')).lower()
                    if open_val in ['1', 'true', 'yes', 'y', 'open']:
                        orf_open = 1
                    else:
                        try:
                            orf_open = int(open_val)
                            if orf_open != 0:
                                orf_open = 1
                        except (ValueError, TypeError):
                            orf_open = 0
                
                # Handle numeric values safely
                try:
                    orf_length_bp = int(row.get('orf_length_bp', 0)) if pd.notna(row.get('orf_length_bp')) else 0
                except (ValueError, TypeError):
                    orf_length_bp = 0
                
                # Handle other optional columns
                orf_organism_id = str(row.get('orf_organism_id', '')) if pd.notna(row.get('orf_organism_id')) else ''
                orf_entrez_id = str(row.get('orf_entrez_id', '')) if pd.notna(row.get('orf_entrez_id')) else ''
                orf_ensembl_id = str(row.get('orf_ensembl_id', '')) if pd.notna(row.get('orf_ensembl_id')) else ''
                orf_uniprot_id = str(row.get('orf_uniprot_id', '')) if pd.notna(row.get('orf_uniprot_id')) else ''
                orf_ref_url = str(row.get('orf_ref_url', '')) if pd.notna(row.get('orf_ref_url')) else ''
                
                # Insert into database
                c.execute('''
                    INSERT OR REPLACE INTO orf_sequence (
                        orf_id, orf_name, orf_annotation, orf_sequence, orf_with_stop, orf_open,
                        orf_organism_id, orf_length_bp, orf_entrez_id, orf_ensembl_id, orf_uniprot_id, orf_ref_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['orf_id'], row['orf_name'], orf_annotation, row['orf_sequence'], 
                    orf_with_stop, orf_open, orf_organism_id, orf_length_bp, 
                    orf_entrez_id, orf_ensembl_id, orf_uniprot_id, orf_ref_url
                ))
                count += 1
        
        elif import_type == 'orf_position':
            # Validate required columns
            required_columns = ['orf_id', 'plate', 'well']
            for col in required_columns:
                if col not in df.columns:
                    return {'success': False, 'message': f'Missing required column: {col}'}
            
            # Process each row
            for _, row in df.iterrows():
                # Skip example rows
                if row['orf_id'] == 'Required' or row['orf_id'] == 'ORF999':
                    continue
                
                # Set default values for optional columns
                freezer_id = row.get('freezer_id', '')
                plasmid_id = row.get('plasmid_id', '')
                orf_create_date = row.get('orf_create_date', datetime.now().strftime('%Y-%m-%d'))
                
                # Insert into database
                c.execute('''
                    INSERT INTO orf_position (
                        orf_id, plate, well, freezer_id, plasmid_id, orf_create_date
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    row['orf_id'], row['plate'], row['well'], 
                    freezer_id, plasmid_id, orf_create_date
                ))
                count += 1
        
        elif import_type == 'plasmid':
            # Validate required columns
            required_columns = ['plasmid_id', 'plasmid_name']
            for col in required_columns:
                if col not in df.columns:
                    return {'success': False, 'message': f'Missing required column: {col}'}
            
            # Process each row
            for _, row in df.iterrows():
                # Skip example rows
                if row['plasmid_id'] == 'Required' or row['plasmid_id'] == 'PLS999':
                    continue
                
                # Set default values for optional columns
                plasmid_type = row.get('plasmid_type', '')
                plasmid_express_organism = row.get('plasmid_express_organism', '')
                plasmid_description = row.get('plasmid_description', '')
                
                # Insert into database
                c.execute('''
                    INSERT OR REPLACE INTO plasmid (
                        plasmid_id, plasmid_name, plasmid_type, plasmid_express_organism, plasmid_description
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    row['plasmid_id'], row['plasmid_name'], plasmid_type, 
                    plasmid_express_organism, plasmid_description
                ))
                count += 1
        
        elif import_type == 'organism':
            # Validate required columns
            required_columns = ['organism_id', 'organism_name']
            for col in required_columns:
                if col not in df.columns:
                    return {'success': False, 'message': f'Missing required column: {col}'}
            
            # Process each row
            for _, row in df.iterrows():
                # Skip example rows
                if row['organism_id'] == 'Required' or row['organism_id'] == 'ORG999':
                    continue
                
                # Set default values for optional columns
                organism_genus = row.get('organism_genus', '')
                organism_species = row.get('organism_species', '')
                organism_strain = row.get('organism_strain', '')
                
                # Insert into database
                c.execute('''
                    INSERT OR REPLACE INTO organisms (
                        organism_id, organism_name, organism_genus, organism_species, organism_strain
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    row['organism_id'], row['organism_name'], organism_genus, 
                    organism_species, organism_strain
                ))
                count += 1
        
        elif import_type == 'freezer':
            # Validate required columns
            required_columns = ['freezer_id', 'freezer_location']
            for col in required_columns:
                if col not in df.columns:
                    return {'success': False, 'message': f'Missing required column: {col}'}
            
            # Process each row
            for _, row in df.iterrows():
                # Skip example rows
                if row['freezer_id'] == 'Required' or row['freezer_id'] == 'FRZ999':
                    continue
                
                # Set default values for optional columns
                freezer_condition = row.get('freezer_condition', '')
                freezer_date = row.get('freezer_date', datetime.now().strftime('%Y-%m-%d'))
                
                # Insert into database
                c.execute('''
                    INSERT OR REPLACE INTO freezer (
                        freezer_id, freezer_location, freezer_condition, freezer_date
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    row['freezer_id'], row['freezer_location'], freezer_condition, freezer_date
                ))
                count += 1
        
        else:
            return {'success': False, 'message': f'Unknown import type: {import_type}'}
        
        conn.commit()
        return {'success': True, 'count': count}
        
    except Exception as e:
        conn.rollback()
        print(f"Database error in process_import: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': f'Database error: {str(e)}'}
    finally:
        conn.close()

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
