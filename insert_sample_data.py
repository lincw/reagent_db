"""
Sample data insertion script for the Reagent Database
This script will insert sample data into the SQLite database for testing purposes.
"""

import sqlite3
import os
from datetime import datetime, timedelta

def insert_sample_data():
    """Insert sample data into the database"""
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(current_dir, 'reagent_db.sqlite')
    
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run setup_db.py first to create it.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # First, clear existing data to avoid duplicates
    tables = ["freezer", "organisms", "plasmid", "orf_sequence", "orf_position"]
    for table in tables:
        c.execute(f"DELETE FROM {table}")
    
    # Create date variables for sample data
    today = datetime.now().strftime('%Y-%m-%d')
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    two_months_ago = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
    
    # Add realistic freezer data
    freezers = [
        ('FRZ001', 'Cold Room Shelf A', '-20°C', month_ago),
        ('FRZ002', 'Lab 220 - Ultra Freezer', '-80°C', two_months_ago),
        ('FRZ003', 'Lab 220 - Cryogenic Storage', '-196°C', month_ago),
        ('FRZ004', 'Lab 310 - Refrigerator', '4°C', today),
        ('FRZ005', 'Biobank Floor 2 - Section C', '-80°C', two_months_ago)
    ]
    
    c.executemany(
        'INSERT INTO freezer (freezer_id, freezer_location, freezer_condition, freezer_date) VALUES (?, ?, ?, ?)',
        freezers
    )
    
    # Add realistic organisms data
    organisms = [
        ('ORG001', 'Escherichia coli', 'Escherichia', 'coli', 'BL21(DE3)'),
        ('ORG002', 'Escherichia coli', 'Escherichia', 'coli', 'DH5α'),
        ('ORG003', 'Saccharomyces cerevisiae', 'Saccharomyces', 'cerevisiae', 'BY4741'),
        ('ORG004', 'Homo sapiens', 'Homo', 'sapiens', 'HEK293T'),
        ('ORG005', 'Mus musculus', 'Mus', 'musculus', 'C57BL/6'),
        ('ORG006', 'Drosophila melanogaster', 'Drosophila', 'melanogaster', 'w1118')
    ]
    
    c.executemany(
        'INSERT INTO organisms (organism_id, organism_name, organism_genus, organism_species, organism_strain) VALUES (?, ?, ?, ?, ?)',
        organisms
    )
    
    # Add realistic plasmid data
    plasmids = [
        ('PLS001', 'pET28a-GFP', 'Expression', 'E. coli', 'GFP expression vector with T7 promoter and His-tag'),
        ('PLS002', 'pGEX-6P-1-GST-TEV', 'Expression', 'E. coli', 'GST fusion protein expression with TEV cleavage site'),
        ('PLS003', 'pCMV-SPORT6', 'Mammalian Expression', 'Mammalian cells', 'CMV promoter for high-level expression in mammalian cells'),
        ('PLS004', 'pRS416-URA3', 'Shuttle', 'S. cerevisiae / E. coli', 'Yeast centromere vector with URA3 selectable marker'),
        ('PLS005', 'pUC19-Amp', 'Cloning', 'E. coli', 'High-copy cloning vector with ampicillin resistance'),
        ('PLS006', 'pLenti-CMV-GFP-Puro', 'Viral', 'Mammalian cells', 'Lentiviral vector with GFP and puromycin resistance')
    ]
    
    c.executemany(
        'INSERT INTO plasmid (plasmid_id, plasmid_name, plasmid_type, plasmid_express_organism, plasmid_description) VALUES (?, ?, ?, ?, ?)',
        plasmids
    )
    
    # Add realistic ORF sequence data (shortened sequences for clarity)
    orfs = [
        ('ORF001', 'GFP', 'Green Fluorescent Protein', 
         'ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAGTTC', 
         1, 1, 'ORG001', 720, '1440866', 'AGG79852', 'P42212', 'https://www.uniprot.org/uniprot/P42212'),
        
        ('ORF002', 'mCherry', 'Red Fluorescent Protein', 
         'ATGGTGAGCAAGGGCGAGGAGGATAACATGGCCATCATCAAGGAGTTCATGCGCTTCAAGGTGCACATGGAGGGCTCCGTGAAC', 
         1, 1, 'ORG001', 711, '283379496', 'AIC55137', 'X5DSL3', 'https://www.uniprot.org/uniprot/X5DSL3'),
        
        ('ORF003', 'LacZ', 'Beta-galactosidase', 
         'ATGACCATGATTACGGATTCACTGGCCGTCGTTTTACAACGTCGTGACTGGGAAAACCCTGGCGTTACCCAACTTAATCGCCTT', 
         1, 1, 'ORG001', 3075, '945006', 'b0344', 'P00722', 'https://www.uniprot.org/uniprot/P00722'),
        
        ('ORF004', 'GAPDH', 'Glyceraldehyde 3-phosphate dehydrogenase', 
         'ATGGGGAAGGTGAAGGTCGGAGTCAACGGATTTGGTCGTATTGGGCGCCTGGTCACCAGGGCTGCTTTTAACTCTGGTAAAGTG', 
         1, 1, 'ORG004', 1008, '2597', 'ENSG00000111640', 'P04406', 'https://www.uniprot.org/uniprot/P04406'),
        
        ('ORF005', 'p53', 'Tumor protein p53', 
         'ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAA', 
         1, 1, 'ORG004', 1182, '7157', 'ENSG00000141510', 'P04637', 'https://www.uniprot.org/uniprot/P04637'),
        
        ('ORF006', 'Cas9', 'CRISPR associated protein 9', 
         'ATGGACAAGAAGTACTCCATTGGGCTCGATATCGGCACAAACAGCGTCGGCTGGGCCGTCATTACGGACGAGTACAAGGTGCCC', 
         1, 1, 'ORG001', 4104, '1389113', 'NP_269215.1', 'Q99ZW2', 'https://www.uniprot.org/uniprot/Q99ZW2'),
        
        ('ORF007', 'ACT1', 'Actin', 
         'ATGGATTCTGAGGTTGCTGCTTTGGTTATTGATAACGGTTCTGGTATGTGTAAAGCCGGTTTTGCCGGTGACGACGCTCCTCGT', 
         1, 1, 'ORG003', 1131, '850504', 'YFL039C', 'P60010', 'https://www.uniprot.org/uniprot/P60010'),
        
        ('ORF008', 'SNF1', 'Carbon catabolite-derepressing protein kinase', 
         'ATGAGCAGTAACAACAATAACAATAATAATAACAACAACAGTGGTACTAGCAGTGGCATGGGCTCTCAAGCTCCCAGTTTCTCA', 
         1, 1, 'ORG003', 1782, '850812', 'YDR477W', 'P06782', 'https://www.uniprot.org/uniprot/P06782')
    ]
    
    c.executemany(
        '''INSERT INTO orf_sequence 
           (orf_id, orf_name, orf_annotation, orf_sequence, orf_with_stop, orf_open, 
            orf_organism_id, orf_length_bp, orf_entrez_id, orf_ensembl_id, orf_uniprot_id, orf_ref_url) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        orfs
    )
    
    # Add realistic ORF positions with meaningful plate/well naming
    positions = [
        # GFP in different locations
        ('ORF001', 'P01', 'A01', 'FRZ001', 'PLS001', month_ago),
        ('ORF001', 'P01', 'A02', 'FRZ001', 'PLS001', month_ago),
        ('ORF001', 'P02', 'C04', 'FRZ002', 'PLS001', today),
        
        # mCherry
        ('ORF002', 'P01', 'B03', 'FRZ001', 'PLS001', month_ago),
        ('ORF002', 'P03', 'D06', 'FRZ002', 'PLS003', two_months_ago),
        
        # LacZ
        ('ORF003', 'P02', 'E01', 'FRZ002', 'PLS002', two_months_ago),
        ('ORF003', 'P04', 'A12', 'FRZ003', 'PLS002', today),
        
        # Human genes
        ('ORF004', 'P05', 'F03', 'FRZ003', 'PLS003', month_ago),
        ('ORF005', 'P05', 'F04', 'FRZ003', 'PLS003', month_ago),
        ('ORF005', 'P05', 'F05', 'FRZ003', 'PLS006', today),
        
        # CRISPR
        ('ORF006', 'P06', 'A01', 'FRZ002', 'PLS005', today),
        
        # Yeast genes
        ('ORF007', 'P07', 'C08', 'FRZ005', 'PLS004', two_months_ago),
        ('ORF008', 'P07', 'C09', 'FRZ005', 'PLS004', two_months_ago)
    ]
    
    c.executemany(
        'INSERT INTO orf_position (orf_id, plate, well, freezer_id, plasmid_id, orf_create_date) VALUES (?, ?, ?, ?, ?, ?)',
        positions
    )
    
    conn.commit()
    conn.close()
    
    print("Sample data inserted successfully!")
    return True
    
if __name__ == "__main__":
    insert_sample_data()
