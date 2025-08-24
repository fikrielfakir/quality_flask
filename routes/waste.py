"""
Dersa EcoQuality - Waste Management Routes
Waste tracking and recycling management
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from data.database import DatabaseManager
from utils.helpers import validate_required_fields, safe_float_convert
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)
waste_bp = Blueprint('waste', __name__)

db = DatabaseManager()

@waste_bp.route('/waste', methods=['GET', 'POST'])
def waste():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            data = {
                'recorded_date': request.form.get('recorded_date'),
                'waste_type': request.form.get('waste_type'),
                'quantity_kg': safe_float_convert(request.form.get('quantity_kg')),
                'source_department': request.form.get('source_department'),
                'disposal_method': request.form.get('disposal_method'),
                'recycling_percentage': safe_float_convert(request.form.get('recycling_percentage')),
                'valorization_amount': safe_float_convert(request.form.get('valorization_amount')),
                'cost_amount': safe_float_convert(request.form.get('cost_amount')),
                'destination': request.form.get('destination'),
                'certificate_number': request.form.get('certificate_number'),
                'notes': request.form.get('notes'),
                'responsible_person_id': session.get('user_id')
            }
            
            # Validate required fields
            required_fields = ['recorded_date', 'waste_type', 'quantity_kg']
            missing_fields = validate_required_fields(data, required_fields)
            
            if missing_fields:
                flash(f'Required fields missing: {", ".join(missing_fields)}', 'error')
                return redirect(url_for('waste.waste'))
            
            if data['quantity_kg'] <= 0:
                flash('Quantity must be a positive number', 'error')
                return redirect(url_for('waste.waste'))
            
            # Remove empty values
            data = {k: v for k, v in data.items() if v is not None and v != '' and v != 0.0}
            
            result = db.insert_record('waste_records', data)
            
            if result:
                flash('Waste record created successfully', 'success')
            else:
                flash('Error creating waste record', 'error')
        
        except Exception as e:
            logger.error(f"Error recording waste: {e}")
            flash('Error recording waste', 'error')
    
    # Get recent waste records
    waste_records = db.execute_query("""
        SELECT wr.*, u.full_name as responsible_person_name
        FROM waste_records wr
        LEFT JOIN users u ON wr.responsible_person_id = u.id
        ORDER BY wr.recorded_date DESC, wr.created_at DESC
        LIMIT 50
    """)
    
    # Add today's date for the form
    today = date.today().isoformat()
    
    return render_template('waste.html', 
                         waste_records=waste_records or [],
                         today=today)