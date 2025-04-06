"""
BLAST Service - A standalone microservice for running BLAST searches.
This service is designed to be run separately from the main Reagent DB application.
"""

from flask import Flask, request, jsonify
import os
import subprocess
import tempfile
import json
import logging
import shutil
from werkzeug.utils import secure_filename

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
BLAST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'fasta', 'fa', 'txt'}

# Create necessary directories
os.makedirs(BLAST_DB_PATH, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Check if BLAST is installed
def check_blast_installed():
    """Check if BLAST+ tools are installed."""
    try:
        result = subprocess.run(['blastn', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"BLAST+ installed: {result.stdout.splitlines()[0]}")
            return True
        return False
    except FileNotFoundError:
        logger.error("BLAST+ tools not found in PATH")
        return False
    except Exception as e:
        logger.error(f"Error checking BLAST installation: {str(e)}")
        return False

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/status', methods=['GET'])
def status():
    """Check the status of the BLAST service."""
    blast_installed = check_blast_installed()
    
    # Check if any BLAST database exists
    blast_db_exists = False
    if os.path.exists(BLAST_DB_PATH):
        db_files = [f for f in os.listdir(BLAST_DB_PATH) if f.endswith('.nsq')]
        blast_db_exists = len(db_files) > 0
    
    return jsonify({
        'status': 'online',
        'blast_installed': blast_installed,
        'blast_db_exists': blast_db_exists,
        'databases': [f.replace('.nsq', '') for f in os.listdir(BLAST_DB_PATH) if f.endswith('.nsq')] if blast_db_exists else []
    })

@app.route('/create_db', methods=['POST'])
def create_db():
    """Create a BLAST database from a FASTA file."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': f'File type not allowed. Supported types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    try:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Get database name from request or use filename
        db_name = request.form.get('db_name', filename.split('.')[0])
        db_path = os.path.join(BLAST_DB_PATH, db_name)
        
        # Get database type from request or default to nucleotide
        db_type = request.form.get('db_type', 'nucl')
        if db_type not in ['nucl', 'prot']:
            return jsonify({'success': False, 'error': 'Invalid database type. Use "nucl" or "prot"'}), 400
        
        # Create the BLAST database
        cmd = [
            'makeblastdb', 
            '-in', filepath, 
            '-dbtype', db_type, 
            '-out', db_path,
            '-parse_seqids'
        ]
        
        logger.info(f"Running makeblastdb command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"makeblastdb error: {result.stderr}")
            return jsonify({
                'success': False, 
                'error': f"Failed to create BLAST database: {result.stderr}"
            }), 500
        
        logger.info(f"Successfully created BLAST database: {db_name}")
        return jsonify({
            'success': True,
            'message': f"Successfully created BLAST database: {db_name}",
            'db_name': db_name,
            'db_path': db_path
        })
        
    except Exception as e:
        logger.exception(f"Error creating BLAST database: {str(e)}")
        return jsonify({'success': False, 'error': f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/create_db_from_sequences', methods=['POST'])
def create_db_from_sequences():
    """Create a BLAST database from a list of sequences in JSON format."""
    try:
        # Get database name from request or use default
        db_name = request.form.get('db_name', 'custom_db')
        db_path = os.path.join(BLAST_DB_PATH, db_name)
        
        # Get database type from request or default to nucleotide
        db_type = request.form.get('db_type', 'nucl')
        if db_type not in ['nucl', 'prot']:
            return jsonify({'success': False, 'error': 'Invalid database type. Use "nucl" or "prot"'}), 400
        
        # Get sequences from request
        if 'sequences' not in request.form:
            return jsonify({'success': False, 'error': 'No sequences provided'}), 400
        
        try:
            sequences = json.loads(request.form['sequences'])
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Invalid JSON format for sequences'}), 400
        
        if not sequences:
            return jsonify({'success': False, 'error': 'Empty sequence list'}), 400
        
        # Create a temporary FASTA file
        fasta_path = os.path.join(UPLOAD_FOLDER, f"{db_name}.fasta")
        with open(fasta_path, 'w') as f:
            for seq in sequences:
                if 'id' not in seq or 'sequence' not in seq:
                    return jsonify({'success': False, 'error': 'Each sequence must have "id" and "sequence" fields'}), 400
                
                # Write in FASTA format
                f.write(f">{seq['id']}|{seq.get('name', '')}|{seq.get('organism', '')}\n")
                
                # Write sequence with line breaks every 60 characters
                sequence = seq['sequence']
                for i in range(0, len(sequence), 60):
                    f.write(sequence[i:i+60] + "\n")
        
        # Create the BLAST database
        cmd = [
            'makeblastdb', 
            '-in', fasta_path, 
            '-dbtype', db_type, 
            '-out', db_path,
            '-parse_seqids'
        ]
        
        logger.info(f"Running makeblastdb command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"makeblastdb error: {result.stderr}")
            return jsonify({
                'success': False, 
                'error': f"Failed to create BLAST database: {result.stderr}"
            }), 500
        
        logger.info(f"Successfully created BLAST database: {db_name}")
        return jsonify({
            'success': True,
            'message': f"Successfully created BLAST database: {db_name}",
            'db_name': db_name,
            'db_path': db_path,
            'sequence_count': len(sequences)
        })
        
    except Exception as e:
        logger.exception(f"Error creating BLAST database from sequences: {str(e)}")
        return jsonify({'success': False, 'error': f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/blast', methods=['POST'])
def blast_search():
    """Run a BLAST search against a database."""
    try:
        # Get parameters from the request
        query_sequence = request.form.get('sequence', '')
        if not query_sequence:
            return jsonify({'success': False, 'error': 'No query sequence provided'}), 400
        
        # Get BLAST program
        program = request.form.get('program', 'blastn')
        valid_programs = ['blastn', 'blastp', 'blastx', 'tblastn', 'tblastx']
        if program not in valid_programs:
            return jsonify({'success': False, 'error': f'Invalid BLAST program. Supported programs: {", ".join(valid_programs)}'}), 400
        
        # Get other parameters
        db_name = request.form.get('db_name', '')
        if not db_name:
            # Get the first available database if none specified
            db_files = [f.replace('.nsq', '') for f in os.listdir(BLAST_DB_PATH) if f.endswith('.nsq')]
            if not db_files:
                return jsonify({'success': False, 'error': 'No BLAST databases available'}), 400
            db_name = db_files[0]
        
        db_path = os.path.join(BLAST_DB_PATH, db_name)
        
        # Check if the database exists
        if not os.path.exists(f"{db_path}.nsq"):
            return jsonify({'success': False, 'error': f'BLAST database not found: {db_name}'}), 404
        
        evalue = float(request.form.get('evalue', 10))
        max_hits = int(request.form.get('max_hits', 50))
        
        # Clean the sequence (remove whitespace, numbers, etc.)
        clean_sequence = ''.join(c for c in query_sequence if c.isalpha())
        
        if not clean_sequence:
            return jsonify({
                'success': False,
                'error': 'Invalid sequence - sequence must contain valid nucleotide or amino acid characters'
            }), 400
        
        # Create a temporary file for the query sequence
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as query_file:
            query_file.write(clean_sequence)
            query_path = query_file.name
        
        try:
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
                return jsonify({
                    'success': False,
                    'error': f"Failed to parse BLAST results: {str(e)}"
                }), 500
            
            # Format results for display
            formatted_results = format_blast_results(blast_results)
            
            return jsonify({
                'success': True,
                'results': formatted_results,
                'raw_results': blast_results
            })
            
        except subprocess.CalledProcessError as e:
            logger.error(f"BLAST error: {e.stderr}")
            return jsonify({
                'success': False,
                'error': f"BLAST search failed: {e.stderr}"
            }), 500
        finally:
            # Clean up temporary file
            try:
                os.unlink(query_path)
            except:
                pass
                
    except Exception as e:
        logger.exception(f"Error in BLAST search: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }), 500

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
            
            # Parse the ID|Name|Organism format
            parts = hit_title.split('|', 2)
            if len(parts) >= 3:
                orf_id = parts[0]
                orf_name = parts[1]
                organism = parts[2]
            elif len(parts) == 2:
                orf_id = parts[0]
                orf_name = parts[1]
                organism = ''
            else:
                orf_id = hit_id
                orf_name = hit_title
                organism = ''
            
            # Get the best HSP (High-scoring Segment Pair)
            hsp = hit['hsps'][0]
            
            formatted_hit = {
                'orf_id': orf_id,
                'orf_name': orf_name,
                'organism': organism,
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

@app.route('/delete_db/<db_name>', methods=['DELETE'])
def delete_db(db_name):
    """Delete a BLAST database."""
    try:
        db_path = os.path.join(BLAST_DB_PATH, db_name)
        
        # Check if the database exists
        if not os.path.exists(f"{db_path}.nsq"):
            return jsonify({'success': False, 'error': f'BLAST database not found: {db_name}'}), 404
        
        # Get all files with the database name prefix
        db_files = [f for f in os.listdir(BLAST_DB_PATH) if f.startswith(f"{db_name}.")]
        
        for file in db_files:
            os.remove(os.path.join(BLAST_DB_PATH, file))
            
        logger.info(f"Successfully deleted BLAST database: {db_name}")
        return jsonify({
            'success': True,
            'message': f"Successfully deleted BLAST database: {db_name}"
        })
        
    except Exception as e:
        logger.exception(f"Error deleting BLAST database: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }), 500

@app.route('/list_dbs', methods=['GET'])
def list_dbs():
    """List all available BLAST databases."""
    try:
        # Get all .nsq files (nucleotide database index files)
        nucl_dbs = [f.replace('.nsq', '') for f in os.listdir(BLAST_DB_PATH) if f.endswith('.nsq')]
        
        # Get all .psq files (protein database index files)
        prot_dbs = [f.replace('.psq', '') for f in os.listdir(BLAST_DB_PATH) if f.endswith('.psq')]
        
        return jsonify({
            'success': True,
            'databases': {
                'nucleotide': nucl_dbs,
                'protein': prot_dbs,
                'all': sorted(list(set(nucl_dbs + prot_dbs)))
            }
        })
        
    except Exception as e:
        logger.exception(f"Error listing BLAST databases: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Check if BLAST is installed on startup
    blast_installed = check_blast_installed()
    if not blast_installed:
        logger.warning("BLAST+ tools are not installed. Some functionality will be limited.")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)
