"""
Dersa EcoQuality - Main Application Routes
Dashboard and core functionality
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from data.database import DatabaseManager
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

db = DatabaseManager()

@main_bp.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        today = date.today()
        month_start = today.replace(day=1)
        
        # Get KPIs
        kpis = {
            'production': db.execute_single("""
                SELECT 
                    COUNT(*) as total_batches,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_batches,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_batches,
                    SUM(actual_quantity) as total_production
                FROM production_batches 
                WHERE production_date >= ?
            """, (month_start,)) or {},
            
            'quality': db.execute_single("""
                SELECT 
                    COUNT(*) as total_tests,
                    SUM(CASE WHEN pass_fail = 'PASS' THEN 1 ELSE 0 END) as passed_tests,
                    AVG(CASE WHEN iso_compliant = 1 THEN 1.0 ELSE 0.0 END) * 100 as compliance_rate
                FROM quality_tests 
                WHERE test_date >= ?
            """, (month_start,)) or {},
            
            'energy': db.execute_single("""
                SELECT 
                    SUM(consumption_kwh) as total_consumption,
                    AVG(efficiency_percentage) as avg_efficiency,
                    SUM(cost_amount) as total_cost
                FROM energy_consumption 
                WHERE recorded_date >= ?
            """, (month_start,)) or {},
            
            'waste': db.execute_single("""
                SELECT 
                    SUM(quantity_kg) as total_waste,
                    AVG(recycling_percentage) as avg_recycling_rate,
                    SUM(valorization_amount) as total_valorization
                FROM waste_records 
                WHERE recorded_date >= ?
            """, (month_start,)) or {}
        }
        
        # Get recent batches
        recent_batches = db.execute_query("""
            SELECT * FROM production_batches 
            ORDER BY production_date DESC 
            LIMIT 10
        """)
        
        # Get recent tests
        recent_tests = db.execute_query("""
            SELECT qt.*, pb.batch_number 
            FROM quality_tests qt
            LEFT JOIN production_batches pb ON qt.batch_id = pb.id
            ORDER BY qt.test_date DESC 
            LIMIT 10
        """)
        
        return render_template('dashboard.html', 
                             kpis=kpis, 
                             recent_batches=recent_batches, 
                             recent_tests=recent_tests)
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('dashboard.html', 
                             kpis={'production': {}, 'quality': {}, 'energy': {}, 'waste': {}}, 
                             recent_batches=[], 
                             recent_tests=[])

@main_bp.route('/users')
def users():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        all_users = db.execute_query("""
            SELECT id, username, email, full_name, role, department, is_active, 
                   created_at, last_login 
            FROM users 
            ORDER BY created_at DESC
        """)
        
        return render_template('users.html', users=all_users)
    
    except Exception as e:
        logger.error(f"Users page error: {e}")
        flash('Error loading users', 'error')
        return render_template('users.html', users=[])