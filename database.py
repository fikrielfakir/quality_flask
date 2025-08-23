import os
import psycopg2
import psycopg2.extras
import bcrypt
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseStorage:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is required")

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

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    # Authentication methods
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by email and password"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM profiles WHERE email = %s",
                        (email,)
                    )
                    profile = cur.fetchone()
                    
                    if not profile:
                        return None
                    
                    if not self.verify_password(password, profile['password']):
                        return None
                    
                    # Return profile without password
                    if profile:
                        profile_dict = {key: value for key, value in profile.items()}
                        del profile_dict['password']
                        return profile_dict
                    return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    # Profile methods
    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get profile by ID"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM profiles WHERE id = %s", (profile_id,))
                profile = cur.fetchone()
                return {key: value for key, value in profile.items()} if profile else None

    def get_profile_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get profile by email"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM profiles WHERE email = %s", (email,))
                profile = cur.fetchone()
                return {key: value for key, value in profile.items()} if profile else None

    def create_profile(self, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new profile"""
        hashed_password = self.hash_password(profile_data['password'])
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO profiles (email, full_name, role, department, password)
                    VALUES (%(email)s, %(full_name)s, %(role)s, %(department)s, %(password)s)
                    RETURNING id, email, full_name, role, department, created_at, updated_at
                """, {
                    **profile_data,
                    'password': hashed_password
                })
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None

    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update profile"""
        if 'password' in updates:
            updates['password'] = self.hash_password(updates['password'])
        
        set_clause = ", ".join([f"{key} = %({key})s" for key in updates.keys()])
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"""
                    UPDATE profiles 
                    SET {set_clause}, updated_at = NOW()
                    WHERE id = %(id)s
                    RETURNING id, email, full_name, role, department, created_at, updated_at
                """, {**updates, 'id': profile_id})
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None

    # Quality tests methods
    def get_quality_tests(self) -> List[Dict[str, Any]]:
        """Get all quality tests"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM quality_tests ORDER BY created_at DESC")
                return [{key: value for key, value in row.items()} for row in cur.fetchall()]

    def create_quality_test(self, test_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new quality test"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO quality_tests (
                        lot_id, test_date, operator_id, length_mm, width_mm, 
                        thickness_mm, water_absorption_percent, break_resistance_n,
                        defect_type, defect_count, status, test_type, notes
                    ) VALUES (
                        %(lot_id)s, %(test_date)s, %(operator_id)s, %(length_mm)s, %(width_mm)s,
                        %(thickness_mm)s, %(water_absorption_percent)s, %(break_resistance_n)s,
                        %(defect_type)s, %(defect_count)s, %(status)s, %(test_type)s, %(notes)s
                    ) RETURNING *
                """, test_data)
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None

    def update_quality_test(self, test_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update quality test"""
        set_clause = ", ".join([f"{key} = %({key})s" for key in updates.keys()])
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"""
                    UPDATE quality_tests 
                    SET {set_clause}, updated_at = NOW()
                    WHERE id = %(id)s
                    RETURNING *
                """, {**updates, 'id': test_id})
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None

    # Production lots methods
    def get_production_lots(self) -> List[Dict[str, Any]]:
        """Get all production lots"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM production_lots ORDER BY created_at DESC")
                return [{key: value for key, value in row.items()} for row in cur.fetchall()]

    def create_production_lot(self, lot_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new production lot"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO production_lots (
                        lot_number, production_date, product_type, quantity, operator_id, status
                    ) VALUES (
                        %(lot_number)s, %(production_date)s, %(product_type)s, %(quantity)s, %(operator_id)s, %(status)s
                    ) RETURNING *
                """, lot_data)
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None

    # Energy consumption methods
    def get_energy_consumption(self) -> List[Dict[str, Any]]:
        """Get all energy consumption records"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM energy_consumption ORDER BY recorded_date DESC, recorded_time DESC")
                return [{key: value for key, value in row.items()} for row in cur.fetchall()]

    def create_energy_record(self, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new energy consumption record"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO energy_consumption (
                        recorded_date, recorded_time, source, consumption_kwh, 
                        cost_amount, equipment_name, department
                    ) VALUES (
                        %(recorded_date)s, %(recorded_time)s, %(source)s, %(consumption_kwh)s,
                        %(cost_amount)s, %(equipment_name)s, %(department)s
                    ) RETURNING *
                """, record_data)
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None

    # Waste records methods
    def get_waste_records(self) -> List[Dict[str, Any]]:
        """Get all waste records"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM waste_records ORDER BY recorded_date DESC")
                return [{key: value for key, value in row.items()} for row in cur.fetchall()]

    def create_waste_record(self, record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new waste record"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO waste_records (
                        recorded_date, waste_type, quantity_kg, disposal_method,
                        cost_amount, responsible_person_id, notes
                    ) VALUES (
                        %(recorded_date)s, %(waste_type)s, %(quantity_kg)s, %(disposal_method)s,
                        %(cost_amount)s, %(responsible_person_id)s, %(notes)s
                    ) RETURNING *
                """, record_data)
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None

    # Compliance documents methods
    def get_compliance_documents(self) -> List[Dict[str, Any]]:
        """Get all compliance documents"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM compliance_documents ORDER BY created_at DESC")
                return [{key: value for key, value in row.items()} for row in cur.fetchall()]

    def create_compliance_document(self, document_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new compliance document"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO compliance_documents (
                        document_name, document_type, issue_date, expiry_date,
                        issuing_authority, status, file_url, uploaded_by
                    ) VALUES (
                        %(document_name)s, %(document_type)s, %(issue_date)s, %(expiry_date)s,
                        %(issuing_authority)s, %(status)s, %(file_url)s, %(uploaded_by)s
                    ) RETURNING *
                """, document_data)
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None

    # Testing campaigns methods
    def get_testing_campaigns(self) -> List[Dict[str, Any]]:
        """Get all testing campaigns"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM testing_campaigns ORDER BY created_at DESC")
                return [{key: value for key, value in row.items()} for row in cur.fetchall()]

    def create_testing_campaign(self, campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new testing campaign"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO testing_campaigns (
                        campaign_name, start_date, end_date, description, status, created_by
                    ) VALUES (
                        %(campaign_name)s, %(start_date)s, %(end_date)s, %(description)s, %(status)s, %(created_by)s
                    ) RETURNING *
                """, campaign_data)
                result = cur.fetchone()
                return {key: value for key, value in result.items()} if result else None