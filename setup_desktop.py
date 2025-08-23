#!/usr/bin/env python3
"""
Dersa EcoQuality - Desktop Setup Script
Setup script for the desktop application
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements_local.txt"
        ])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False
    except FileNotFoundError:
        print("❌ requirements_local.txt not found")
        return False

def create_startup_scripts():
    """Create platform-specific startup scripts"""
    print("\n📝 Creating startup scripts...")
    
    # Windows batch file
    if platform.system() == "Windows":
        with open("start_dersa.bat", "w") as f:
            f.write("""@echo off
title Dersa EcoQuality
echo Starting Dersa EcoQuality...
python main.py
pause
""")
        print("✅ Created start_dersa.bat for Windows")
    
    # Unix shell script
    else:
        with open("start_dersa.sh", "w") as f:
            f.write("""#!/bin/bash
echo "Starting Dersa EcoQuality..."
python3 main.py
read -p "Press Enter to continue..."
""")
        
        # Make executable
        os.chmod("start_dersa.sh", 0o755)
        print("✅ Created start_dersa.sh for Unix/Linux")

def setup_database():
    """Initialize the local database"""
    print("\n💾 Setting up local database...")
    
    try:
        from local_database import LocalDatabaseManager
        
        db = LocalDatabaseManager()
        db.seed_initial_data()
        
        print("✅ Database initialized successfully")
        print("   📁 Database file: dersa_ecoquality.db")
        print("   👤 Admin user created:")
        print("      Username: admin")
        print("      Password: admin123")
        
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def main():
    """Main setup process"""
    print("=" * 60)
    print("  DERSA ECOQUALITY - DESKTOP SETUP")
    print("  Quality Management System for Ceramic Manufacturing")
    print("=" * 60)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install requirements
    if success and not install_requirements():
        success = False
    
    # Setup database
    if success and not setup_database():
        success = False
    
    # Create startup scripts
    if success:
        create_startup_scripts()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print()
        print("Next steps:")
        print("1. Run the application:")
        if platform.system() == "Windows":
            print("   • Double-click start_dersa.bat")
            print("   • Or run: python main.py")
        else:
            print("   • Run: ./start_dersa.sh")
            print("   • Or run: python3 main.py")
        print()
        print("2. Open your browser to: http://localhost:5000")
        print("3. Login with:")
        print("   Username: admin")
        print("   Password: admin123")
        print()
        print("📊 Features available:")
        print("   • Production batch management")
        print("   • Quality control with ISO compliance")
        print("   • Energy consumption monitoring")
        print("   • Waste and recycling tracking")
        print("   • Environmental KPIs dashboard")
        print("   • Compliance document management")
        
    else:
        print("❌ SETUP FAILED")
        print("Please resolve the issues above and run setup again.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()