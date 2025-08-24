"""
Dersa EcoQuality - Quality Control Routes
Quality testing and compliance management
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from data.database import DatabaseManager
from utils.helpers import validate_required_fields, safe_int_convert, safe_float_convert, save_uploaded_file
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)
quality_bp = Blueprint('quality', __name__)

db = DatabaseManager()

@quality_bp.route('/quality', methods=['GET', 'POST'])
def quality():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            data = {
                'batch_id': safe_int_convert(request.form.get('batch_id')),
                'test_type': request.form.get('test_type'),
                'test_date': request.form.get('test_date'),
                'technician_id': session.get('user_id'),
                'length_mm': safe_float_convert(request.form.get('length_mm')),
                'width_mm': safe_float_convert(request.form.get('width_mm')),
                'thickness_mm': safe_float_convert(request.form.get('thickness_mm')),
                'warping_percentage': safe_float_convert(request.form.get('warping_percentage')),
                'water_absorption_percentage': safe_float_convert(request.form.get('water_absorption_percentage')),
                'breaking_strength_n': safe_int_convert(request.form.get('breaking_strength_n')),
                'abrasion_resistance_pei': safe_int_convert(request.form.get('abrasion_resistance_pei')),
                'defect_type': request.form.get('defect_type', 'none'),
                'defect_count': safe_int_convert(request.form.get('defect_count')),
                'defect_severity': request.form.get('defect_severity', 'minor'),
                'defect_description': request.form.get('defect_description'),
                'equipment_used': request.form.get('equipment_used'),
                'test_notes': request.form.get('test_notes'),
                'status': 'completed'
            }
            
            # Handle photo upload
            defect_photo = request.files.get('defect_photo')
            if defect_photo and defect_photo.filename:
                photo_path = save_uploaded_file(defect_photo, 'defects')
                if photo_path:
                    data['defect_image_url'] = photo_path
                else:
                    flash('Photo upload failed, but test was recorded', 'warning')
            
            # Simple ISO compliance check
            iso_compliant = check_iso_compliance(data)
            data['iso_compliant'] = iso_compliant
            data['pass_fail'] = 'PASS' if iso_compliant else 'FAIL'
            
            # Remove empty values
            data = {k: v for k, v in data.items() if v is not None and v != '' and v != 0.0}
            
            # Insert quality test
            result = db.insert_record('quality_tests', data)
            
            if result:
                flash('Quality test recorded successfully', 'success')
                logger.info(f"Quality test recorded for batch {data.get('batch_id')} by user {session.get('username')}")
            else:
                flash('Error recording quality test', 'error')
        
        except Exception as e:
            logger.error(f"Error recording quality test: {e}")
            flash('Error recording quality test', 'error')
    
    # Get data for the page
    iso_standards = db.execute_query("SELECT * FROM iso_standards WHERE is_active = 1 ORDER BY standard_code")
    production_batches = db.execute_query("""
        SELECT id, batch_number, product_type, production_date, status 
        FROM production_batches 
        WHERE status IN ('in_production', 'quality_testing', 'planned')
        ORDER BY production_date DESC
    """)
    
    # Get recent quality tests
    recent_tests = db.execute_query("""
        SELECT qt.*, pb.batch_number, pb.product_type,
               u.full_name as technician_name
        FROM quality_tests qt
        LEFT JOIN production_batches pb ON qt.batch_id = pb.id
        LEFT JOIN users u ON qt.technician_id = u.id
        ORDER BY qt.test_date DESC, qt.created_at DESC
        LIMIT 20
    """)
    
    # Add today's date for the form
    today = date.today().isoformat()
    
    return render_template('quality.html', 
                         iso_standards=iso_standards or [],
                         production_batches=production_batches or [],
                         recent_tests=recent_tests or [],
                         today=today)

def check_iso_compliance(data):
    """Simple ISO compliance check based on standards"""
    try:
        # Get applicable standards for the test
        standards = db.execute_query("""
            SELECT * FROM iso_standards 
            WHERE is_active = 1 AND parameter_name IN (?, ?, ?, ?)
        """, ('length_mm', 'water_absorption_percentage', 'breaking_strength_n', 'warping_percentage'))
        
        compliant = True
        
        for standard in standards or []:
            param_name = standard['parameter_name']
            value = data.get(param_name)
            
            if value is not None and value > 0:
                min_val = standard.get('min_value')
                max_val = standard.get('max_value')
                
                if min_val is not None and value < min_val:
                    compliant = False
                    break
                    
                if max_val is not None and value > max_val:
                    compliant = False
                    break
        
        return compliant
        
    except Exception as e:
        logger.error(f"Error checking ISO compliance: {e}")
        return False  # Default to non-compliant on error