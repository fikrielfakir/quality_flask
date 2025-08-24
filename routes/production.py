"""
Dersa EcoQuality - Production Routes
Production batch management and tracking
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from data.database import DatabaseManager
from utils.helpers import validate_required_fields, safe_int_convert, safe_float_convert
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)
production_bp = Blueprint('production', __name__)

db = DatabaseManager()

@production_bp.route('/production', methods=['GET', 'POST'])
def production():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        return create_production_lot()
    
    return display_production_lots()

def create_production_lot():
    """Create a new production lot"""
    try:
        # Extract form data
        form_data = {
            'batch_number': request.form.get('batch_number', '').strip(),
            'product_type': request.form.get('product_type', '').strip(),
            'production_date': request.form.get('production_date', '').strip(),
            'planned_quantity': request.form.get('planned_quantity', '').strip(),
            'kiln_number': request.form.get('kiln_number', '').strip(),
            'firing_temperature': request.form.get('firing_temperature', '').strip(),
            'firing_duration': request.form.get('firing_duration', '').strip(),
            'notes': request.form.get('notes', '').strip()
        }
        
        # Validate required fields
        required_fields = ['batch_number', 'product_type', 'production_date', 'planned_quantity']
        missing_fields = validate_required_fields(form_data, required_fields)
        
        if missing_fields:
            flash(f'Required fields missing: {", ".join(missing_fields)}', 'error')
            return redirect(url_for('production.production'))
        
        # Validate and convert data types
        planned_quantity = safe_int_convert(form_data['planned_quantity'])
        if planned_quantity <= 0:
            flash('Planned quantity must be a positive number', 'error')
            return redirect(url_for('production.production'))
        
        firing_temperature = None
        if form_data['firing_temperature']:
            firing_temperature = safe_float_convert(form_data['firing_temperature'])
            if firing_temperature < 500 or firing_temperature > 1500:
                flash('Firing temperature must be between 500 and 1500°C', 'error')
                return redirect(url_for('production.production'))
        
        # Check for duplicate batch number
        existing_batch = db.execute_single(
            "SELECT id, batch_number FROM production_batches WHERE batch_number = ?", 
            (form_data['batch_number'],)
        )
        
        if existing_batch:
            flash(f'Error: Batch number "{form_data["batch_number"]}" already exists', 'error')
            return redirect(url_for('production.production'))
        
        # Prepare data for database insertion
        lot_data = {
            'batch_number': form_data['batch_number'],
            'product_type': form_data['product_type'],
            'production_date': form_data['production_date'],
            'planned_quantity': planned_quantity,
            'kiln_number': form_data['kiln_number'] if form_data['kiln_number'] else None,
            'firing_temperature': firing_temperature,
            'firing_duration': form_data['firing_duration'] if form_data['firing_duration'] else None,
            'supervisor_id': session.get('user_id'),
            'notes': form_data['notes'] if form_data['notes'] else None,
            'status': 'planned',
            'actual_quantity': None
        }
        
        # Insert into database
        result = db.insert_record('production_batches', lot_data)
        
        if result:
            flash(f'Production lot "{form_data["batch_number"]}" created successfully', 'success')
            logger.info(f"Production lot created: {form_data['batch_number']} by user {session.get('username')}")
        else:
            flash('Error: Unable to create production lot', 'error')
        
        return redirect(url_for('production.production'))
        
    except Exception as e:
        flash('System error creating production lot', 'error')
        logger.error(f"Error in create_production_lot: {e}", exc_info=True)
        return redirect(url_for('production.production'))

def display_production_lots():
    """Display production lots with filtering"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        
        # Build query with filters
        base_query = """
            SELECT 
                pb.*,
                u.full_name as supervisor_name,
                u.username as supervisor_username
            FROM production_batches pb
            LEFT JOIN users u ON pb.supervisor_id = u.id
        """
        
        conditions = []
        params = []
        
        if status_filter:
            conditions.append("pb.status = ?")
            params.append(status_filter)
        
        if date_from:
            conditions.append("pb.production_date >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("pb.production_date <= ?")
            params.append(date_to)
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " ORDER BY pb.production_date DESC, pb.created_at DESC"
        
        # Execute query
        batches = db.execute_query(base_query, tuple(params)) if params else db.execute_query(base_query)
        
        if batches is None:
            batches = []
        
        # Add today's date for the form
        today = date.today().isoformat()
        
        return render_template('production.html', batches=batches, today=today)
        
    except Exception as e:
        logger.error(f"Error displaying production lots: {e}", exc_info=True)
        flash('Error loading production lots', 'error')
        today = date.today().isoformat()
        return render_template('production.html', batches=[], today=today)