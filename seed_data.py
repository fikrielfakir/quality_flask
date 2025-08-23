"""
Dersa EcoQuality - Seed Data
Initialize database with ISO standards and sample data
"""

from models import DatabaseManager
import logging

logger = logging.getLogger(__name__)

def seed_iso_standards(db: DatabaseManager):
    """Seed the database with ISO standards for ceramic tiles"""
    
    iso_standards = [
        # ISO 13006 - Ceramic tiles classification and standards
        {
            'standard_code': 'ISO 13006',
            'standard_name': 'Ceramic tiles - Definitions, classification, characteristics and marking',
            'parameter_name': 'length_tolerance',
            'min_value': None,
            'max_value': 0.5,  # ±0.5% tolerance
            'unit': '%',
            'test_method': 'Measure length with calibrated instruments',
            'applicable_product_types': ['floor_tiles', 'wall_tiles', 'rectified_tiles']
        },
        {
            'standard_code': 'ISO 13006',
            'standard_name': 'Ceramic tiles - Definitions, classification, characteristics and marking',
            'parameter_name': 'width_tolerance',
            'min_value': None,
            'max_value': 0.5,  # ±0.5% tolerance
            'unit': '%',
            'test_method': 'Measure width with calibrated instruments',
            'applicable_product_types': ['floor_tiles', 'wall_tiles', 'rectified_tiles']
        },
        {
            'standard_code': 'ISO 13006',
            'standard_name': 'Ceramic tiles - Definitions, classification, characteristics and marking',
            'parameter_name': 'thickness_tolerance',
            'min_value': None,
            'max_value': 0.5,  # ±0.5% tolerance
            'unit': '%',
            'test_method': 'Measure thickness with calibrated instruments',
            'applicable_product_types': ['floor_tiles', 'wall_tiles', 'rectified_tiles']
        },
        {
            'standard_code': 'ISO 13006',
            'standard_name': 'Ceramic tiles - Definitions, classification, characteristics and marking',
            'parameter_name': 'warping_percentage',
            'min_value': None,
            'max_value': 0.6,  # ≤0.6% for rectified tiles
            'unit': '%',
            'test_method': 'Measure warping using straightedge and feeler gauge',
            'applicable_product_types': ['rectified_tiles', 'floor_tiles']
        },
        
        # ISO 10545-3 - Water absorption test
        {
            'standard_code': 'ISO 10545-3',
            'standard_name': 'Ceramic tiles - Determination of water absorption',
            'parameter_name': 'water_absorption_percentage',
            'min_value': None,
            'max_value': 3.0,  # ≤3% for gres cérame (porcelain stoneware)
            'unit': '%',
            'test_method': 'Boiling water method or vacuum method',
            'applicable_product_types': ['gres_cerame', 'porcelain_tiles']
        },
        {
            'standard_code': 'ISO 10545-3',
            'standard_name': 'Ceramic tiles - Determination of water absorption',
            'parameter_name': 'water_absorption_percentage',
            'min_value': None,
            'max_value': 10.0,  # ≤10% for earthenware tiles
            'unit': '%',
            'test_method': 'Boiling water method or vacuum method',
            'applicable_product_types': ['earthenware_tiles', 'wall_tiles']
        },
        
        # ISO 10545-4 - Breaking strength test
        {
            'standard_code': 'ISO 10545-4',
            'standard_name': 'Ceramic tiles - Determination of modulus of rupture and breaking strength',
            'parameter_name': 'breaking_strength_n',
            'min_value': 1300,  # min. 1,300 N for floor tiles
            'max_value': None,
            'unit': 'N',
            'test_method': 'Three-point bending test with universal testing machine',
            'applicable_product_types': ['floor_tiles', 'gres_cerame']
        },
        {
            'standard_code': 'ISO 10545-4',
            'standard_name': 'Ceramic tiles - Determination of modulus of rupture and breaking strength',
            'parameter_name': 'breaking_strength_n',
            'min_value': 600,  # min. 600 N for wall tiles
            'max_value': None,
            'unit': 'N',
            'test_method': 'Three-point bending test with universal testing machine',
            'applicable_product_types': ['wall_tiles']
        },
        
        # ISO 10545-7 - Abrasion resistance
        {
            'standard_code': 'ISO 10545-7',
            'standard_name': 'Ceramic tiles - Determination of resistance to surface abrasion',
            'parameter_name': 'abrasion_resistance_pei',
            'min_value': 1,  # PEI I for wall tiles
            'max_value': 5,  # PEI V for heavy commercial use
            'unit': 'PEI',
            'test_method': 'Rotating abrasive wheel test with standard abrasive charge',
            'applicable_product_types': ['floor_tiles', 'commercial_tiles']
        },
        
        # IMANOR Morocco specific standards
        {
            'standard_code': 'NM 10.1.008',
            'standard_name': 'Moroccan standard for ceramic tiles quality',
            'parameter_name': 'thermal_shock_resistance',
            'min_value': 10,  # minimum 10 cycles
            'max_value': None,
            'unit': 'cycles',
            'test_method': 'Temperature cycling between 15°C and 145°C',
            'applicable_product_types': ['floor_tiles', 'exterior_tiles']
        },
        {
            'standard_code': 'NM 10.1.008',
            'standard_name': 'Moroccan standard for ceramic tiles quality',
            'parameter_name': 'frost_resistance',
            'min_value': 100,  # minimum 100 freeze-thaw cycles
            'max_value': None,
            'unit': 'cycles',
            'test_method': 'Freeze-thaw cycling test',
            'applicable_product_types': ['exterior_tiles', 'outdoor_tiles']
        }
    ]
    
    try:
        # Clear existing standards
        db.execute_query("DELETE FROM iso_standards")
        
        # Insert ISO standards
        for standard in iso_standards:
            db.insert_record('iso_standards', standard)
        
        logger.info(f"Successfully seeded {len(iso_standards)} ISO standards")
        
    except Exception as e:
        logger.error(f"Error seeding ISO standards: {e}")

