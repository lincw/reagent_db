"""
Utility functions for BLAST searches in the Reagent Database application.
This module requires the BLAST+ tools to be installed on the server.
"""

import os
import subprocess
import tempfile
import sqlite3
import json
import logging
from app import DB_PATH

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the BLAST database files
blast_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blast_db')

def check_blast_db_status():
    """
    Check if BLAST database files exist.
    
    Returns:
        bool: True if BLAST database exists, False otherwise
    """
    return os.path.exists(os.path.join(blast_db_path, 'reagent_db_nucl.nsq'))

def check_blast_installed():
    """
    Check if BLAST+ tools are installed.
    
    Returns:
        bool: True if installed, False otherwise
    """
    try:
        result = subprocess.run(['blastn', '-version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        logger.error("BLAST+ tools not found in PATH.")
        return False
    except Exception as e:
        logger.error(f"Error checking BLAST installation: {str(e)}")
        return False

def ensure_blast_db_exists():
    """
    Create BLAST database if it doesn't exist.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if BLAST is installed
    if not check_blast_installed():
        logger.error("BLAST+ tools are not installed. Cannot create database.")
        return False
    
    # Create blast_db directory if it doesn't exist
    if not os.path.exists(blast_db_path):
        os.makedirs(blast_db_path)
        logger.info(f"Created BLAST database directory at {blast_db_path}")
    
    # Path to the FASTA file for makeblastdb
    fasta_path = os.path.join(blast_db_path, 'reagent_db_sequences.fasta')
    
    # Extract sequences from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT orf_id, orf_name, orf_sequence 
        FROM orf_sequence 
        WHERE orf_sequence IS NOT NULL AND orf_sequence != ''
    ''')
    
    sequences = cursor.fetchall()
    conn.close()
    
    if not sequences:
        logger.warning("No sequences found in the database.")
        return False
    
    # Write sequences to FASTA file
    with open(fasta_path, 'w') as f:
        for seq_id, seq_name, sequence in sequences:
            # Format: >id|name
            f.write(f">{seq_id}|{seq_name}\n")
            
            # Write sequence with line breaks every 60 characters
            for i in range(0, len(sequence), 60):
                f.write(sequence[i:i+60] + "\n")
    
    logger.info(f"Wrote {len(sequences)} sequences to {fasta_path}")
    
    # Create BLAST databases (nucleotide)
    try:
        subprocess.run(
            ['makeblastdb', '-in', fasta_path, '-dbtype', 'nucl', '-out', os.path.join(blast_db_path, 'reagent_db_nucl')],
            check=True
        )
        logger.info("Successfully created nucleotide BLAST database")
        return True
    except Exception as e:
        logger.error(f"Error creating BLAST database: {str(e)}")
        return False

def run_blast_search(query_sequence, program='blastn', evalue=10, max_hits=50):
    """
    Run a BLAST search against the reagent database.
    
    Args:
        query_sequence (str): The query sequence to search
        program (str): BLAST program to use ('blastn', 'blastp', 'blastx', 'tblastn', 'tblastx')
        evalue (float): E-value threshold
        max_hits (int): Maximum number of hits to return
    
    Returns:
        dict: BLAST results in a structured format
    """
    # Check if BLAST is installed
    if not check_blast_installed():
        return {
            'success': False,
            'error': 'BLAST+ tools are not installed on the server. Please contact the administrator.'
        }
    
    # Check if BLAST database exists, create if not
    if not check_blast_db_status():
        if not ensure_blast_db_exists():
            return {
                'success': False,
                'error': 'Failed to create BLAST database. Please try again later.'
            }
    
    # Clean up the sequence (remove whitespace, numbers, etc.)
    clean_sequence = ''.join(c for c in query_sequence if c.isalpha())
    
    if not clean_sequence:
        return {
            'success': False,
            'error': 'Invalid sequence - sequence must contain valid nucleotide or amino acid characters'
        }
    
    # Create temporary file for query sequence
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as query_file:
        query_file.write(clean_sequence)
        query_path = query_file.name
    
    try:
        # Determine which database to use based on program
        db_path = os.path.join(blast_db_path, 'reagent_db_nucl')
        
        # Run BLAST command
        cmd = [
            program,
            '-query', query_path,
            '-db', db_path,
            '-outfmt', '15',  # JSON output format
            '-evalue', str(evalue),
            '-max_target_seqs', str(max_hits)
        ]
        
        logger.info(f"Running BLAST command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the JSON output
        try:
            blast_results = json.loads(result.stdout)
            logger.info("Successfully parsed BLAST results")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse BLAST JSON output: {str(e)}")
            logger.debug(f"BLAST stdout: {result.stdout}")
            return {
                'success': False,
                'error': f"Failed to parse BLAST results: {str(e)}"
            }
        
        # Format results for display
        formatted_results = format_blast_results(blast_results)
        
        return {
            'success': True,
            'results': formatted_results
        }
    
    except subprocess.CalledProcessError as e:
        logger.error(f"BLAST error: {e.stderr}")
        return {
            'success': False,
            'error': f"BLAST search failed: {e.stderr}"
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }
    finally:
        # Clean up temporary file
        try:
            os.unlink(query_path)
        except:
            pass

def format_blast_results(blast_json):
    """
    Format BLAST JSON results into a more user-friendly structure.
    
    Args:
        blast_json (dict): Raw BLAST JSON output
    
    Returns:
        list: Formatted hit information
    """
    formatted_hits = []
    
    # Check if we have results
    if 'BlastOutput2' not in blast_json:
        logger.warning("No 'BlastOutput2' key in BLAST results JSON")
        return formatted_hits
    
    # Navigate to the hits section
    try:
        report = blast_json['BlastOutput2'][0]['report']
        results = report['results']['search']
        
        # Check if we have hits
        if 'hits' not in results:
            logger.info("No hits found in BLAST results")
            return formatted_hits
        
        # Process each hit
        for hit in results['hits']:
            # Extract hit information
            hit_id = hit['description'][0]['id']
            hit_title = hit['description'][0]['title']
            
            # Parse the ID|Name format
            parts = hit_title.split('|', 1)
            if len(parts) > 1:
                orf_id = parts[0]
                orf_name = parts[1]
            else:
                orf_id = hit_id
                orf_name = hit_title
            
            # Get the best HSP (High-scoring Segment Pair)
            hsp = hit['hsps'][0]
            
            formatted_hit = {
                'orf_id': orf_id,
                'orf_name': orf_name,
                'bit_score': hsp['bit_score'],
                'score': hsp['score'],
                'evalue': hsp['evalue'],
                'identity': hsp['identity'],
                'query_from': hsp['query_from'],
                'query_to': hsp['query_to'],
                'hit_from': hsp['hit_from'],
                'hit_to': hsp['hit_to'],
                'align_len': hsp['align_len'],
                'gaps': hsp.get('gaps', 0),
                'qseq': hsp['qseq'],
                'hseq': hsp['hseq'],
                'midline': hsp['midline'],
                'percent_identity': (hsp['identity'] / hsp['align_len']) * 100 if hsp['align_len'] > 0 else 0
            }
            
            formatted_hits.append(formatted_hit)
        
        # Sort by bit score (highest first)
        formatted_hits.sort(key=lambda x: x['bit_score'], reverse=True)
        
    except KeyError as e:
        logger.error(f"Error parsing BLAST results: {str(e)}")
    
    return formatted_hits

def get_sequence_by_id(orf_id):
    """
    Get the full sequence and details for a given ORF ID
    
    Args:
        orf_id (str): The ORF ID to retrieve
        
    Returns:
        dict: Sequence information or None if not found
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
        SELECT os.*, o.organism_name 
        FROM orf_sequence os
        LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
        WHERE os.orf_id = ?
    ''', (orf_id,))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    else:
        return None
