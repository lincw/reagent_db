"""
Routes for managing application configuration
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
import os
import shutil
import sqlite3
from app import app, DB_PATH
import sys

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import load_config, save_config, get_db_path, get_onedrive_path

@app.route('/configuration', methods=['GET'])
def view_configuration():
    """Render the configuration page"""
    config = load_config()
    
    # Detect OneDrive path if not set
    if not config['onedrive_path']:
        config['onedrive_path'] = get_onedrive_path() or ''
    
    return render_template('configuration.html', config=config, current_db_path=DB_PATH)

@app.route('/update_configuration', methods=['POST'])
def update_configuration():
    """Update configuration settings"""
    config = load_config()
    
    # Update configuration values
    config['use_onedrive'] = request.form.get('use_onedrive') == 'on'
    
    # Only update OneDrive path if provided
    onedrive_path = request.form.get('onedrive_path', '').strip()
    if onedrive_path:
        config['onedrive_path'] = onedrive_path
    
    # Save configuration
    save_config(config)
    
    # Check if database needs to be moved
    old_db_path = DB_PATH
    new_db_path = get_db_path()
    
    # If paths are different and old database exists, offer to migrate
    if old_db_path != new_db_path and os.path.exists(old_db_path):
        flash('Configuration updated. Database location has changed.')
        return redirect(url_for('migrate_database', 
                               source=old_db_path, 
                               destination=new_db_path))
    
    flash('Configuration updated successfully.')
    return redirect(url_for('view_configuration'))

@app.route('/migrate_database', methods=['GET'])
def migrate_database_page():
    """Show the database migration confirmation page"""
    source = request.args.get('source', '')
    destination = request.args.get('destination', '')
    
    if not source or not destination:
        flash('Invalid migration parameters.')
        return redirect(url_for('view_configuration'))
    
    return render_template('migrate_database.html', 
                          source=source, 
                          destination=destination)

@app.route('/perform_migration', methods=['POST'])
def perform_migration():
    """Perform database migration"""
    source = request.form.get('source', '')
    destination = request.form.get('destination', '')
    
    if not source or not destination or not os.path.exists(source):
        flash('Invalid migration parameters or source database not found.')
        return redirect(url_for('view_configuration'))
    
    try:
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Copy database file
        shutil.copy2(source, destination)
        
        # Verify the copied database
        conn = sqlite3.connect(destination)
        conn.close()
        
        flash('Database migrated successfully.')
        
        # Option to remove original database
        if request.form.get('remove_original') == 'on':
            try:
                os.remove(source)
                flash('Original database removed.')
            except Exception as e:
                flash(f'Could not remove original database: {str(e)}')
        
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error during database migration: {str(e)}')
        return redirect(url_for('view_configuration'))

@app.route('/check_path', methods=['POST'])
def check_path():
    """API endpoint to check if a path exists and is writable"""
    path = request.json.get('path', '')
    
    if not path:
        return jsonify({'valid': False, 'message': 'No path provided'})
    
    # Check if path exists
    exists = os.path.exists(path)
    
    # Check if directory is writable
    writable = False
    if exists and os.path.isdir(path):
        try:
            test_file = os.path.join(path, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            writable = True
        except:
            writable = False
    
    return jsonify({
        'valid': exists and writable,
        'exists': exists,
        'writable': writable,
        'message': 'Path is valid and writable' if (exists and writable) else 'Path is invalid or not writable'
    })
