import re
from bs4 import BeautifulSoup
from models.sequence import Sequence
from models.human_gene import HumanGene

class BlastService:
    """Service for processing BLAST search results."""
    
    def process_results(self, xml_results):
        """Process BLAST XML results into a structured format."""
        hits = []
        soup = BeautifulSoup(xml_results, 'xml')
        
        for hit_num, hit in enumerate(soup.find_all('Hit'), 1):
            hit_def = hit.find('Hit_def').text
            hit_accession = hit.find('Hit_accession').text
            hit_len = int(hit.find('Hit_len').text)
            
            # Extract ID from hit_def (assuming format like "lcl|123 description")
            seq_id = hit_accession
            if '|' in hit_def:
                parts = hit_def.split('|')
                if len(parts) > 1 and parts[1]:
                    id_part = parts[1].split(' ')[0]
                    if id_part:
                        seq_id = id_part
            
            # Find the sequence in the database
            sequence = Sequence.find_by_id(seq_id)
            
            # Initialize gene information
            gene_symbol = None
            original_name = hit_def
            
            if sequence:
                # Try to get gene symbol through different approaches
                gene_symbol = self.find_gene_symbol(sequence, hit_def)
                
                # Get original name if available
                if hasattr(sequence, 'name') and sequence.name:
                    original_name = sequence.name
                elif hasattr(sequence, 'human_gene') and sequence.human_gene and hasattr(sequence.human_gene, 'original_name'):
                    original_name = sequence.human_gene.original_name
            
            # Get the first HSP (High-scoring Segment Pair)
            hsp = hit.find('Hsp')
            
            if hsp:
                hit_data = {
                    'hit_num': hit_num,
                    'hit_id': seq_id,
                    'hit_def': hit_def,
                    'gene_symbol': gene_symbol or '-',
                    'original_name': original_name,
                    'hit_len': hit_len,
                    'hsp_bit_score': float(hsp.find('Hsp_bit-score').text),
                    'hsp_score': int(hsp.find('Hsp_score').text),
                    'hsp_evalue': float(hsp.find('Hsp_evalue').text),
                    'hsp_query_from': int(hsp.find('Hsp_query-from').text),
                    'hsp_query_to': int(hsp.find('Hsp_query-to').text),
                    'hsp_hit_from': int(hsp.find('Hsp_hit-from').text),
                    'hsp_hit_to': int(hsp.find('Hsp_hit-to').text),
                    'hsp_identity': int(hsp.find('Hsp_identity').text),
                    'hsp_positive': int(hsp.find('Hsp_positive').text),
                    'hsp_gaps': int(hsp.find('Hsp_gaps').text),
                    'hsp_align_len': int(hsp.find('Hsp_align-len').text)
                }
                hits.append(hit_data)
        
        return hits
    
    def find_gene_symbol(self, sequence, hit_def):
        """Find gene symbol using various approaches."""
        # Check if sequence has a direct association with human_gene
        if hasattr(sequence, 'human_gene') and sequence.human_gene:
            if hasattr(sequence.human_gene, 'hgnc_symbol') and sequence.human_gene.hgnc_symbol:
                return sequence.human_gene.hgnc_symbol
        
        # Check if sequence has a gene_name attribute
        if hasattr(sequence, 'gene_name') and sequence.gene_name:
            return sequence.gene_name
        
        # Try to find gene symbol by name or id
        name_to_try = None
        
        # First try using sequence name if available
        if hasattr(sequence, 'name') and sequence.name:
            name_to_try = sequence.name
        
        # Then try extracting from hit_def
        if not name_to_try or name_to_try == hit_def:
            name_to_try = self.extract_gene_name_from_hit_def(hit_def)
        
        # Next try the sequence ID itself if it looks like a gene name
        if not name_to_try and re.match(r'^[A-Za-z0-9]+$', str(sequence.id)):
            name_to_try = str(sequence.id)
        
        # Try to find a human gene with that original name
        if name_to_try:
            human_gene = HumanGene.find_by_name(name_to_try)
            if human_gene and hasattr(human_gene, 'hgnc_symbol') and human_gene.hgnc_symbol:
                return human_gene.hgnc_symbol
        
        return None
    
    def extract_gene_name_from_hit_def(self, hit_def):
        """Extract gene names from hit definition using regex patterns."""
        gene_patterns = [
            r'\b(MGC\d+)\b',                     # Match MGC followed by numbers
            r'\b([A-Z0-9]{2,})\s+protein\b',     # Match gene name followed by "protein" 
            r'protein\s+([A-Z0-9]{2,})\b',       # Match "protein" followed by gene name
            r'\b([A-Z]{2,}[0-9]{1,})\b'          # Match letters followed by numbers
        ]
        
        for pattern in gene_patterns:
            match = re.search(pattern, hit_def, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
