# DERSA ECOQUALITY - DESKTOP APPLICATION

Quality Management System for Ceramic Tile Manufacturing  
**Ceramica Dersa - Tétouan, Morocco**

## 🏭 Overview

Dersa EcoQuality is a comprehensive quality management system specifically designed for ceramic tile manufacturing. It provides end-to-end quality control, energy monitoring, waste management, and ISO compliance tracking for ceramic production facilities.

## ✨ Key Features

### 📊 **Dashboard & Analytics**
- Real-time KPIs and performance indicators
- Production efficiency metrics
- Energy consumption trends
- Environmental compliance tracking

### 🏭 **Production Management**
- Batch tracking and status management
- Kiln operation monitoring
- Production planning and scheduling
- Supervisor assignment and oversight

### 🔬 **Quality Control (ISO Compliant)**
- **ISO 13006**: Ceramic tiles classification and marking
- **ISO 10545-3**: Water absorption testing
- **ISO 10545-4**: Breaking strength determination
- **ISO 10545-7**: Surface abrasion resistance
- Automated compliance validation
- Defect tracking and analysis

### ⚡ **Energy & Resources Monitoring**
- Multi-source energy tracking (electricity, gas, solar)
- Consumption efficiency analysis
- Cost monitoring and optimization
- Target vs. actual performance

### 🌱 **Environmental Management**
- Waste categorization and tracking
- Recycling rate monitoring
- Heat recovery system tracking
- Environmental KPI dashboard

### 📋 **Compliance & Documentation**
- ISO certification management
- Audit trail documentation
- Regulatory compliance tracking
- Document version control

## 🚀 Installation & Setup

### Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux Ubuntu 18.04+
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 4GB RAM
- **Storage**: 1GB free disk space

### Quick Start

1. **Download and Extract**: Extract all files to your desired directory

2. **Run Setup**: 
   ```bash
   python setup_desktop.py
   ```

3. **Start Application**:
   - **Windows**: Double-click `start_dersa.bat`
   - **Linux/Mac**: Run `./start_dersa.sh`
   - **Manual**: `python main.py`

4. **Access Application**: Open browser to http://localhost:5000

5. **Login**:
   - Username: `admin`
   - Password: `admin123`

## 📁 File Structure

```
dersa_ecoquality/
├── main.py                 # Main application launcher
├── app_local.py            # Flask application (local version)
├── local_database.py       # SQLite database manager
├── desktop_config.py       # Desktop application configuration
├── build_executable.py     # Executable builder script
├── setup_desktop.py        # Setup and installation script
├── requirements_local.txt  # Python dependencies
├── dersa_ecoquality.db    # SQLite database (created after setup)
└── start_dersa.*          # Platform-specific startup scripts
```

## 🎯 System Modules

### 1. **Authentication System**
- Role-based access control
- User management
- Department assignment
- Activity logging

### 2. **Production Tracking**
- Batch number management
- Product type classification
- Kiln operation tracking
- Production status workflow

### 3. **Quality Assurance**
- Dimensional testing (length, width, thickness)
- Physical property testing (water absorption, breaking strength)
- Visual defect inspection
- ISO compliance validation

### 4. **Energy Management**
- Real-time consumption monitoring
- Efficiency calculation
- Cost analysis
- Target setting and tracking

### 5. **Environmental Monitoring**
- Waste stream tracking
- Recycling metrics
- Heat recovery monitoring
- Sustainability KPIs

## 🛠️ Building Executable

To create a standalone executable:

```bash
python build_executable.py
```

This creates a portable application in `dist/DersaEcoQuality_Portable/`

## 📊 Default Data

The system comes pre-configured with:
- **ISO Standards**: 5 key ceramic testing standards
- **Environmental KPIs**: Energy and waste reduction targets
- **Admin User**: Default administrator account
- **Reference Data**: Standard test parameters and compliance thresholds

## 🔧 Configuration

### Database Location
- **File**: `dersa_ecoquality.db` (SQLite)
- **Location**: Application directory
- **Backup**: Copy the .db file to backup data

### Network Settings
- **Host**: localhost (127.0.0.1)
- **Port**: 5000
- **Protocol**: HTTP

### User Roles
- **Admin**: Full system access
- **Quality Technician**: Quality control and testing
- **Production Manager**: Production and energy monitoring
- **Operator**: Basic data entry and viewing

## 📈 Key Performance Indicators

### Production KPIs
- Total batches processed
- Approved vs. rejected batches
- Production efficiency
- Supervisor performance

### Quality KPIs
- ISO compliance rate
- Test pass/fail ratios
- Defect categories and trends
- Corrective action effectiveness

### Environmental KPIs
- Energy reduction percentage
- Waste recycling rate
- Heat recovery efficiency
- Cost savings achieved

## 🔐 Security Features

- Encrypted password storage (bcrypt)
- Role-based access control
- Audit trail logging
- Session management
- Data validation and sanitization

## 📞 Support & Contact

**Ceramica Dersa Technical Support**
- **Email**: support@ceramicadersa.com
- **Phone**: +212 539 XXX XXX
- **Address**: Tétouan, Morocco

**System Information**
- **Version**: 1.0.0
- **Technology**: Python Flask + SQLite
- **Standards Compliance**: ISO 9001, ISO 14001, ISO 13006
- **Certification**: IMANOR Morocco

## 📝 Troubleshooting

### Common Issues

**Application won't start**
- Check Python version (3.8+ required)
- Verify all packages installed: `pip install -r requirements_local.txt`
- Check port 5000 availability

**Database errors**
- Ensure write permissions in application directory
- Check disk space availability
- Backup and recreate database if corrupted

**Browser access issues**
- Try http://127.0.0.1:5000 or http://localhost:5000
- Disable firewall/antivirus temporarily
- Check browser security settings

**Performance issues**
- Close unnecessary applications
- Ensure minimum 4GB RAM available
- Check disk space for database growth

### Log Files
- **Application logs**: `dersa_ecoquality.log`
- **Database logs**: Console output during startup
- **Error logs**: Displayed in application console

## 📄 License

Proprietary software - Ceramica Dersa  
All rights reserved. Unauthorized distribution prohibited.

---

**Dersa EcoQuality** - Empowering ceramic manufacturing through intelligent quality management.