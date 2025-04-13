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
        
    elif import_type == 'yeast_orf_position':
        columns = ['orf_id', 'plate', 'well']
        
        # Create example row
        example = {
            'orf_id': 'ORF999',
            'plate': 'Yeast Plate A',
            'well': 'A01'
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
        
    elif import_type == 'orf_sources':
        columns = ['orf_id', 'source_name', 'source_details', 'source_url', 'submission_date', 'submitter', 'notes']
        
        # Create example row
        example = {
            'orf_id': 'ORF999',
            'source_name': 'Harvard PlasmID Repository',
            'source_details': 'Clone ID: HsCD00001234',
            'source_url': 'https://plasmid.med.harvard.edu/PLASMID/',
            'submission_date': datetime.now().strftime('%Y-%m-%d'),
            'submitter': 'Jane Doe',
            'notes': 'Verified by sequencing'
        }
        
        # Specify which fields are required
        required_fields = ['orf_id', 'source_name']
        
    else:
        return None, None, None
        
    return columns, example, required_fields

def create_template_dataframe(import_type):
    """
    Create a template DataFrame for the specified import type
    
    Args:
        import_type: The type of import data
        
    Returns:
        DataFrame with template columns and example data
    """
    if import_type == 'unified_position':
        data = {
            # ORF basic information
            'orf_id': ['Required', 'ORF001', 'ORF002', 'ORF003', 'ORF004', 'ORF005', 'ORF006'],
            'orf_name': ['Required', 'BRCA1', 'TP53', 'KRAS', 'EGFR', 'PTEN', 'AKT1'],
            'orf_annotation': ['Optional', 'Breast cancer type 1', 'Tumor protein p53', 'KRAS proto-oncogene', 'Epidermal growth factor receptor', 'Phosphatidylinositol 3,4,5-trisphosphate 3-phosphatase', 'RAC-alpha serine/threonine-protein kinase'],
            'orf_sequence': ['Optional', 'ATGCATGCATGC', 'GTACGTACGTAC', 'ACGTACGTACGT', 'GCATGCATGCAT', 'TGCATGCATGCA', 'CGTAGCTAGCTA'],
            
            # Position information (direct format)
            'entry_position': ['Optional (Plate-Well format)', 'Plate1-A1', '', '', 'Plate4-D7', '', 'Plate6-F11'],
            'yeast_ad_position': ['Optional (Plate-Well format)', '', 'Plate2-B5', '', 'Plate4-D8', 'Plate5-E9', 'Plate6-F12'],
            'yeast_db_position': ['Optional (Plate-Well format)', '', '', 'Plate3-C3', '', 'Plate5-E10', 'Plate6-G1'],
            
            # Source information
            'source_name': ['Required', 'SourceLab1', 'SourceLab2', 'SourceLab3', 'SourceLab4', 'SourceLab5', 'SourceLab6'],
            'source_details': ['Optional', 'Entry clone from Lab1', 'AD yeast clone from Lab2', 'DB yeast clone from Lab3', 'Combined entry and AD clone', 'Both AD and DB clones', 'Complete set of positions'],
            
            # ORF additional properties
            'orf_with_stop': ['Optional (1=yes, 0=no)', 1, 0, 1, 1, 0, 1],
            'orf_open': ['Optional (1=yes, 0=no)', 1, 1, 0, 1, 1, 1],
            'orf_length_bp': ['Optional', 12, 12, 12, 12, 12, 12],
            'orf_entrez_id': ['Optional', '672', '7157', '3845', '1956', '5728', '207'],
            'orf_ensembl_id': ['Optional', 'ENSG00000012048', 'ENSG00000141510', 'ENSG00000133703', 'ENSG00000146648', 'ENSG00000171862', 'ENSG00000142208'],
            'orf_uniprot_id': ['Optional', 'P38398', 'P04637', 'P01116', 'P00533', 'P60484', 'P31749'],
            'orf_ref_url': ['Optional', 'https://www.ncbi.nlm.nih.gov/gene/672', 'https://www.ncbi.nlm.nih.gov/gene/7157', 'https://www.ncbi.nlm.nih.gov/gene/3845', 'https://www.ncbi.nlm.nih.gov/gene/1956', 'https://www.ncbi.nlm.nih.gov/gene/5728', 'https://www.ncbi.nlm.nih.gov/gene/207'],
            
            # Organism information
            'organism_id': ['Optional', 'ORG001', 'ORG001', 'ORG001', 'ORG002', 'ORG003', 'ORG004'],
            'organism_name': ['Optional', 'Human', 'Human', 'Human', 'Mouse', 'Yeast', 'Bacteria'],
            'organism_genus': ['Optional', 'Homo', 'Homo', 'Homo', 'Mus', 'Saccharomyces', 'Escherichia'],
            'organism_species': ['Optional', 'sapiens', 'sapiens', 'sapiens', 'musculus', 'cerevisiae', 'coli'],
            'organism_strain': ['Optional', '', '', '', 'C57BL/6', 'Y8930', 'BL21'],
            
            # Freezer information
            'freezer_id': ['Optional', 'FRZ001', 'FRZ002', 'FRZ003', 'FRZ004', 'FRZ005', 'FRZ006'],
            'freezer_location': ['Optional', 'Lab 101 - Main', 'Lab 102 - Secondary', 'Lab 103 - Backup', 'Lab 104', 'Lab 105', 'Lab 106'],
            'freezer_condition': ['Optional', '-80C', '-20C', '-80C', '-80C', '-20C', 'Liquid Nitrogen'],
            
            # Plasmid information
            'plasmid_id': ['Optional', 'PLS001', 'PLS002', 'PLS003', 'PLS004', 'PLS005', 'PLS006'],
            'plasmid_name': ['Optional', 'pDEST-GW', 'pDEST-AD', 'pDEST-DB', 'pENTR-D', 'pENTR221', 'pETG30A'],
            'plasmid_type': ['Optional', 'Destination', 'Destination', 'Destination', 'Entry', 'Entry', 'Expression'],
            'plasmid_express_organism': ['Optional', 'E. coli', 'Yeast', 'Yeast', 'E. coli', 'E. coli', 'Bacteria'],
            'plasmid_description': ['Optional', 'Gateway destination vector', 'Yeast two-hybrid AD vector', 'Yeast two-hybrid DB vector', 'Gateway entry vector', 'Gateway entry vector with kanamycin resistance', 'Bacterial expression vector with GST tag']
        }
        return pd.DataFrame(data)
    
    elif import_type == 'plasmid':
        data = {
            'plasmid_id': ['Required', 'PLS001', 'PLS002', 'PLS003'],
            'plasmid_name': ['Required', 'pDEST-AD', 'pDEST-DB', 'pENTR-D-TOPO'],
            'plasmid_type': ['Optional', 'Destination', 'Destination', 'Entry'],
            'plasmid_express_organism': ['Optional', 'Yeast', 'Yeast', 'E. coli'],
            'plasmid_description': ['Optional', 'Yeast two-hybrid AD vector', 'Yeast two-hybrid DB vector', 'Gateway entry vector']
        }
        return pd.DataFrame(data)
    
    elif import_type == 'organism':
        data = {
            'organism_id': ['Required', 'ORG001', 'ORG002', 'ORG003'],
            'organism_name': ['Required', 'Human', 'Mouse', 'Yeast'],
            'organism_genus': ['Optional', 'Homo', 'Mus', 'Saccharomyces'],
            'organism_species': ['Optional', 'sapiens', 'musculus', 'cerevisiae'],
            'organism_strain': ['Optional', '', 'C57BL/6', 'Y8930']
        }
        return pd.DataFrame(data)
    
    elif import_type == 'freezer':
        data = {
            'freezer_id': ['Required', 'FRZ001', 'FRZ002', 'FRZ003'],
            'freezer_location': ['Required', 'Lab 101 - Main', 'Lab 203 - Backup', 'Storage Room B'],
            'freezer_condition': ['Optional', '-80C', '-20C', 'Liquid Nitrogen'],
            'freezer_date': ['Optional', '2023-01-15', '2023-02-20', '2023-03-25']
        }
        return pd.DataFrame(data)
    
    # Fallback to support legacy code (these can be removed once the new system is fully tested)
    elif import_type == 'orf_sequence':
        return create_template_dataframe('unified_position')
    elif import_type == 'orf_position':
        return create_template_dataframe('unified_position') 
    elif import_type == 'yeast_orf_position':
        return create_template_dataframe('unified_position')
    elif import_type == 'orf_sources':
        return create_template_dataframe('unified_position')
    
    return None
