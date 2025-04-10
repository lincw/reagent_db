from flask import render_template, jsonify
import sqlite3

from app import app, DB_PATH

def get_database_stats():
    """Get statistics about the database collections"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        stats = {}
        
        # Check if the orf_id column exists in organisms table
        cursor.execute("PRAGMA table_info(organisms)")
        columns = [column[1] for column in cursor.fetchall()]  # column[1] is the name
        has_orf_id = 'orf_id' in columns
        
        # Count ORF sequences
        cursor.execute('SELECT COUNT(*) FROM orf_sequence')
        stats['orf_sequences'] = cursor.fetchone()[0]
        
        # Include these for backward compatibility
        cursor.execute('SELECT COUNT(*) FROM orf_position')
        stats['orf_positions'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT orf_id) FROM orf_position')
        stats['unique_positioned_orfs'] = cursor.fetchone()[0]
        
        # Count plasmids
        cursor.execute('SELECT COUNT(*) FROM plasmid')
        stats['plasmids'] = cursor.fetchone()[0]
        
        # Count unique organisms
        cursor.execute('SELECT COUNT(DISTINCT organism_name) FROM organisms')
        stats['organisms'] = cursor.fetchone()[0]
        
        # Count organisms with linked ORFs if the column exists
        if has_orf_id:
            cursor.execute('SELECT COUNT(*) FROM organisms WHERE orf_id IS NOT NULL')
            stats['linked_organisms'] = cursor.fetchone()[0]
        else:
            # No orf_id column yet, use the reference in orf_sequence for now
            cursor.execute('SELECT COUNT(DISTINCT orf_organism_id) FROM orf_sequence WHERE orf_organism_id IS NOT NULL')
            stats['linked_organisms'] = cursor.fetchone()[0]
        
        # Count unique freezers
        cursor.execute('SELECT COUNT(DISTINCT freezer_location) FROM freezer')
        stats['freezers'] = cursor.fetchone()[0]
        
        # Count unique ORF sources
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orf_sources'")
        orf_sources_table_exists = cursor.fetchone()
        
        if orf_sources_table_exists:
            cursor.execute('SELECT COUNT(DISTINCT source_name) FROM orf_sources')
            stats['orf_sources'] = cursor.fetchone()[0]
        else:
            stats['orf_sources'] = 0
        
        # Count yeast ORF positions if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='yeast_orf_position'")
        yeast_orf_table_exists = cursor.fetchone()
        
        if yeast_orf_table_exists:
            # Check if position_type column exists
            cursor.execute("PRAGMA table_info(yeast_orf_position)")
            columns = [column[1] for column in cursor.fetchall()]
            has_position_type = 'position_type' in columns
            
            # Get total count
            cursor.execute('SELECT COUNT(*) FROM yeast_orf_position')
            stats['yeast_positions'] = cursor.fetchone()[0]
            
            # Get counts by type if the column exists
            if has_position_type:
                cursor.execute("SELECT COUNT(*) FROM yeast_orf_position WHERE position_type = 'AD' OR position_type IS NULL")
                stats['yeast_ad_positions'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM yeast_orf_position WHERE position_type = 'DB'")
                stats['yeast_db_positions'] = cursor.fetchone()[0]
            else:
                # If position_type doesn't exist, all are considered AD
                stats['yeast_ad_positions'] = stats['yeast_positions']
                stats['yeast_db_positions'] = 0
        else:
            stats['yeast_positions'] = 0
            stats['yeast_ad_positions'] = 0
            stats['yeast_db_positions'] = 0
        
        # Get last update timestamp
        cursor.execute("SELECT datetime('now')")
        stats['current_time'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    except Exception as e:
        import traceback
        print(f"Error in get_database_stats: {e}")
        print(traceback.format_exc())
        # Return at least some data in case of error
        return {
            'orf_sequences': 0,
            'orf_positions': 0,
            'unique_positioned_orfs': 0,
            'plasmids': 0,
            'organisms': 0,
            'linked_organisms': 0,
            'freezers': 0,
            'orf_sources': 0,
            'yeast_positions': 0,
            'yeast_ad_positions': 0,
            'yeast_db_positions': 0,
            'current_time': 'Error occurred'
        }

@app.route('/')
def index():
    try:
        stats = get_database_stats()
    except Exception as e:
        import traceback
        print(f"Error getting stats for index page: {e}")
        print(traceback.format_exc())
        # Provide default empty stats if database access fails
        stats = {
            'orf_sequences': 0,
            'plasmids': 0,
            'organisms': 0,
            'linked_organisms': 0,
            'orf_sources': 0,
            'current_time': 'Database Error - Use Refresh button'
        }
    return render_template('index.html', stats=stats)

@app.route('/batch_search')
def batch_search_page():
    """Render the batch search page"""
    return render_template('batch_search.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint to get current database statistics"""
    try:
        # Print the database path to debug potential connection issues
        print(f"Accessing database at: {DB_PATH}")
        
        stats = get_database_stats()
        # Add a timestamp for client-side validation
        stats['timestamp'] = sqlite3.connect(DB_PATH).execute("SELECT strftime('%s', 'now')").fetchone()[0]
        
        # Print the stats to server log for debugging
        print(f"Database stats: {stats}")
        
        return jsonify(stats)
    except Exception as e:
        import traceback
        print(f"Error in api_stats: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': 'Failed to fetch database statistics',
            'message': str(e),
            'current_time': sqlite3.connect(DB_PATH).execute("SELECT datetime('now')").fetchone()[0]
        }), 500

@app.route('/gene-nomenclature')
def gene_nomenclature():
    """Render the gene nomenclature explanation page"""
    return render_template('gene_nomenclature.html')
