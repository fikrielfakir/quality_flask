#!/usr/bin/env python3
"""
Dersa EcoQuality - Desktop Application Launcher
Main entry point for the local desktop application
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dersa_ecoquality.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    print("=" * 60)
    print("  DERSA ECOQUALITY - DESKTOP APPLICATION")
    print("  Quality Management System for Ceramic Manufacturing")
    print("  Ceramica Dersa - Tétouan, Morocco")
    print("=" * 60)
    print()
    
    logger.info("Starting Dersa EcoQuality Desktop Application")
    
    try:
        # Import and run the local Flask application
        from app_local import app
        
        print("✓ Application initialized successfully")
        print("✓ Database: SQLite (Local)")
        print("✓ Server starting on: http://localhost:5000")
        print()
        print("Default login credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print()
        print("To stop the application, press Ctrl+C")
        print("-" * 60)
        print()
        
        # Run the Flask application
        app.run(
            host='127.0.0.1',  # Localhost only for desktop app
            port=5000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("  SHUTTING DOWN DERSA ECOQUALITY")
        print("=" * 60)
        logger.info("Application stopped by user")
        
    except ImportError as e:
        print(f"✗ Import Error: {e}")
        print("Please ensure all required packages are installed:")
        print("  pip install flask flask-cors bcrypt")
        logger.error(f"Import error: {e}")
        
    except Exception as e:
        print(f"✗ Application Error: {e}")
        logger.error(f"Application error: {e}")
        
    finally:
        print("Thank you for using Dersa EcoQuality!")

if __name__ == "__main__":
    main()