def seed_sample_data(db: DatabaseManager):
    """Seed the database with sample data for demonstration"""
    
    try:
        # Create admin user
        admin_user = {
            'username': 'admin',
            'email': 'admin@ceramicadersa.com',
            'password': 'admin123',  # Will be hashed by AuthService
            'full_name': 'Administrator',
            'role': 'admin',
            'department': 'Management',
            'is_active': True
        }
        
        # Create sample users
        sample_users = [
            {
                'username': 'tech_quality',
                'email': 'quality@ceramicadersa.com',
                'password': 'quality123',
                'full_name': 'Ahmed Benali',
                'role': 'quality_technician',
                'department': 'Quality Control',
                'is_active': True
            },
            {
                'username': 'prod_manager',
                'email': 'production@ceramicadersa.com',
                'password': 'prod123',
                'full_name': 'Fatima El Khatib',
                'role': 'production_manager',
                'department': 'Production',
                'is_active': True
            },
            {
                'username': 'env_manager',
                'email': 'environment@ceramicadersa.com',
                'password': 'env123',
                'full_name': 'Omar Tazi',
                'role': 'environment_manager',
                'department': 'Environment',
                'is_active': True
            }
        ]
        
        # Note: In real implementation, we would use AuthService to hash passwords
        # For now, we'll insert users manually
        
        logger.info("Sample data seeding completed")
        
    except Exception as e:
        logger.error(f"Error seeding sample data: {e}")

def seed_environmental_kpis(db: DatabaseManager):
    """Seed environmental KPI targets"""
    
    kpi_targets = [
        {
            'kpi_name': 'energy_reduction_target',
            'kpi_value': 12.0,  # 12% reduction target
            'target_value': 12.0,
            'unit': '%',
            'category': 'Energy',
            'calculation_method': 'Annual energy consumption reduction percentage',
            'data_source': 'Energy monitoring system'
        },
        {
            'kpi_name': 'liquid_waste_recycling',
            'kpi_value': 100.0,  # 100% recycling target
            'target_value': 100.0,
            'unit': '%',
            'category': 'Waste',
            'calculation_method': 'Percentage of liquid waste recycled',
            'data_source': 'Waste management system'
        },
        {
            'kpi_name': 'heat_recovery_annual',
            'kpi_value': 511.0,  # 511 MWh/year target
            'target_value': 511.0,
            'unit': 'MWh',
            'category': 'Energy',
            'calculation_method': 'Annual heat recovery from kilns',
            'data_source': 'Heat recovery monitoring'
        },
        {
            'kpi_name': 'solid_waste_valorization',
            'kpi_value': 100.0,  # 100% valorization target
            'target_value': 100.0,
            'unit': '%',
            'category': 'Waste',
            'calculation_method': 'Percentage of solid waste reused/recycled',
            'data_source': 'Waste tracking system'
        }
    ]
    
    try:
        for kpi in kpi_targets:
            db.insert_record('environmental_kpis', kpi)
        
        logger.info(f"Successfully seeded {len(kpi_targets)} environmental KPIs")
        
    except Exception as e:
        logger.error(f"Error seeding environmental KPIs: {e}")

def run_seed():
    """Run all seeding functions"""
    try:
        db = DatabaseManager()
        
        logger.info("Starting database seeding...")
        
        seed_iso_standards(db)
        seed_environmental_kpis(db)
        seed_sample_data(db)
        
        logger.info("Database seeding completed successfully")
        
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_seed()