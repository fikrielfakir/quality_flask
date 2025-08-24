#!/usr/bin/env python3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the main Flask application
from app import app

if __name__ == "__main__":
    # ALWAYS serve the app on port 5000
    # this serves the API.
    # It is the only port that is not firewalled.
    port = 5000
    host = "0.0.0.0"
    
    logger.info(f"Starting Dersa EcoQuality on port {port}")
    app.run(host=host, port=port, debug=os.getenv("FLASK_ENV") == "development")
