"""
Dersa EcoQuality - Local SQLite Database
Local database configuration for desktop deployment
"""

import sqlite3
import os
import bcrypt
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

class LocalDatabaseManager:
    def __init__(self, db_path: str = "dersa_ecoquality.db"):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def init_database(self):
        """Initialize SQLite database with all required tables"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            # Users and Authentication
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    role VARCHAR(50) DEFAULT 'quality_technician',
                    department VARCHAR(100),
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)

            # Production Batches
            cur.execute("""
                CREATE TABLE IF NOT EXISTS production_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_number VARCHAR(50) UNIQUE NOT NULL,
                    product_type VARCHAR(100) NOT NULL,
                    production_date DATE NOT NULL,
                    planned_quantity INTEGER NOT NULL,
                    actual_quantity INTEGER,
                    kiln_number VARCHAR(20),
                    firing_temperature DECIMAL(5,2),
                    firing_duration VARCHAR(50),
                    status VARCHAR(50) DEFAULT 'planned',
                    supervisor_id INTEGER REFERENCES users(id),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Quality Control Tests
            cur.execute("""
                CREATE TABLE IF NOT EXISTS quality_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id INTEGER REFERENCES production_batches(id) NOT NULL,
                    test_date DATE DEFAULT (date('now')),
                    technician_id INTEGER REFERENCES users(id),
                    test_type VARCHAR(50) NOT NULL,
                    
                    -- Dimensional measurements (ISO 13006)
                    length_mm DECIMAL(8,2),
                    width_mm DECIMAL(8,2),
                    thickness_mm DECIMAL(6,2),
                    warping_percentage DECIMAL(4,2),
                    
                    -- Physical properties
                    water_absorption_percentage DECIMAL(5,2),
                    breaking_strength_n INTEGER,
                    abrasion_resistance_pei INTEGER,
                    
                    -- Visual inspection
                    defect_type VARCHAR(50) DEFAULT 'none',
                    defect_count INTEGER DEFAULT 0,
                    defect_severity VARCHAR(20) DEFAULT 'minor',
                    defect_description TEXT,
                    defect_image_url VARCHAR(500),
                    
                    -- Equipment tracking
                    equipment_used VARCHAR(100),
                    equipment_calibration_date DATE,
                    
                    -- Test results
                    status VARCHAR(50) DEFAULT 'pending',
                    iso_compliant BOOLEAN,
                    pass_fail VARCHAR(10),
                    test_notes TEXT,
                    
                    -- Advanced features
                    auto_pass_fail BOOLEAN DEFAULT 0,
                    compliance_score DECIMAL(5,2),
                    corrective_actions TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Equipment and Calibration
            cur.execute("""
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_code VARCHAR(50) UNIQUE NOT NULL,
                    equipment_name VARCHAR(100) NOT NULL,
                    equipment_type VARCHAR(50) NOT NULL,
                    manufacturer VARCHAR(100),
                    model VARCHAR(100),
                    last_calibration_date DATE,
                    calibration_due_date DATE,
                    calibration_interval_days INTEGER DEFAULT 365,
                    calibration_status VARCHAR(20) DEFAULT 'valid',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Energy Consumption
            cur.execute("""
                CREATE TABLE IF NOT EXISTS energy_consumption (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_date DATE DEFAULT (date('now')),
                    recorded_time TIME DEFAULT (time('now')),
                    source VARCHAR(50) NOT NULL,
                    equipment_name VARCHAR(100),
                    department VARCHAR(100),
                    consumption_kwh DECIMAL(10,3) NOT NULL,
                    cost_amount DECIMAL(10,2),
                    meter_reading DECIMAL(12,3),
                    efficiency_percentage DECIMAL(5,2),
                    target_consumption DECIMAL(10,3),
                    notes TEXT,
                    recorded_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Heat Recovery System
            cur.execute("""
                CREATE TABLE IF NOT EXISTS heat_recovery (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_date DATE DEFAULT (date('now')),
                    kiln_id VARCHAR(20),
                    input_temperature DECIMAL(6,2),
                    output_temperature DECIMAL(6,2),
                    heat_recovered_kwh DECIMAL(10,3),
                    thermal_efficiency_percentage DECIMAL(5,2),
                    energy_savings_kwh DECIMAL(10,3),
                    cost_savings DECIMAL(10,2),
                    equipment_status VARCHAR(50),
                    maintenance_notes TEXT,
                    recorded_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Waste Management
            cur.execute("""
                CREATE TABLE IF NOT EXISTS waste_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_date DATE DEFAULT (date('now')),
                    waste_type VARCHAR(50) NOT NULL,
                    quantity_kg DECIMAL(10,2) NOT NULL,
                    source_department VARCHAR(100),
                    disposal_method VARCHAR(100),
                    recycling_percentage DECIMAL(5,2),
                    valorization_amount DECIMAL(10,2),
                    cost_amount DECIMAL(10,2),
                    destination VARCHAR(200),
                    certificate_number VARCHAR(100),
                    responsible_person_id INTEGER REFERENCES users(id),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Compliance Documents
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compliance_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_name VARCHAR(255) NOT NULL,
                    document_type VARCHAR(100) NOT NULL,
                    standard_reference VARCHAR(100),
                    issue_date DATE,
                    expiry_date DATE,
                    issuing_authority VARCHAR(255),
                    certificate_number VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'active',
                    file_path VARCHAR(500),
                    compliance_score DECIMAL(5,2),
                    audit_notes TEXT,
                    uploaded_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Testing Campaigns
            cur.execute("""
                CREATE TABLE IF NOT EXISTS testing_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_name VARCHAR(255) NOT NULL,
                    campaign_type VARCHAR(100),
                    start_date DATE NOT NULL,
                    end_date DATE,
                    target_batches INTEGER,
                    completed_tests INTEGER DEFAULT 0,
                    pass_rate DECIMAL(5,2),
                    description TEXT,
                    objectives TEXT,
                    status VARCHAR(50) DEFAULT 'planning',
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Environmental KPIs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS environmental_kpis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_date DATE DEFAULT (date('now')),
                    kpi_name VARCHAR(100) NOT NULL,
                    kpi_value DECIMAL(12,4) NOT NULL,
                    target_value DECIMAL(12,4),
                    unit VARCHAR(20),
                    category VARCHAR(50),
                    calculation_method TEXT,
                    data_source VARCHAR(100),
                    recorded_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Alerts and Notifications
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type VARCHAR(50) NOT NULL,
                    priority VARCHAR(20) DEFAULT 'medium',
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    related_table VARCHAR(50),
                    related_id INTEGER,
                    assigned_to INTEGER REFERENCES users(id),
                    is_resolved BOOLEAN DEFAULT 0,
                    resolved_at TIMESTAMP,
                    resolved_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ISO Standards Reference
            cur.execute("""
                CREATE TABLE IF NOT EXISTS iso_standards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    standard_code VARCHAR(20) NOT NULL,
                    standard_name VARCHAR(255) NOT NULL,
                    parameter_name VARCHAR(100) NOT NULL,
                    min_value DECIMAL(12,4),
                    max_value DECIMAL(12,4),
                    unit VARCHAR(20),
                    test_method TEXT,
                    applicable_product_types TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Raw Material Management Tables
            cur.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_code VARCHAR(20) UNIQUE NOT NULL,
                    supplier_name VARCHAR(255) NOT NULL,
                    contact_person VARCHAR(255),
                    phone VARCHAR(50),
                    email VARCHAR(255),
                    address TEXT,
                    region VARCHAR(100),
                    certification_status VARCHAR(50) DEFAULT 'pending',
                    quality_rating DECIMAL(3,2) DEFAULT 5.0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS raw_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material_code VARCHAR(50) UNIQUE NOT NULL,
                    material_name VARCHAR(255) NOT NULL,
                    material_type VARCHAR(50) NOT NULL,
                    supplier_id INTEGER REFERENCES suppliers(id),
                    reception_date DATE DEFAULT (date('now')),
                    lot_number VARCHAR(100),
                    quantity_kg DECIMAL(10,2) NOT NULL,
                    unit_cost DECIMAL(10,2),
                    status VARCHAR(20) DEFAULT 'en_attente',
                    humidity_percentage DECIMAL(5,2),
                    particle_size_microns DECIMAL(8,2),
                    chemical_composition TEXT,
                    inspection_notes TEXT,
                    storage_location VARCHAR(100),
                    expiry_date DATE,
                    inspected_by INTEGER REFERENCES users(id),
                    approved_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Silo Inventory Management
            cur.execute("""
                CREATE TABLE IF NOT EXISTS silos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    silo_code VARCHAR(20) UNIQUE NOT NULL,
                    silo_name VARCHAR(100) NOT NULL,
                    capacity_kg DECIMAL(10,2) NOT NULL,
                    current_level_kg DECIMAL(10,2) DEFAULT 0,
                    material_type VARCHAR(50),
                    humidity_sensor_id VARCHAR(50),
                    target_humidity_min DECIMAL(5,2),
                    target_humidity_max DECIMAL(5,2),
                    current_humidity DECIMAL(5,2),
                    last_humidity_check TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'active',
                    location VARCHAR(100),
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Glaze and Engobe Tank Management
            cur.execute("""
                CREATE TABLE IF NOT EXISTS glaze_tanks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tank_code VARCHAR(20) UNIQUE NOT NULL,
                    tank_name VARCHAR(100) NOT NULL,
                    tank_type VARCHAR(50) NOT NULL,
                    capacity_liters DECIMAL(8,2) NOT NULL,
                    current_level_liters DECIMAL(8,2) DEFAULT 0,
                    material_batch_code VARCHAR(100),
                    viscosity_cps DECIMAL(8,2),
                    density_gcm3 DECIMAL(6,3),
                    refusal_rate_percentage DECIMAL(5,2),
                    temperature_celsius DECIMAL(5,2),
                    ph_level DECIMAL(4,2),
                    preparation_date DATE,
                    expiry_date DATE,
                    status VARCHAR(20) DEFAULT 'active',
                    quality_approved BOOLEAN DEFAULT 0,
                    approved_by INTEGER REFERENCES users(id),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Enhanced Testing for Complete ISO 13006:2018 Compliance
            cur.execute("""
                CREATE TABLE IF NOT EXISTS advanced_quality_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id INTEGER REFERENCES production_batches(id) NOT NULL,
                    test_date DATE DEFAULT (date('now')),
                    technician_id INTEGER REFERENCES users(id),
                    test_standard VARCHAR(50) NOT NULL,
                    
                    -- Chemical Properties (ISO 10545 series)
                    stain_resistance_class INTEGER,
                    acid_resistance_class VARCHAR(10),
                    alkali_resistance_class VARCHAR(10),
                    lead_release_mgdm2 DECIMAL(8,4),
                    cadmium_release_mgdm2 DECIMAL(8,4),
                    
                    -- Thermal Properties
                    thermal_expansion_coefficient DECIMAL(8,4),
                    thermal_shock_resistance_passed BOOLEAN,
                    crazing_resistance_passed BOOLEAN,
                    frost_resistance_passed BOOLEAN,
                    
                    -- Moisture and Size Stability
                    moisture_expansion_percentage DECIMAL(6,4),
                    
                    -- Surface Properties
                    deep_abrasion_resistance_mm3 DECIMAL(8,2),
                    slip_resistance_wet DECIMAL(4,2),
                    slip_resistance_dry DECIMAL(4,2),
                    
                    -- Test Conditions
                    test_temperature_celsius DECIMAL(5,2),
                    test_humidity_percentage DECIMAL(5,2),
                    testing_equipment VARCHAR(255),
                    
                    -- Results
                    overall_grade VARCHAR(10),
                    application_classification VARCHAR(100),
                    compliance_certificate_number VARCHAR(100),
                    test_notes TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Production Line Monitoring
            cur.execute("""
                CREATE TABLE IF NOT EXISTS production_line_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    line_name VARCHAR(100) NOT NULL,
                    station_name VARCHAR(100) NOT NULL,
                    equipment_id VARCHAR(50),
                    current_batch_id INTEGER REFERENCES production_batches(id),
                    status VARCHAR(50) NOT NULL,
                    operator_id INTEGER REFERENCES users(id),
                    work_instruction_displayed TEXT,
                    parameter_values TEXT,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    alert_status VARCHAR(20) DEFAULT 'normal',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_production_batches_date ON production_batches(production_date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_quality_tests_batch ON quality_tests(batch_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_energy_consumption_date ON energy_consumption(recorded_date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_waste_records_date ON waste_records(recorded_date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON alerts(is_resolved)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_raw_materials_supplier ON raw_materials(supplier_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_raw_materials_status ON raw_materials(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_silos_material_type ON silos(material_type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_glaze_tanks_status ON glaze_tanks(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_advanced_tests_batch ON advanced_quality_tests(batch_id)")

            conn.commit()
            logger.info("SQLite database tables created successfully")

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            rows = cur.fetchall()
            return [{column: row[column] for column in row.keys()} for row in rows]

    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute a query and return single result"""
        with self.get_connection() as conn:
            cur = conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            row = cur.fetchone()
            return {column: row[column] for column in row.keys()} if row else None

    def insert_record(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a record and return the created record"""
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        values = [data[col] for col in columns]
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, values)
            conn.commit()
            
            # Get the inserted record
            row_id = cur.lastrowid
            return self.execute_single(f"SELECT * FROM {table} WHERE id = ?", (row_id,))

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def seed_initial_data(self):
        """Seed the database with initial data"""
        # Check if admin user exists
        admin_exists = self.execute_single("SELECT id FROM users WHERE username = 'admin'")
        
        if not admin_exists:
            # Create admin user
            admin_data = {
                'username': 'admin',
                'email': 'admin@ceramicadersa.com',
                'password_hash': self.hash_password('admin123'),
                'full_name': 'Administrator',
                'role': 'admin',
                'department': 'Management',
                'is_active': 1
            }
            self.insert_record('users', admin_data)
            logger.info("Created admin user (username: admin, password: admin123)")

        # Check if ISO standards exist
        standards_exist = self.execute_query("SELECT COUNT(*) as count FROM iso_standards")
        if not standards_exist or standards_exist[0]['count'] == 0:
            self.seed_iso_standards()
        
        # Seed new module data - will be implemented
        pass

    def seed_iso_standards(self):
        """Seed ISO standards for ceramic tiles"""
        iso_standards = [
            {
                'standard_code': 'ISO 13006',
                'standard_name': 'Ceramic tiles - Definitions, classification, characteristics and marking',
                'parameter_name': 'length_tolerance',
                'min_value': None,
                'max_value': 0.5,
                'unit': '%',
                'test_method': 'Measure length with calibrated instruments',
                'applicable_product_types': 'floor_tiles,wall_tiles,rectified_tiles'
            },
            {
                'standard_code': 'ISO 13006',
                'standard_name': 'Ceramic tiles - Definitions, classification, characteristics and marking',
                'parameter_name': 'warping_percentage',
                'min_value': None,
                'max_value': 0.6,
                'unit': '%',
                'test_method': 'Measure warping using straightedge and feeler gauge',
                'applicable_product_types': 'rectified_tiles,floor_tiles'
            },
            {
                'standard_code': 'ISO 10545-3',
                'standard_name': 'Ceramic tiles - Determination of water absorption',
                'parameter_name': 'water_absorption_percentage',
                'min_value': None,
                'max_value': 3.0,
                'unit': '%',
                'test_method': 'Boiling water method or vacuum method',
                'applicable_product_types': 'gres_cerame,porcelain_tiles'
            },
            {
                'standard_code': 'ISO 10545-4',
                'standard_name': 'Ceramic tiles - Determination of modulus of rupture and breaking strength',
                'parameter_name': 'breaking_strength_n',
                'min_value': 1300,
                'max_value': None,
                'unit': 'N',
                'test_method': 'Three-point bending test with universal testing machine',
                'applicable_product_types': 'floor_tiles,gres_cerame'
            },
            {
                'standard_code': 'ISO 10545-7',
                'standard_name': 'Ceramic tiles - Determination of resistance to surface abrasion',
                'parameter_name': 'abrasion_resistance_pei',
                'min_value': 1,
                'max_value': 5,
                'unit': 'PEI',
                'test_method': 'Rotating abrasive wheel test with standard abrasive charge',
                'applicable_product_types': 'floor_tiles,commercial_tiles'
            }
        ]

        for standard in iso_standards:
            self.insert_record('iso_standards', standard)
        
        logger.info(f"Seeded {len(iso_standards)} ISO standards")
        
        # Seed equipment data
        self.seed_equipment_data()

        # Seed environmental KPIs
        kpi_targets = [
            {
                'kpi_name': 'energy_reduction_target',
                'kpi_value': 12.0,
                'target_value': 12.0,
                'unit': '%',
                'category': 'Energy',
                'calculation_method': 'Annual energy consumption reduction percentage',
                'data_source': 'Energy monitoring system'
            },
            {
                'kpi_name': 'liquid_waste_recycling',
                'kpi_value': 100.0,
                'target_value': 100.0,
                'unit': '%',
                'category': 'Waste',
                'calculation_method': 'Percentage of liquid waste recycled',
                'data_source': 'Waste management system'
            },
            {
                'kpi_name': 'heat_recovery_annual',
                'kpi_value': 511.0,
                'target_value': 511.0,
                'unit': 'MWh',
                'category': 'Energy',
                'calculation_method': 'Annual heat recovery from kilns',
                'data_source': 'Heat recovery monitoring'
            }
        ]

        for kpi in kpi_targets:
            self.insert_record('environmental_kpis', kpi)
        
        logger.info(f"Seeded {len(kpi_targets)} environmental KPIs")
        
    def seed_equipment_data(self):
        """Seed equipment data for calibration tracking"""
        equipment_list = [
            {
                'equipment_code': 'digital_caliper_001',
                'equipment_name': 'Pied à Coulisse Digital #001',
                'equipment_type': 'dimensional_measurement',
                'manufacturer': 'Mitutoyo',
                'model': 'CD-15DCX',
                'last_calibration_date': '2024-12-15',
                'calibration_due_date': '2025-12-15',
                'calibration_interval_days': 365,
                'calibration_status': 'valid'
            },
            {
                'equipment_code': 'universal_tester_002',
                'equipment_name': 'Machine d\'Essai Universelle #002',
                'equipment_type': 'mechanical_testing',
                'manufacturer': 'Zwick Roell',
                'model': 'Z050',
                'last_calibration_date': '2024-11-20',
                'calibration_due_date': '2025-11-20',
                'calibration_interval_days': 365,
                'calibration_status': 'expires_soon'
            },
            {
                'equipment_code': 'absorption_tester_003',
                'equipment_name': 'Testeur d\'Absorption #003',
                'equipment_type': 'water_absorption',
                'manufacturer': 'Controls Group',
                'model': 'WA-3000',
                'last_calibration_date': '2024-10-10',
                'calibration_due_date': '2025-10-10',
                'calibration_interval_days': 365,
                'calibration_status': 'expired'
            },
            {
                'equipment_code': 'pei_tester_004',
                'equipment_name': 'Testeur PEI #004',
                'equipment_type': 'abrasion_testing',
                'manufacturer': 'Erichsen',
                'model': 'PEI-450',
                'last_calibration_date': '2024-12-01',
                'calibration_due_date': '2025-12-01',
                'calibration_interval_days': 365,
                'calibration_status': 'valid'
            }
        ]
        
        # Check if equipment already exists
        existing_equipment = self.execute_query("SELECT COUNT(*) as count FROM equipment")
        if not existing_equipment or existing_equipment[0]['count'] == 0:
            for equipment in equipment_list:
                self.insert_record('equipment', equipment)
            logger.info(f"Seeded {len(equipment_list)} equipment records")
    
    def update_equipment_calibration_status(self):
        """Update equipment calibration status based on due dates"""
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        warning_threshold = timedelta(days=30)  # Warn 30 days before expiry
        
        # Get all equipment
        equipment = self.execute_query("SELECT * FROM equipment WHERE is_active = 1")
        
        for item in equipment:
            if item['calibration_due_date']:
                due_date = datetime.strptime(item['calibration_due_date'], '%Y-%m-%d').date()
                
                if due_date < today:
                    new_status = 'expired'
                elif due_date <= today + warning_threshold:
                    new_status = 'expires_soon'
                else:
                    new_status = 'valid'
                
                if new_status != item['calibration_status']:
                    self.execute_single(
                        "UPDATE equipment SET calibration_status = ? WHERE id = ?",
                        (new_status, item['id'])
                    )
        
        logger.info("Equipment calibration status updated")
    
    def get_equipment_by_code(self, equipment_code: str):
        """Get equipment information by code"""
        return self.execute_single(
            "SELECT * FROM equipment WHERE equipment_code = ? AND is_active = 1",
            (equipment_code,)
        )