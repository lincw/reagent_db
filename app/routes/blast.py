"""
Routes for BLAST sequence searches in the Reagent Database application.
"""

from flask import render_template, request, jsonify, flash
import logging

from app import app
from app.blast_simple import check_blast_db_status, check_blast_installed, ensure_blast_db_exists
from app.blast_simple import run_blast_search, get_sequence_by_id

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/blast')
def blast_page():
    """Render the BLAST search page"""
    # Check if BLAST is installed
    blast_installed = check_blast_installed()
    if not blast_installed:
        flash('BLAST+ tools are not installed on the server. Please contact the administrator.', 'warning')
    
    # Check if BLAST database is ready
    blast_ready = check_blast_db_status()
    if not blast_ready and blast_installed:
        flash('BLAST database is not ready. Use the "Update BLAST Database" button to create it.', 'info')
    
    return render_template('blast.html', blast_ready=blast_ready, blast_installed=blast_installed)

@app.route('/api/blast_search', methods=['POST'])
def api_blast_search():
    """API endpoint to run a BLAST search"""
    try:
        # Get parameters from the request
        query_sequence = request.form.get('sequence', '')
        program = request.form.get('program', 'blastn')
        evalue = float(request.form.get('evalue', 10))
        max_hits = int(request.form.get('max_hits', 50))
        
        logger.info(f"BLAST search with program={program}, evalue={evalue}")
        
        if not query_sequence:
            return jsonify({
                'success': False,
                'error': 'No sequence provided'
            })
        
        # Run the BLAST search
        results = run_blast_search(
            query_sequence=query_sequence,
            program=program,
            evalue=evalue,
            max_hits=max_hits
        )
        
        if results.get('success', False) and 'results' in results:
            # Get additional details for each hit from the database
            hits = results['results']
            # Log the number of results
            hit_count = len(hits)
            logger.info(f"BLAST search found {hit_count} hits")
        
        return jsonify(results)
    
    except Exception as e:
        logger.exception(f"Error in BLAST search: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        })

@app.route('/api/blast_sequence/<orf_id>')
def api_blast_sequence(orf_id):
    """API endpoint to get the full sequence for a given ORF ID"""
    try:
        sequence_data = get_sequence_by_id(orf_id)
        
        if sequence_data:
            return jsonify({
                'success': True,
                'sequence': sequence_data
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Sequence not found for ID: {orf_id}"
            })
    except Exception as e:
        logger.exception(f"Error retrieving sequence: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"An error occurred: {str(e)}"
        })

@app.route('/api/update_blast_db')
def api_update_blast_db():
    """API endpoint to manually update the BLAST database"""
    try:
        if not check_blast_installed():
            flash('BLAST+ tools are not installed on the server. Please contact the administrator.', 'error')
            return jsonify({
                'success': False,
                'message': 'BLAST+ tools are not installed on the server.'
            })
            
        result = ensure_blast_db_exists()
        
        if result.get('success', False):
            flash('BLAST database updated successfully')
            return jsonify({
                'success': True,
                'message': 'BLAST database updated successfully'
            })
        else:
            flash(f"Failed to update BLAST database: {result.get('error', 'Unknown error')}", 'error')
            return jsonify({
                'success': False,
                'message': f"Failed to update BLAST database: {result.get('error', 'Unknown error')}"
            })
    except Exception as e:
        logger.exception(f"Error updating BLAST database: {str(e)}")
        flash(f'Error updating BLAST database: {str(e)}', 'error')
        return jsonify({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        })
