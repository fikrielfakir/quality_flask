"""
Dersa EcoQuality - Executable Builder
Script to build desktop executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not available"""
    try:
        import PyInstaller
        print("PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def create_spec_file():
    """Create PyInstaller spec file for the application"""
    
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['desktop_config.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        'app_dersa',
        'models',
        'services',
        'seed_data',
        'flask',
        'flask_cors',
        'psycopg2',
        'bcrypt',
        'python-dotenv'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DersaEcoQuality',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='dersa_icon.ico' if os.path.exists('dersa_icon.ico') else None,
)
'''
    
    with open('dersa_ecoquality.spec', 'w') as f:
        f.write(spec_content.strip())
    
    print("Created PyInstaller spec file: dersa_ecoquality.spec")

def build_executable():
    """Build the executable using PyInstaller"""
    
    print("Building executable...")
    
    # Create dist and build directories if they don't exist
    os.makedirs('dist', exist_ok=True)
    os.makedirs('build', exist_ok=True)
    
    # Run PyInstaller
    try:
        result = subprocess.run([
            'pyinstaller',
            '--clean',
            '--noconfirm',
            'dersa_ecoquality.spec'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Executable built successfully!")
            print(f"✓ Location: {os.path.abspath('dist/DersaEcoQuality')}")
            
            # Create portable package
            create_portable_package()
            
        else:
            print("✗ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
    except FileNotFoundError:
        print("✗ PyInstaller not found. Please install it first:")
        print("pip install pyinstaller")

def create_portable_package():
    """Create a portable package with all necessary files"""
    
    package_dir = Path('dist/DersaEcoQuality_Portable')
    package_dir.mkdir(exist_ok=True)
    
    # Copy executable
    if os.path.exists('dist/DersaEcoQuality'):
        if os.path.isfile('dist/DersaEcoQuality'):
            shutil.copy2('dist/DersaEcoQuality', package_dir)
        else:
            shutil.copytree('dist/DersaEcoQuality', package_dir / 'DersaEcoQuality', dirs_exist_ok=True)
    
    # Create README
    readme_content = """
DERSA ECOQUALITY - DESKTOP APPLICATION
=====================================

Quality Management System for Ceramic Tile Manufacturing
Ceramica Dersa - Tétouan, Morocco

INSTALLATION & USAGE:
--------------------

1. REQUIREMENTS:
   - Windows 10/11, macOS 10.15+, or Linux Ubuntu 18.04+
   - No additional software required (PostgreSQL embedded)
   - Minimum 4GB RAM, 1GB free disk space

2. FIRST RUN:
   - Run the DersaEcoQuality executable
   - The application will automatically open in your web browser
   - Default login: admin / admin123

3. FEATURES:
   - Production batch management
   - Quality control with ISO compliance (ISO 13006, ISO 10545-3, ISO 10545-4)
   - Energy consumption monitoring
   - Waste and recycling tracking
   - Heat recovery system monitoring
   - Environmental KPIs dashboard
   - Compliance document management
   - Testing campaign management
   - Multi-language support (French/Arabic)

4. SYSTEM MODULES:
   - Dashboard: Real-time KPIs and trend analysis
   - Production: Batch tracking and status management
   - Quality Control: ISO-compliant testing with automated validation
   - Energy Management: Consumption tracking and efficiency monitoring
   - Environmental: Waste management and heat recovery tracking
   - Compliance: Document management and audit trails
   - Reporting: PDF/Excel export capabilities

5. TECHNICAL SPECIFICATIONS:
   - Backend: Flask (Python)
   - Database: PostgreSQL (embedded)
   - Frontend: RESTful API (browser-based interface)
   - Standards: ISO 9001, ISO 14001, ISO 13006, IMANOR Morocco

6. SUPPORT:
   - Email: support@ceramicadersa.com
   - Phone: +212 539 XXX XXX
   - Documentation: Available in application help section

7. DATA BACKUP:
   - Database files stored in: ./data/
   - Regular backups recommended
   - Export functions available in application

TROUBLESHOOTING:
---------------
- If browser doesn't open automatically, navigate to: http://localhost:5000
- For database issues, check data/ directory permissions
- For network issues, ensure port 5000 is not blocked
- Check logs in: ./logs/dersa_ecoquality.log

VERSION: 1.0.0
BUILD DATE: """ + str(Path(__file__).stat().st_mtime) + """
LICENSE: Proprietary - Ceramica Dersa
"""
    
    with open(package_dir / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Create startup script for different platforms
    if sys.platform.startswith('win'):
        startup_script = """@echo off
echo Starting Dersa EcoQuality...
DersaEcoQuality.exe
pause"""
        with open(package_dir / 'Start_DersaEcoQuality.bat', 'w') as f:
            f.write(startup_script)
    
    else:
        startup_script = """#!/bin/bash
echo "Starting Dersa EcoQuality..."
./DersaEcoQuality
read -p "Press Enter to continue...""""
        startup_file = package_dir / 'Start_DersaEcoQuality.sh'
        with open(startup_file, 'w') as f:
            f.write(startup_script)
        startup_file.chmod(0o755)
    
    print(f"✓ Portable package created: {package_dir}")
    print("✓ Package includes executable, documentation, and startup scripts")

def main():
    """Main build process"""
    print("=" * 60)
    print("  DERSA ECOQUALITY - EXECUTABLE BUILDER")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher required")
        sys.exit(1)
    
    print(f"✓ Python version: {sys.version}")
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    build_executable()
    
    print("\nBuild process completed!")
    print("Run the executable from: dist/DersaEcoQuality_Portable/")

if __name__ == '__main__':
    main()