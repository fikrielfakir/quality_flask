"""
Dersa EcoQuality - Database Models
Comprehensive quality management system for ceramic tile manufacturing
"""

import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import logging
from datetime import datetime, date, time
from enum import Enum

logger = logging.getLogger(__name__)

class UserRole(Enum):
    ADMIN = "admin"
    QUALITY_TECHNICIAN = "quality_technician"
    PRODUCTION_MANAGER = "production_manager"
    ENVIRONMENT_MANAGER = "environment_manager"
    MAINTENANCE = "maintenance"

class TestStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"

class DefectType(Enum):
    NONE = "none"
    CRACK = "crack"
    CHIP = "chip"
    GLAZE_DEFECT = "glaze_defect"
    COLOR_DEVIATION = "color_deviation"
    WARPING = "warping"
    DIMENSION_ERROR = "dimension_error"

class EnergySource(Enum):
    ELECTRICITY = "electricity"
    GAS = "gas"
    THERMAL = "thermal"
    SOLAR = "solar"
    RECOVERED_HEAT = "recovered_heat"

class WasteType(Enum):
    CERAMIC_WASTE = "ceramic_waste"
    GLAZE_WASTE = "glaze_waste"
    CARDBOARD = "cardboard"
    PLASTIC = "plastic"
    METAL = "metal"
    LIQUID_WASTE = "liquid_waste"
    ALUMINA = "alumina"

class BatchStatus(Enum):
    PLANNED = "planned"
    IN_PRODUCTION = "in_production"
    QUALITY_TESTING = "quality_testing"
    APPROVED = "approved"
    REJECTED = "rejected"
    SHIPPED = "shipped"

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is required")
        self.init_database()

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = True
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
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create ENUM types
                cur.execute("""
                    DO $$ BEGIN
                        CREATE TYPE user_role AS ENUM ('admin', 'quality_technician', 'production_manager', 'environment_manager', 'maintenance');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """)
                
                cur.execute("""
                    DO $$ BEGIN
                        CREATE TYPE test_status AS ENUM ('pending', 'in_progress', 'passed', 'failed', 'requires_review');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """)
                
                cur.execute("""
                    DO $$ BEGIN
                        CREATE TYPE defect_type AS ENUM ('none', 'crack', 'chip', 'glaze_defect', 'color_deviation', 'warping', 'dimension_error');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """)
                
                cur.execute("""
                    DO $$ BEGIN
                        CREATE TYPE energy_source AS ENUM ('electricity', 'gas', 'thermal', 'solar', 'recovered_heat');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """)
                
                cur.execute("""
                    DO $$ BEGIN
                        CREATE TYPE waste_type AS ENUM ('ceramic_waste', 'glaze_waste', 'cardboard', 'plastic', 'metal', 'liquid_waste', 'alumina');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """)
                
                cur.execute("""
                    DO $$ BEGIN
                        CREATE TYPE batch_status AS ENUM ('planned', 'in_production', 'quality_testing', 'approved', 'rejected', 'shipped');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """)

                # Users and Authentication
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255),
                        role user_role DEFAULT 'quality_technician',
                        department VARCHAR(100),
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                """)

                # Production Batches
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS production_batches (
                        id SERIAL PRIMARY KEY,
                        batch_number VARCHAR(50) UNIQUE NOT NULL,
                        product_type VARCHAR(100) NOT NULL,
                        production_date DATE NOT NULL,
                        planned_quantity INTEGER NOT NULL,
                        actual_quantity INTEGER,
                        kiln_number VARCHAR(20),
                        firing_temperature DECIMAL(5,2),
                        firing_duration INTERVAL,
                        status batch_status DEFAULT 'planned',
                        supervisor_id INTEGER REFERENCES users(id),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Quality Control Tests
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS quality_tests (
                        id SERIAL PRIMARY KEY,
                        batch_id INTEGER REFERENCES production_batches(id) NOT NULL,
                        test_date DATE DEFAULT CURRENT_DATE,
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
                        defect_type defect_type DEFAULT 'none',
                        defect_count INTEGER DEFAULT 0,
                        defect_description TEXT,
                        defect_image_url VARCHAR(500),
                        
                        -- Test results
                        status test_status DEFAULT 'pending',
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
                        id SERIAL PRIMARY KEY,
                        recorded_date DATE DEFAULT CURRENT_DATE,
                        recorded_time TIME DEFAULT CURRENT_TIME,
                        source energy_source NOT NULL,
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
                        id SERIAL PRIMARY KEY,
                        recorded_date DATE DEFAULT CURRENT_DATE,
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
                        id SERIAL PRIMARY KEY,
                        recorded_date DATE DEFAULT CURRENT_DATE,
                        waste_type waste_type NOT NULL,
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
                        id SERIAL PRIMARY KEY,
                        document_name VARCHAR(255) NOT NULL,
                        document_type VARCHAR(100) NOT NULL,
                        standard_reference VARCHAR(100), -- ISO 9001, ISO 14001, etc.
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
                        id SERIAL PRIMARY KEY,
                        campaign_name VARCHAR(255) NOT NULL,
                        campaign_type VARCHAR(100), -- Quality, Environmental, Energy, etc.
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
                        id SERIAL PRIMARY KEY,
                        recorded_date DATE DEFAULT CURRENT_DATE,
                        kpi_name VARCHAR(100) NOT NULL,
                        kpi_value DECIMAL(12,4) NOT NULL,
                        target_value DECIMAL(12,4),
                        unit VARCHAR(20),
                        category VARCHAR(50), -- Energy, Waste, Water, Emissions
                        calculation_method TEXT,
                        data_source VARCHAR(100),
                        recorded_by INTEGER REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Alerts and Notifications
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id SERIAL PRIMARY KEY,
                        alert_type VARCHAR(50) NOT NULL,
                        priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
                        title VARCHAR(255) NOT NULL,
                        message TEXT NOT NULL,
                        related_table VARCHAR(50),
                        related_id INTEGER,
                        assigned_to INTEGER REFERENCES users(id),
                        is_resolved BOOLEAN DEFAULT false,
                        resolved_at TIMESTAMP,
                        resolved_by INTEGER REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # ISO Standards Reference
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS iso_standards (
                        id SERIAL PRIMARY KEY,
                        standard_code VARCHAR(20) NOT NULL, -- ISO 13006, ISO 10545-3, etc.
                        standard_name VARCHAR(255) NOT NULL,
                        parameter_name VARCHAR(100) NOT NULL,
                        min_value DECIMAL(12,4),
                        max_value DECIMAL(12,4),
                        unit VARCHAR(20),
                        test_method TEXT,
                        applicable_product_types TEXT[],
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes for better performance
                cur.execute("CREATE INDEX IF NOT EXISTS idx_production_batches_date ON production_batches(production_date)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_quality_tests_batch ON quality_tests(batch_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_energy_consumption_date ON energy_consumption(recorded_date)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_waste_records_date ON waste_records(recorded_date)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON alerts(is_resolved) WHERE is_resolved = false")

                logger.info("Database tables created successfully")

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                if cur.description:
                    return [{key: value for key, value in row.items()} for row in cur.fetchall()]
                return []

    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute a query and return single result"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None

    def insert_record(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a record and return the created record"""
        columns = list(data.keys())
        placeholders = [f"%({col})s" for col in columns]
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        return self.execute_single(query, data)