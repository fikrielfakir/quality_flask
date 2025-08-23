#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize local database and seed data
try:
    from local_database import LocalDatabaseManager
    
    logger.info("Initializing Dersa EcoQuality local database...")
    db = LocalDatabaseManager()
    
    # Check if database is empty and seed if needed
    existing_standards = db.execute_query("SELECT COUNT(*) as count FROM iso_standards")
    if not existing_standards or existing_standards[0]['count'] == 0:
        logger.info("Database appears empty, running seed data...")
        db.seed_initial_data()
    else:
        logger.info("Database already contains data, skipping seed")
    
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    # Continue anyway, app might still work

# Import the local web application
from app_local import app

if __name__ == "__main__":
    # ALWAYS serve the app on port 5000
    # this serves the API.
    # It is the only port that is not firewalled.
    port = 5000
    host = "0.0.0.0"
    
    logger.info(f"Starting Dersa EcoQuality on port {port}")
    app.run(host=host, port=port, debug=os.getenv("FLASK_ENV") == "development")
