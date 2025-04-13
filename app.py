from flask import Flask, jsonify
from database import db, get_db
from routes.blast_routes import blast_bp
import os

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///reagent_db.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(blast_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    @app.route('/api/orf_sources', methods=['GET'])
    def api_orf_sources():
        """API endpoint to get all ORF sources for dropdowns"""
        try:
            # Connect to the database
            conn = get_db()
            cursor = conn.cursor()
            
            # Query all sources
            cursor.execute('''
                SELECT source_id, source_name 
                FROM orf_sources 
                ORDER BY source_name
            ''')
            
            sources = [{"source_id": row[0], "source_name": row[1]} for row in cursor.fetchall()]
            
            # Close the connection
            conn.close()
            
            return jsonify({"success": True, "sources": sources})
        except Exception as e:
            app.logger.error(f"Error fetching ORF sources: {e}")
            return jsonify({"success": False, "message": str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
