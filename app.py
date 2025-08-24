"""
Dersa EcoQuality - Main Flask Application
Pure Flask web application for ceramic tile quality management
"""

from flask import Flask, render_template, session, redirect, url_for
from data.database import DatabaseManager
import os
import logging

# Import route blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.production import production_bp
from routes.quality import quality_bp
from routes.energy import energy_bp
from routes.waste import waste_bp
from routes.raw_materials import raw_materials_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.secret_key = 'dersa_ecoquality_secret_key_2025'
    
    # Initialize database
    try:
        db = DatabaseManager()
        db.seed_initial_data()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise RuntimeError(f"Cannot start application without database: {e}")
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(quality_bp)
    app.register_blueprint(energy_bp)
    app.register_blueprint(waste_bp)
    app.register_blueprint(raw_materials_bp)
    
    # Template filters for better display
    @app.template_filter('format_date')
    def format_date_filter(date_obj):
        """Format date for templates"""
        from utils.helpers import format_date
        return format_date(date_obj)
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(datetime_obj):
        """Format datetime for templates"""
        from utils.helpers import format_datetime
        return format_datetime(datetime_obj)
    
    @app.template_filter('status_badge')
    def status_badge_filter(status):
        """Get CSS class for status badges"""
        from utils.helpers import get_status_badge_class
        return get_status_badge_class(status)
    
    @app.template_filter('priority_badge')
    def priority_badge_filter(priority):
        """Get CSS class for priority badges"""
        from utils.helpers import get_priority_badge_class
        return get_priority_badge_class(priority)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    # Context processors for templates
    @app.context_processor
    def inject_user():
        """Inject user session data into all templates"""
        return {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'user_role': session.get('role'),
            'full_name': session.get('full_name')
        }
    
    return app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # ALWAYS serve the app on port 5000
    # this serves the API.
    # It is the only port that is not firewalled.
    port = 5000
    host = '0.0.0.0'
    
    logger.info(f"serving on port {port}")
    app.run(host=host, port=port, debug=os.getenv('FLASK_ENV') == 'development')