import os
import pandas as pd
from datetime import datetime

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
        
    elif import_type == 'freezer':
        columns = ['freezer_id', 'freezer_location', 'freezer_condition', 'freezer_date']
        
        # Create example row
        example = {
            'freezer_id': 'FRZ999',
            'freezer_location': 'Example Location',
            'freezer_condition': '-80°C',
            'freezer_date': datetime.now().strftime('%Y-%m-%d')
        }
    else:
        return None, None
        
    return columns, example

def create_template_dataframe(import_type):
    """Create a DataFrame template for the specified import type"""
    columns, example = get_column_info(import_type)
    if not columns or not example:
        return None
        
    # Create template DataFrame with example row
    df = pd.DataFrame([example], columns=columns)
    
    # Add a row with just required fields
    required = {k: 'Required' if k in example else '' for k in columns}
    df2 = pd.DataFrame([required], columns=columns)
    
    # Combine
    return pd.concat([df, df2], ignore_index=True)
