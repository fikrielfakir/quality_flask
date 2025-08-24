"""
Dersa EcoQuality - Energy Management Routes
Energy consumption tracking and efficiency monitoring
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from data.database import DatabaseManager
from utils.helpers import validate_required_fields, safe_float_convert
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)
energy_bp = Blueprint('energy', __name__)

db = DatabaseManager()

@energy_bp.route('/energy', methods=['GET', 'POST'])
def energy():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            data = {
                'recorded_date': request.form.get('recorded_date'),
                'source': request.form.get('source'),
                'equipment_name': request.form.get('equipment_name'),
                'department': request.form.get('department'),
                'consumption_kwh': safe_float_convert(request.form.get('consumption_kwh')),
                'cost_amount': safe_float_convert(request.form.get('cost_amount')),
                'meter_reading': safe_float_convert(request.form.get('meter_reading')),
                'efficiency_percentage': safe_float_convert(request.form.get('efficiency_percentage')),
                'target_consumption': safe_float_convert(request.form.get('target_consumption')),
                'notes': request.form.get('notes'),
                'recorded_by': session.get('user_id')
            }
            
            # Validate required fields
            required_fields = ['recorded_date', 'source', 'consumption_kwh']
            missing_fields = validate_required_fields(data, required_fields)
            
            if missing_fields:
                flash(f'Required fields missing: {", ".join(missing_fields)}', 'error')
                return redirect(url_for('energy.energy'))
            
            if data['consumption_kwh'] <= 0:
                flash('Consumption must be a positive number', 'error')
                return redirect(url_for('energy.energy'))
            
            # Remove empty values
            data = {k: v for k, v in data.items() if v is not None and v != '' and v != 0.0}
            
            result = db.insert_record('energy_consumption', data)
            
            if result:
                flash('Energy consumption recorded successfully', 'success')
            else:
                flash('Error recording energy consumption', 'error')
        
        except Exception as e:
            logger.error(f"Error recording energy consumption: {e}")
            flash('Error recording energy consumption', 'error')
    
    # Get recent energy records
    energy_records = db.execute_query("""
        SELECT ec.*, u.full_name as recorded_by_name
        FROM energy_consumption ec
        LEFT JOIN users u ON ec.recorded_by = u.id
        ORDER BY ec.recorded_date DESC, ec.created_at DESC
        LIMIT 50
    """)
    
    # Add today's date for the form
    today = date.today().isoformat()
    
    return render_template('energy.html', 
                         energy_records=energy_records or [],
                         today=today)