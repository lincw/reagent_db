from flask import Blueprint, request, render_template, jsonify
from services.blast_service import BlastService
import subprocess
import tempfile
import os

blast_bp = Blueprint('blast', __name__)
blast_service = BlastService()

@blast_bp.route('/blast', methods=['GET', 'POST'])
def blast_search():
    """Handle BLAST search requests."""
    if request.method == 'POST':
        sequence = request.form.get('sequence', '')
        database = request.form.get('database', 'nucleotide')
        
        # Run BLAST search
        results = run_blast(sequence, database)
        
        # Process results
        hits = blast_service.process_results(results)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'hits': hits})
        
        return render_template('blast_results.html', blast_results={'hits': hits})
    
    return render_template('blast_form.html')

def run_blast(sequence, database):
    """Run BLAST search against the selected database."""
    # Write sequence to temporary file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp.write(sequence)
        temp_path = temp.name
    
    try:
        # Run BLAST command
        blast_cmd = [
            'blastn', 
            '-query', temp_path,
            '-db', f'databases/{database}',
            '-outfmt', '5'  # XML output
        ]
        
        process = subprocess.Popen(
            blast_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate(timeout=300)  # 5-minute timeout
        
        if process.returncode != 0:
            raise Exception(f"BLAST error: {stderr.decode('utf-8')}")
        
        return stdout.decode('utf-8')
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
