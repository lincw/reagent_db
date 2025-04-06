"""
Simplified BLAST utility module for the Reagent Database application.
This module provides a more robust implementation with better error handling.
"""

import os
import subprocess
import tempfile
import sqlite3
import json
import logging
import time
import threading
import signal
from functools import wraps
import sys

from app import app, DB_PATH

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the BLAST database files
BLAST_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blast_db')

# Make sure the directory exists
os.makedirs(BLAST_DB_PATH, exist_ok=True)

# Timeout for BLAST commands (seconds)
BLAST_TIMEOUT = 120

def timeout_handler(func):
    """
    Decorator to handle timeouts for long-running functions.
    Uses a thread with a timeout to prevent hanging processes.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = [None]
        error = [None]
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                error[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(BLAST_TIMEOUT)
        
        if thread.is_alive():
            logger.error(f"Function {func.__name__} timed out after {BLAST_TIMEOUT} seconds")
            # Try to terminate any subprocess if needed
            for proc in kwargs.get('_processes', []):
                try:
                    if proc.poll() is None:  # If process is still running
                        proc.terminate()
                except:
                    pass
            return {
                'success': False,
                'error': f"Operation timed out after {BLAST_TIMEOUT} seconds"
            }
        
        if error[0]:
            logger.error(f"Error in {func.__name__}: {str(error[0])}")
            return {
                'success': False,
                'error': str(error[0])
            }
        
        return result[0]
    
    return wrapper

def check_blast_installed():
    """
    Check if BLAST+ tools are installed.
    
    Returns:
        bool: True if installed, False otherwise
    """
    try:
        # Set a short timeout for this check
        result = subprocess.run(
            ['blastn', '-version'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0:
            # Use a different approach to get the first line
            first_line = result.stdout.strip().split(os.linesep)[0]
            logger.info(f"BLAST+ installed: {first_line}")
            return True
        logger.error(f"BLAST command returned non-zero exit code: {result.returncode}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("BLAST version check timed out")
        return False
    except FileNotFoundError:
        logger.error("BLAST+ tools not found in PATH")
        return False
    except Exception as e:
        logger.error(f"Error checking BLAST installation: {str(e)}")
        return False

def check_blast_db_status():
    """
    Check if BLAST database files exist.
    
    Returns:
        bool: True if BLAST database exists, False otherwise
    """
    try:
        db_path = os.path.join(BLAST_DB_PATH, 'reagent_db_nucl.nsq')
        exists = os.path.exists(db_path)
        if exists:
            logger.info(f"BLAST database found at {db_path}")
        else:
            logger.info(f"BLAST database not found at {db_path}")
        return exists
    except Exception as e:
        logger.error(f"Error checking BLAST database status: {str(e)}")
        return False

@timeout_handler
def ensure_blast_db_exists():
    """
    Create BLAST database if it doesn't exist.
    Uses improved error handling and timeout protection.
    
    Returns:
        dict: Result with success status and message
    """
    # Check if BLAST is installed
    if not check_blast_installed():
        logger.error("BLAST+ tools are not installed. Cannot create database.")
        return {
            'success': False,
            'error': 'BLAST+ tools are not installed. Please install BLAST+ and try again.'
        }
    
    # Extract sequences from database
    try:
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
            return {
                'success': False,
                'error': 'No sequences found in the database to create BLAST database.'
            }
        
        logger.info(f"Found {len(sequences)} sequences in the database")
        
        # Path to the FASTA file for makeblastdb
        fasta_path = os.path.join(BLAST_DB_PATH, 'reagent_db_sequences.fasta')
        
        # Write sequences to FASTA file
        with open(fasta_path, 'w') as f:
            for seq_id, seq_name, sequence in sequences:
                # Format: >id|name
                name_value = seq_name or 'Unknown'
                f.write(f">{seq_id}|{name_value}\n")
                
                # Write sequence with line breaks every 60 characters
                for i in range(0, len(sequence), 60):
                    f.write(f"{sequence[i:i+60]}\n")
        
        logger.info(f"Wrote {len(sequences)} sequences to {fasta_path}")
        
        # Create BLAST database (nucleotide)
        cmd = [
            'makeblastdb', 
            '-in', fasta_path, 
            '-dbtype', 'nucl', 
            '-out', os.path.join(BLAST_DB_PATH, 'reagent_db_nucl'),
            '-parse_seqids'
        ]
        
        logger.info(f"Running makeblastdb command: {' '.join(cmd)}")
        
        # Store process for potential termination
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Track process for timeout handler
        _processes = [process]
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error creating BLAST database: {stderr}")
            return {
                'success': False,
                'error': f"Failed to create BLAST database: {stderr}"
            }
        
        logger.info("Successfully created nucleotide BLAST database")
        return {
            'success': True,
            'message': 'BLAST database created successfully'
        }
        
    except Exception as e:
        logger.exception(f"Error creating BLAST database: {str(e)}")
        return {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }

@timeout_handler
def run_blast_search(query_sequence, program='blastn', evalue=10, max_hits=50):
    """
    Run a BLAST search against the reagent database.
    With improved error handling and timeout protection.
    
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
            'error': 'BLAST+ tools are not installed. Please contact the administrator.'
        }
    
    # Check if BLAST database exists, create if not
    if not check_blast_db_status():
        db_result = ensure_blast_db_exists()
        if not db_result.get('success', False):
            return {
                'success': False,
                'error': f"Failed to create BLAST database: {db_result.get('error', 'Unknown error')}"
            }
    
    # Clean up the sequence (remove whitespace, numbers, etc.)
    clean_sequence = ''.join(c for c in query_sequence if c.isalpha())
    
    if not clean_sequence:
        return {
            'success': False,
            'error': 'Invalid sequence - sequence must contain valid nucleotide or amino acid characters'
        }
    
    # Create temporary file for query sequence
    temp_query_file = None
    try:
        # Use secure temp file creation
        temp_query_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_query_file.write(clean_sequence)
        temp_query_file.close()
        query_path = temp_query_file.name
        
        # Determine which database to use based on program
        db_path = os.path.join(BLAST_DB_PATH, 'reagent_db_nucl')
        
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
        
        # Create process with pipes for communication
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Track process for timeout handler
        _processes = [process]
        
        # Get output with timeout
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"BLAST error: {stderr}")
            return {
                'success': False,
                'error': f"BLAST search failed: {stderr}"
            }
        
        # Parse the JSON output
        try:
            blast_results = json.loads(stdout)
            logger.info("Successfully parsed BLAST results")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse BLAST JSON output: {str(e)}")
            logger.debug(f"BLAST stdout: {stdout[:500]}...")  # Log only first part to avoid huge logs
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
    
    except Exception as e:
        logger.exception(f"Unexpected error in BLAST search: {str(e)}")
        return {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }
    finally:
        # Clean up temporary file
        if temp_query_file:
            try:
                if os.path.exists(temp_query_file.name):
                    os.unlink(temp_query_file.name)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {str(e)}")

