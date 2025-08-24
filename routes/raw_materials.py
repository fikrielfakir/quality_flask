"""
Dersa EcoQuality - Raw Materials Routes
Raw materials management and inventory
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from data.database import DatabaseManager
from utils.helpers import validate_required_fields, safe_float_convert
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)
raw_materials_bp = Blueprint('raw_materials', __name__)

db = DatabaseManager()

@raw_materials_bp.route('/raw_materials', methods=['GET', 'POST'])
def raw_materials():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            data = {
                'material_code': request.form.get('material_code'),
                'material_name': request.form.get('material_name'),
                'material_type': request.form.get('material_type'),
                'reception_date': request.form.get('reception_date'),
                'lot_number': request.form.get('lot_number'),
                'quantity_kg': safe_float_convert(request.form.get('quantity_kg')),
                'unit_cost': safe_float_convert(request.form.get('unit_cost')),
                'humidity_percentage': safe_float_convert(request.form.get('humidity_percentage')),
                'particle_size_microns': safe_float_convert(request.form.get('particle_size_microns')),
                'chemical_composition': request.form.get('chemical_composition'),
                'inspection_notes': request.form.get('inspection_notes'),
                'storage_location': request.form.get('storage_location'),
                'expiry_date': request.form.get('expiry_date'),
                'status': 'en_attente',
                'inspected_by': session.get('user_id')
            }
            
            # Validate required fields
            required_fields = ['material_code', 'material_name', 'material_type', 'reception_date', 'quantity_kg']
            missing_fields = validate_required_fields(data, required_fields)
            
            if missing_fields:
                flash(f'Required fields missing: {", ".join(missing_fields)}', 'error')
                return redirect(url_for('raw_materials.raw_materials'))
            
            if data['quantity_kg'] <= 0:
                flash('Quantity must be a positive number', 'error')
                return redirect(url_for('raw_materials.raw_materials'))
            
            # Check for duplicate material code
            existing = db.execute_single(
                "SELECT id FROM raw_materials WHERE material_code = ?", 
                (data['material_code'],)
            )
            
            if existing:
                flash(f'Material code "{data["material_code"]}" already exists', 'error')
                return redirect(url_for('raw_materials.raw_materials'))
            
            # Remove empty values
            data = {k: v for k, v in data.items() if v is not None and v != '' and v != 0.0}
            
            result = db.insert_record('raw_materials', data)
            
            if result:
                flash('Raw material record created successfully', 'success')
            else:
                flash('Error creating raw material record', 'error')
        
        except Exception as e:
            logger.error(f"Error recording raw material: {e}")
            flash('Error recording raw material', 'error')
    
    # Get recent raw material records
    materials = db.execute_query("""
        SELECT rm.*, 
               u1.full_name as inspected_by_name,
               u2.full_name as approved_by_name
        FROM raw_materials rm
        LEFT JOIN users u1 ON rm.inspected_by = u1.id
        LEFT JOIN users u2 ON rm.approved_by = u2.id
        ORDER BY rm.reception_date DESC, rm.created_at DESC
        LIMIT 50
    """)
    
    # Add today's date for the form
    today = date.today().isoformat()
    
    return render_template('raw_materials.html', 
                         materials=materials or [],
                         today=today)