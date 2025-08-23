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
                    defect_description TEXT,
                    defect_image_url VARCHAR(500),
                    
                    -- Test results
                    status VARCHAR(50) DEFAULT 'pending',
                    iso_compliant BOOLEAN,
                    pass_fail VARCHAR(10),
                    test_notes TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

            # Create indexes for better performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_production_batches_date ON production_batches(production_date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_quality_tests_batch ON quality_tests(batch_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_energy_consumption_date ON energy_consumption(recorded_date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_waste_records_date ON waste_records(recorded_date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON alerts(is_resolved)")

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