def format_blast_results(blast_json):
    """
    Format BLAST JSON results into a more user-friendly structure.
    
    Args:
        blast_json (dict): Raw BLAST JSON output
    
    Returns:
        list: Formatted hit information
    """
    formatted_hits = []
    
    try:
        # Check if we have results
        if 'BlastOutput2' not in blast_json:
            logger.warning("No 'BlastOutput2' key in BLAST results JSON")
            return formatted_hits
        
        # Navigate to the hits section
        report = blast_json['BlastOutput2'][0]['report']
        results = report['results']['search']
        
        # Check if we have hits
        if 'hits' not in results:
            logger.info("No hits found in BLAST results")
            return formatted_hits
        
        # Get ORF IDs to fetch HGNC symbols in bulk
        orf_ids = []
        hit_dict = {}
        
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
            
            # Add to ORF IDs list for later lookup
            orf_ids.append(orf_id)
            
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
            
            hit_dict[orf_id] = formatted_hit
        
        # Fetch HGNC symbols and organism names in one query
        if orf_ids:
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                
                # Check if human_gene table exists
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='human_gene'")
                human_gene_exists = c.fetchone() is not None
                
                # Create placeholders for SQL query
                placeholders = ','.join(['?'] * len(orf_ids))
                
                # Query for organism names (and HGNC symbols if available)
                if human_gene_exists:
                    c.execute(f'''
                        SELECT os.orf_id, h.hgnc_symbol, o.organism_name
                        FROM orf_sequence os
                        LEFT JOIN human_gene h ON os.orf_id = h.orf_id
                        LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                        WHERE os.orf_id IN ({placeholders})
                    ''', orf_ids)
                else:
                    c.execute(f'''
                        SELECT os.orf_id, o.organism_name
                        FROM orf_sequence os
                        LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                        WHERE os.orf_id IN ({placeholders})
                    ''', orf_ids)
                
                rows = c.fetchall()
                conn.close()
                
                # Create lookup dictionary
                for row in rows:
                    orf_id = str(row['orf_id'])
                    if orf_id in hit_dict:
                        # Set display name - use HGNC symbol if available
                        if 'hgnc_symbol' in row.keys() and row['hgnc_symbol']:
                            hit_dict[orf_id]['hgnc_symbol'] = row['hgnc_symbol']
                            hit_dict[orf_id]['display_name'] = row['hgnc_symbol']  # Use HGNC symbol as display name
                        else:
                            hit_dict[orf_id]['display_name'] = hit_dict[orf_id]['orf_name']  # Use ORF name if no HGNC symbol
                        
                        if row['organism_name']:
                            hit_dict[orf_id]['organism'] = row['organism_name']
            except Exception as e:
                logger.error(f"Error enriching BLAST results with HGNC symbols: {str(e)}")
        
        # Convert dictionary to list and sort by bit score
        formatted_hits = list(hit_dict.values())
        formatted_hits.sort(key=lambda x: x['bit_score'], reverse=True)
        
    except KeyError as e:
        logger.error(f"Error parsing BLAST results - missing key: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error formatting BLAST results: {str(e)}")
    
    return formatted_hits

def get_sequence_by_id(orf_id):
    """
    Get the full sequence and details for a given ORF ID
    
    Args:
        orf_id (str): The ORF ID to retrieve
        
    Returns:
        dict: Sequence information or None if not found
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Check if the human_gene table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='human_gene'")
        human_gene_exists = c.fetchone() is not None
        
        if human_gene_exists:
            c.execute('''
                SELECT os.*, o.organism_name, h.hgnc_symbol 
                FROM orf_sequence os
                LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
                LEFT JOIN human_gene h ON os.orf_id = h.orf_id
                WHERE os.orf_id = ?
            ''', (orf_id,))
        else:
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
    except Exception as e:
        logger.exception(f"Error getting sequence by ID: {str(e)}")
        return None
