#!/usr/bin/env python3
"""
Dersa EcoQuality - Application Entry Point
Run the Flask application server
"""

from app import create_app
import logging

if __name__ == '__main__':
    try:
        app = create_app()
        logger = logging.getLogger(__name__)
        logger.info("Starting Dersa EcoQuality on port 5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Failed to start application: {e}")
        raise