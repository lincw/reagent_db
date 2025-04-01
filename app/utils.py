import os
import pandas as pd
from datetime import datetime
import sqlite3
from config import get_db_path

def fetch_hgnc_mapping():
    """Fetch HGNC symbol mapping from database"""
    DB_PATH = get_db_path()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT orf_id, hgnc_approved_symbol FROM human_gene_data')
        hgnc_map = {row[0]: row[1] for row in cursor.fetchall() if row[1]}
        return hgnc_map
    except sqlite3.OperationalError:
        # Handle case where table might not exist
        return {}
    finally:
        conn.close()

def format_database_ids(orf_data):
    """
    Format database IDs to remove decimal points, map HGNC symbols
    
    Priority:
    1. Use HGNC symbol if exists
    2. Keep original name if no HGNC symbol
    """
    # Fetch HGNC mapping 
    hgnc_map = fetch_hgnc_mapping()

    # Handle Entrez ID 
    if 'orf_entrez_id' in orf_data and orf_data['orf_entrez_id']:
        try:
            # Try to convert to integer and back to string to remove decimal point
            orf_data['orf_entrez_id'] = str(int(float(orf_data['orf_entrez_id'])))
        except (ValueError, TypeError):
            # If conversion fails, keep as is
            pass

    # Map HGNC symbol if exists 
    if orf_data.get('orf_id') in hgnc_map:
        # Store original name before replacement
        orf_data['previous_name'] = orf_data.get('orf_name', '')
        
        # Replace name with HGNC symbol
        hgnc_symbol = hgnc_map[orf_data['orf_id']]
        orf_data['orf_name'] = hgnc_symbol

    return orf_data

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    """Check if a file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_column_info(import_type):
    """Get column information for different table types"""
    if import_type == 'orf_sequence':
        columns = ['orf_id', 'orf_name', 'orf_annotation', 'orf_sequence', 'orf_with_stop', 
                'orf_open', 'orf_organism_id', 'orf_length_bp', 'orf_entrez_id', 
                'orf_ensembl_id', 'orf_uniprot_id', 'orf_ref_url']
        
        # Create example row
        example = {
            'orf_id': 'ORF999',
            'orf_name': 'Example Gene',
            'orf_annotation': 'Example Annotation',
            'orf_sequence': 'ATGCTAGCTAGCTAGC',
            'orf_with_stop': 1,
            'orf_open': 1,
            'orf_organism_id': 'ORG001',
            'orf_length_bp': 16,
            'orf_entrez_id': '12345',
            'orf_ensembl_id': 'ENSG00000000000',
            'orf_uniprot_id': 'P12345',
            'orf_ref_url': 'https://example.com/gene'
        }
        
        # Specify which fields are actually required
        required_fields = ['orf_id', 'orf_name', 'orf_sequence']
        
    elif import_type == 'orf_position':
        columns = ['orf_id', 'plate', 'well', 'freezer_id', 'plasmid_id', 'orf_create_date']
        
        # Create example row
        example = {
            'orf_id': 'ORF999',
            'plate': 'P01',
            'well': 'A01',
            'freezer_id': 'FRZ001',
            'plasmid_id': 'PLS001',
            'orf_create_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Specify which fields are required
        required_fields = ['orf_id', 'plate', 'well']
        
    elif import_type == 'plasmid':
        columns = ['plasmid_id', 'plasmid_name', 'plasmid_type', 'plasmid_express_organism', 'plasmid_description']
        
        # Create example row
        example = {
            'plasmid_id': 'PLS999',
            'plasmid_name': 'pExample',
            'plasmid_type': 'Expression',
            'plasmid_express_organism': 'E. coli',
            'plasmid_description': 'Example plasmid description'
        }
        
        # Specify which fields are required
        required_fields = ['plasmid_id', 'plasmid_name']
        
    elif import_type == 'organism':
        columns = ['organism_id', 'organism_name', 'organism_genus', 'organism_species', 'organism_strain']
        
        # Create example row
        example = {
            'organism_id': 'ORG999',
            'organism_name': 'Example Organism',
            'organism_genus': 'Example',
            'organism_species': 'organism',
            'organism_strain': 'XYZ'
        }
        
        # Specify which fields are required
        required_fields = ['organism_id', 'organism_name']
        
    elif import_type == 'freezer':
        columns = ['freezer_id', 'freezer_location', 'freezer_condition', 'freezer_date']
        
        # Create example row
        example = {
            'freezer_id': 'FRZ999',
            'freezer_location': 'Example Location',
            'freezer_condition': '-80°C',
            'freezer_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Specify which fields are required
        required_fields = ['freezer_id', 'freezer_location']
    else:
        return None, None, None
        
    return columns, example, required_fields

def create_template_dataframe(import_type):
    """Create a DataFrame template for the specified import type"""
    columns, example, required_fields = get_column_info(import_type)
    if not columns or not example or not required_fields:
        return None
        
    # Create template DataFrame with example row
    df = pd.DataFrame([example], columns=columns)
    
    # Add a row with just required fields
    required = {}
    for col in columns:
        if col in required_fields:
            required[col] = 'Required'
        else:
            required[col] = 'Optional'
    
    df2 = pd.DataFrame([required], columns=columns)
    
    # Combine
    return pd.concat([df, df2], ignore_index=True)
