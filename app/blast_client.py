"""
BLAST client module for the Reagent Database application.
This module handles communication with the separate BLAST service.
"""

import os
import requests
import json
import logging
import sqlite3
from app import app, DB_PATH

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get BLAST service URL from environment variable or use default
BLAST_SERVICE_URL = os.environ.get('BLAST_SERVICE_URL', 'http://localhost:5001')

def check_blast_service_status():
    """
    Check if the BLAST service is running and available.
    
    Returns:
        dict: Status information from the BLAST service
    """
    try:
        response = requests.get(f"{BLAST_SERVICE_URL}/status", timeout=5)
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error connecting to BLAST service: {str(e)}")
        return {
            'status': 'offline',
            'error': str(e),
            'blast_installed': False,
            'blast_db_exists': False
        }

def update_blast_database():
    """
    Update the BLAST database with sequences from the local SQLite database.
    
    Returns:
        dict: Result of the database creation
    """
    try:
        # Extract sequences from the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT os.orf_id, os.orf_name, os.orf_sequence, o.organism_name
            FROM orf_sequence os
            LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            WHERE os.orf_sequence IS NOT NULL AND os.orf_sequence != ''
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            logger.warning("No sequences found in the database")
            return {
                'success': False,
                'error': 'No sequences found in the database'
            }
        
        # Format sequences for the BLAST service
        sequences = []
        for row in rows:
            orf_id, orf_name, orf_sequence, organism_name = row
            sequences.append({
                'id': str(orf_id),
                'name': orf_name or '',
                'organism': organism_name or '',
                'sequence': orf_sequence
            })
        
        # Send sequences to the BLAST service
        response = requests.post(
            f"{BLAST_SERVICE_URL}/create_db_from_sequences",
            data={
                'db_name': 'reagent_db',
                'db_type': 'nucl',
                'sequences': json.dumps(sequences)
            },
            timeout=30  # Longer timeout for database creation
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                logger.info(f"BLAST database created with {len(sequences)} sequences")
            return result
        else:
            logger.error(f"Error from BLAST service: {response.text}")
            return {
                'success': False,
                'error': f"Error from BLAST service: {response.text}"
            }
    
    except requests.RequestException as e:
        logger.error(f"Error connecting to BLAST service: {str(e)}")
        return {
            'success': False,
            'error': f"Error connecting to BLAST service: {str(e)}"
        }
    except Exception as e:
        logger.exception(f"Error updating BLAST database: {str(e)}")
        return {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }

def run_blast_search(query_sequence, program='blastn', evalue=10, max_hits=50):
    """
    Run a BLAST search using the BLAST service.
    
    Args:
        query_sequence (str): The query sequence to search
        program (str): BLAST program to use ('blastn', 'blastp', 'blastx', 'tblastn', 'tblastx')
        evalue (float): E-value threshold
        max_hits (int): Maximum number of hits to return
    
    Returns:
        dict: BLAST results in a structured format
    """
    try:
        # Send BLAST search request to the service
        response = requests.post(
            f"{BLAST_SERVICE_URL}/blast",
            data={
                'sequence': query_sequence,
                'program': program,
                'evalue': str(evalue),
                'max_hits': str(max_hits),
                'db_name': 'reagent_db'
            },
            timeout=30  # Longer timeout for BLAST search
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result['success']:
                # Enrich results with additional data from the database
                if 'results' in result:
                    enrich_blast_results(result['results'])
                
                logger.info(f"BLAST search found {len(result.get('results', []))} hits")
            
            return result
        else:
            logger.error(f"Error from BLAST service: {response.text}")
            return {
                'success': False,
                'error': f"Error from BLAST service: {response.text}"
            }
    
    except requests.RequestException as e:
        logger.error(f"Error connecting to BLAST service: {str(e)}")
        return {
            'success': False,
            'error': f"Error connecting to BLAST service: {str(e)}"
        }
    except Exception as e:
        logger.exception(f"Error running BLAST search: {str(e)}")
        return {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }

def enrich_blast_results(results):
    """
    Enrich BLAST results with additional information from the database.
    
    Args:
        results (list): List of BLAST hit results to enrich
    """
    if not results:
        return
    
    try:
        # Get ORF IDs from results
        orf_ids = [hit['orf_id'] for hit in results]
        
        if not orf_ids:
            return
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Prepare placeholders for SQL query
        placeholders = ','.join(['?'] * len(orf_ids))
        
        # Get additional ORF information
        c.execute(f'''
            SELECT os.orf_id, os.orf_annotation, o.organism_name
            FROM orf_sequence os
            LEFT JOIN organisms o ON os.orf_organism_id = o.organism_id
            WHERE os.orf_id IN ({placeholders})
        ''', orf_ids)
        
        rows = c.fetchall()
        conn.close()
        
        # Create lookup dictionary
        orf_data = {str(row['orf_id']): dict(row) for row in rows}
        
        # Enrich results
        for hit in results:
            orf_id = hit['orf_id']
            if orf_id in orf_data:
                if not hit.get('organism') and orf_data[orf_id]['organism_name']:
                    hit['organism'] = orf_data[orf_id]['organism_name']
                if not hit.get('annotation') and orf_data[orf_id]['orf_annotation']:
                    hit['annotation'] = orf_data[orf_id]['orf_annotation']
    
    except Exception as e:
        logger.exception(f"Error enriching BLAST results: {str(e)}")

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
