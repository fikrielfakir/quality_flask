"""
Dersa EcoQuality - Business Logic Services
Service layer for quality management operations
"""

import bcrypt
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from models import DatabaseManager, UserRole, TestStatus, DefectType, EnergySource, WasteType, BatchStatus
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        try:
            user = self.db.execute_single(
                "SELECT * FROM users WHERE username = %s AND is_active = true",
                (username,)
            )
            
            if user and self.verify_password(password, user['password_hash']):
                # Update last login
                self.db.execute_single(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user['id'],)
                )
                
                # Remove password from response
                del user['password_hash']
                return user
            
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user"""
        try:
            # Hash password
            user_data['password_hash'] = self.hash_password(user_data.pop('password'))
            
            # Insert user
            user = self.db.insert_record('users', user_data)
            
            if user:
                del user['password_hash']
            
            return user
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return None

class ProductionService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_production_batch(self, batch_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new production batch"""
        try:
            return self.db.insert_record('production_batches', batch_data)
        except Exception as e:
            logger.error(f"Batch creation error: {e}")
            return None

    def get_production_batches(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get production batches with optional filters"""
        try:
            base_query = """
                SELECT pb.*, u.full_name as supervisor_name
                FROM production_batches pb
                LEFT JOIN users u ON pb.supervisor_id = u.id
            """
            
            conditions = []
            params = []
            
            if filters:
                if filters.get('status'):
                    conditions.append("pb.status = %s")
                    params.append(filters['status'])
                
                if filters.get('date_from'):
                    conditions.append("pb.production_date >= %s")
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    conditions.append("pb.production_date <= %s")
                    params.append(filters['date_to'])
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += " ORDER BY pb.production_date DESC"
            
            return self.db.execute_query(base_query, tuple(params))
        except Exception as e:
            logger.error(f"Batch retrieval error: {e}")
            return []

    def update_batch_status(self, batch_id: int, status: str, notes: str = None) -> bool:
        """Update batch status"""
        try:
            update_data = {'status': status, 'updated_at': datetime.now()}
            if notes:
                update_data['notes'] = notes
            
            query = """
                UPDATE production_batches 
                SET status = %(status)s, updated_at = %(updated_at)s
            """
            params = update_data
            
            if notes:
                query += ", notes = %(notes)s"
            
            query += " WHERE id = %(id)s"
            params['id'] = batch_id
            
            self.db.execute_single(query, params)
            return True
        except Exception as e:
            logger.error(f"Batch status update error: {e}")
            return False

class QualityService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_quality_test(self, test_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new quality test"""
        try:
            # Validate against ISO standards if applicable
            if test_data.get('test_type'):
                iso_compliance = self._check_iso_compliance(test_data)
                test_data['iso_compliant'] = iso_compliance
                test_data['pass_fail'] = 'PASS' if iso_compliance else 'FAIL'
            
            return self.db.insert_record('quality_tests', test_data)
        except Exception as e:
            logger.error(f"Quality test creation error: {e}")
            return None

    def _check_iso_compliance(self, test_data: Dict[str, Any]) -> bool:
        """Check if test results comply with ISO standards"""
        try:
            # Get applicable ISO standards
            standards = self.db.execute_query("""
                SELECT * FROM iso_standards 
                WHERE is_active = true
            """)
            
            compliant = True
            
            for standard in standards:
                param_name = standard['parameter_name'].lower()
                
                # Check dimensional compliance (ISO 13006)
                if 'length' in param_name and test_data.get('length_mm'):
                    if not self._is_within_tolerance(test_data['length_mm'], standard):
                        compliant = False
                
                if 'width' in param_name and test_data.get('width_mm'):
                    if not self._is_within_tolerance(test_data['width_mm'], standard):
                        compliant = False
                
                if 'thickness' in param_name and test_data.get('thickness_mm'):
                    if not self._is_within_tolerance(test_data['thickness_mm'], standard):
                        compliant = False
                
                # Check warping (≤0.6% for rectified tiles)
                if 'warping' in param_name and test_data.get('warping_percentage'):
                    if not self._is_within_tolerance(test_data['warping_percentage'], standard):
                        compliant = False
                
                # Check water absorption (≤3% for gres cérame)
                if 'water_absorption' in param_name and test_data.get('water_absorption_percentage'):
                    if not self._is_within_tolerance(test_data['water_absorption_percentage'], standard):
                        compliant = False
                
                # Check breaking strength (min 1300N for floor tiles)
                if 'breaking_strength' in param_name and test_data.get('breaking_strength_n'):
                    if not self._is_within_tolerance(test_data['breaking_strength_n'], standard):
                        compliant = False
            
            return compliant
        except Exception as e:
            logger.error(f"ISO compliance check error: {e}")
            return False

    def _is_within_tolerance(self, value: float, standard: Dict[str, Any]) -> bool:
        """Check if value is within standard tolerance"""
        if standard['min_value'] is not None and value < standard['min_value']:
            return False
        if standard['max_value'] is not None and value > standard['max_value']:
            return False
        return True

    def get_quality_tests(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get quality tests with optional filters"""
        try:
            base_query = """
                SELECT qt.*, pb.batch_number, pb.product_type, u.full_name as technician_name
                FROM quality_tests qt
                LEFT JOIN production_batches pb ON qt.batch_id = pb.id
                LEFT JOIN users u ON qt.technician_id = u.id
            """
            
            conditions = []
            params = []
            
            if filters:
                if filters.get('batch_id'):
                    conditions.append("qt.batch_id = %s")
                    params.append(filters['batch_id'])
                
                if filters.get('status'):
                    conditions.append("qt.status = %s")
                    params.append(filters['status'])
                
                if filters.get('date_from'):
                    conditions.append("qt.test_date >= %s")
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    conditions.append("qt.test_date <= %s")
                    params.append(filters['date_to'])
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += " ORDER BY qt.test_date DESC"
            
            return self.db.execute_query(base_query, tuple(params))
        except Exception as e:
            logger.error(f"Quality tests retrieval error: {e}")
            return []

class EnergyService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def record_energy_consumption(self, consumption_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Record energy consumption"""
        try:
            # Calculate efficiency if target is provided
            if consumption_data.get('target_consumption'):
                actual = consumption_data['consumption_kwh']
                target = consumption_data['target_consumption']
                efficiency = (target / actual) * 100 if actual > 0 else 0
                consumption_data['efficiency_percentage'] = round(efficiency, 2)
            
            return self.db.insert_record('energy_consumption', consumption_data)
        except Exception as e:
            logger.error(f"Energy consumption recording error: {e}")
            return None

    def get_energy_consumption(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get energy consumption records"""
        try:
            base_query = """
                SELECT ec.*, u.full_name as recorded_by_name
                FROM energy_consumption ec
                LEFT JOIN users u ON ec.recorded_by = u.id
            """
            
            conditions = []
            params = []
            
            if filters:
                if filters.get('source'):
                    conditions.append("ec.source = %s")
                    params.append(filters['source'])
                
                if filters.get('date_from'):
                    conditions.append("ec.recorded_date >= %s")
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    conditions.append("ec.recorded_date <= %s")
                    params.append(filters['date_to'])
                
                if filters.get('department'):
                    conditions.append("ec.department = %s")
                    params.append(filters['department'])
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += " ORDER BY ec.recorded_date DESC, ec.recorded_time DESC"
            
            return self.db.execute_query(base_query, tuple(params))
        except Exception as e:
            logger.error(f"Energy consumption retrieval error: {e}")
            return []

    def record_heat_recovery(self, recovery_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Record heat recovery data"""
        try:
            # Calculate thermal efficiency
            if recovery_data.get('input_temperature') and recovery_data.get('output_temperature'):
                input_temp = recovery_data['input_temperature']
                output_temp = recovery_data['output_temperature']
                efficiency = ((input_temp - output_temp) / input_temp) * 100 if input_temp > 0 else 0
                recovery_data['thermal_efficiency_percentage'] = round(efficiency, 2)
            
            return self.db.insert_record('heat_recovery', recovery_data)
        except Exception as e:
            logger.error(f"Heat recovery recording error: {e}")
            return None

class WasteService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def record_waste(self, waste_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Record waste data"""
        try:
            return self.db.insert_record('waste_records', waste_data)
        except Exception as e:
            logger.error(f"Waste recording error: {e}")
            return None

    def get_waste_records(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get waste records"""
        try:
            base_query = """
                SELECT wr.*, u.full_name as responsible_person_name
                FROM waste_records wr
                LEFT JOIN users u ON wr.responsible_person_id = u.id
            """
            
            conditions = []
            params = []
            
            if filters:
                if filters.get('waste_type'):
                    conditions.append("wr.waste_type = %s")
                    params.append(filters['waste_type'])
                
                if filters.get('date_from'):
                    conditions.append("wr.recorded_date >= %s")
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    conditions.append("wr.recorded_date <= %s")
                    params.append(filters['date_to'])
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += " ORDER BY wr.recorded_date DESC"
            
            return self.db.execute_query(base_query, tuple(params))
        except Exception as e:
            logger.error(f"Waste records retrieval error: {e}")
            return []

class DashboardService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_kpi_summary(self) -> Dict[str, Any]:
        """Get KPI summary for dashboard"""
        try:
            today = date.today()
            month_start = today.replace(day=1)
            
            # Production KPIs
            production_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_batches,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_batches,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_batches,
                    SUM(actual_quantity) as total_production
                FROM production_batches 
                WHERE production_date >= %s
            """, (month_start,))
            
            # Quality KPIs
            quality_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_tests,
                    SUM(CASE WHEN pass_fail = 'PASS' THEN 1 ELSE 0 END) as passed_tests,
                    AVG(CASE WHEN iso_compliant THEN 1.0 ELSE 0.0 END) * 100 as compliance_rate
                FROM quality_tests 
                WHERE test_date >= %s
            """, (month_start,))
            
            # Energy KPIs
            energy_stats = self.db.execute_single("""
                SELECT 
                    SUM(consumption_kwh) as total_consumption,
                    AVG(efficiency_percentage) as avg_efficiency,
                    SUM(cost_amount) as total_cost
                FROM energy_consumption 
                WHERE recorded_date >= %s
            """, (month_start,))
            
            # Waste KPIs
            waste_stats = self.db.execute_single("""
                SELECT 
                    SUM(quantity_kg) as total_waste,
                    AVG(recycling_percentage) as avg_recycling_rate,
                    SUM(valorization_amount) as total_valorization
                FROM waste_records 
                WHERE recorded_date >= %s
            """, (month_start,))
            
            # Heat Recovery KPIs
            heat_recovery_stats = self.db.execute_single("""
                SELECT 
                    SUM(heat_recovered_kwh) as total_heat_recovered,
                    AVG(thermal_efficiency_percentage) as avg_thermal_efficiency,
                    SUM(energy_savings_kwh) as total_energy_savings
                FROM heat_recovery 
                WHERE recorded_date >= %s
            """, (month_start,))
            
            return {
                'production': production_stats or {},
                'quality': quality_stats or {},
                'energy': energy_stats or {},
                'waste': waste_stats or {},
                'heat_recovery': heat_recovery_stats or {},
                'period': f"{month_start} to {today}"
            }
        except Exception as e:
            logger.error(f"KPI summary error: {e}")
            return {}

    def get_trend_data(self, metric: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get trend data for charts"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            if metric == 'energy_consumption':
                return self.db.execute_query("""
                    SELECT 
                        recorded_date as date,
                        SUM(consumption_kwh) as value,
                        source
                    FROM energy_consumption 
                    WHERE recorded_date BETWEEN %s AND %s
                    GROUP BY recorded_date, source
                    ORDER BY recorded_date
                """, (start_date, end_date))
            
            elif metric == 'quality_rate':
                return self.db.execute_query("""
                    SELECT 
                        test_date as date,
                        AVG(CASE WHEN pass_fail = 'PASS' THEN 1.0 ELSE 0.0 END) * 100 as value
                    FROM quality_tests 
                    WHERE test_date BETWEEN %s AND %s
                    GROUP BY test_date
                    ORDER BY test_date
                """, (start_date, end_date))
            
            elif metric == 'waste_generation':
                return self.db.execute_query("""
                    SELECT 
                        recorded_date as date,
                        SUM(quantity_kg) as value,
                        waste_type
                    FROM waste_records 
                    WHERE recorded_date BETWEEN %s AND %s
                    GROUP BY recorded_date, waste_type
                    ORDER BY recorded_date
                """, (start_date, end_date))
            
            return []
        except Exception as e:
            logger.error(f"Trend data error: {e}")
            return []