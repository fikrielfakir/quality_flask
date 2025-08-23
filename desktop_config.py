"""
Dersa EcoQuality - Desktop Application Configuration
Configuration for packaging Flask app as desktop executable
"""

import os
import sys
import webbrowser
import threading
import time
import logging
from app_dersa import app

logger = logging.getLogger(__name__)

class DesktopApp:
    def __init__(self):
        self.port = 5000
        self.host = '127.0.0.1'  # Use localhost for desktop app
        self.url = f'http://{self.host}:{self.port}'
        self.server_thread = None
        
    def start_server(self):
        """Start Flask server in a separate thread"""
        try:
            logger.info(f"Starting Dersa EcoQuality server on {self.url}")
            app.run(host=self.host, port=self.port, debug=False, threaded=True)
        except Exception as e:
            logger.error(f"Server startup failed: {e}")
    
    def open_browser(self):
        """Open the default web browser after a delay"""
        time.sleep(2)  # Wait for server to start
        try:
            logger.info(f"Opening browser to {self.url}")
            webbrowser.open(self.url)
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
    
    def run(self):
        """Run the desktop application"""
        print("=" * 60)
        print("  DERSA ECOQUALITY - DESKTOP APPLICATION")
        print("  Quality Management System for Ceramic Manufacturing")
        print("  Ceramica Dersa - Tétouan, Morocco")
        print("=" * 60)
        print()
        print(f"Starting application...")
        print(f"Server URL: {self.url}")
        print()
        print("Instructions:")
        print("- The application will open in your default web browser")
        print("- To stop the application, close this window or press Ctrl+C")
        print("- For support, contact: support@ceramicadersa.com")
        print()
        
        # Start server in background thread
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        # Open browser
        browser_thread = threading.Thread(target=self.open_browser, daemon=True)
        browser_thread.start()
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down Dersa EcoQuality...")
            sys.exit(0)

if __name__ == '__main__':
    # Configure logging for desktop app
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    desktop_app = DesktopApp()
    desktop_app.run()