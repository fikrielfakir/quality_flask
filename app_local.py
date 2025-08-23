"""
Dersa EcoQuality - Local Desktop Application
Flask application configured for local SQLite database
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
import os
import logging
from datetime import datetime, date, timedelta
from local_database import LocalDatabaseManager
import json
from io import BytesIO
import csv
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from enhanced_iso_compliance import check_enhanced_iso_compliance, check_iso_compliance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'dersa_ecoquality_secret_key_2025'
CORS(app)

# Initialize local database
try:
    db = LocalDatabaseManager()
    db.seed_initial_data()
    logger.info("Local database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Global variable to store request start times
request_times = {}

@app.before_request
def log_request():
    start_time = datetime.now()
    request_times[id(request)] = start_time

@app.after_request
def log_response(response):
    request_id = id(request)
    if request_id in request_times:
        duration = datetime.now() - request_times[request_id]
        duration_ms = duration.total_seconds() * 1000
        
        if request.path.startswith('/api'):
            log_line = f"{request.method} {request.path} {response.status_code} in {duration_ms:.0f}ms"
            if len(log_line) > 80:
                log_line = log_line[:79] + "…"
            logger.info(log_line)
        
        # Clean up the request time
        del request_times[request_id]
    
    return response

# Root route - redirect to login or dashboard
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/api')
def api_info():
    return jsonify({
        'application': 'Dersa EcoQuality',
        'description': 'Quality management system for ceramic tile manufacturing',
        'version': '1.0.0',
        'company': 'Ceramica Dersa - Tétouan, Morocco',
        'status': 'running',
        'database': 'SQLite (Local)',
        'modules': {
            'dashboard': '/api/dashboard',
            'authentication': '/api/auth',
            'production': '/api/production',
            'quality': '/api/quality',
            'energy': '/api/energy',
            'waste': '/api/waste',
            'heat_recovery': '/api/heat-recovery',
            'compliance': '/api/compliance',
            'campaigns': '/api/campaigns'
        }
    })

# ============================================================================
# WEB INTERFACE ROUTES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password required', 'error')
            return render_template('login.html')
        
        user = db.execute_single("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
        
        if user and db.verify_password(password, user['password_hash']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            # Update last login
            db.execute_single("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), user['id']))
            
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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
        
        return render_template('dashboard.html', kpis=kpis, recent_batches=recent_batches, recent_tests=recent_tests)
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('dashboard.html', kpis={}, recent_batches=[], recent_tests=[])

@app.route('/production', methods=['GET', 'POST'])
def production():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            batch_number = request.form.get('batch_number')
            product_type = request.form.get('product_type')
            production_date = request.form.get('production_date')
            planned_quantity = request.form.get('planned_quantity')
            
            if not all([batch_number, product_type, production_date, planned_quantity]):
                flash('Veuillez remplir tous les champs obligatoires', 'error')
                return redirect(url_for('production'))
            
            # Prepare data with proper NULL handling
            data = {
                'batch_number': batch_number.strip(),
                'product_type': product_type,
                'production_date': production_date,
                'planned_quantity': int(planned_quantity),
                'kiln_number': request.form.get('kiln_number').strip() if request.form.get('kiln_number') else None,
                'firing_temperature': float(request.form.get('firing_temperature')) if request.form.get('firing_temperature') else None,
                'firing_duration': request.form.get('firing_duration').strip() if request.form.get('firing_duration') else None,
                'supervisor_id': session.get('user_id'),
                'notes': request.form.get('notes').strip() if request.form.get('notes') else None,
                'status': 'planned',
                'actual_quantity': None,
                'start_time': None,
                'end_time': None
            }
            
            # Check if batch number already exists
            existing_batch = db.execute_single(
                "SELECT id FROM production_batches WHERE batch_number = ?", 
                (data['batch_number'],)
            )
            if existing_batch:
                flash(f'Le numéro de lot "{data["batch_number"]}" existe déjà', 'error')
                return redirect(url_for('production'))
            
            batch = db.insert_record('production_batches', data)
            
            if batch:
                flash(f'Lot de production "{data["batch_number"]}" créé avec succès', 'success')
                logger.info(f"Production batch created: {data['batch_number']} by user {session.get('user_id')}")
            else:
                flash('Échec de la création du lot de production', 'error')
                logger.error(f"Failed to create production batch: {data}")
                
        except ValueError as ve:
            logger.error(f"Production batch validation error: {ve}")
            flash('Erreur de validation des données. Vérifiez les valeurs numériques.', 'error')
        except Exception as e:
            logger.error(f"Production batch creation error: {e}")
            flash('Erreur lors de la création du lot de production', 'error')
    
    # Get batches with filters
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = """
        SELECT pb.*, u.full_name as supervisor_name
        FROM production_batches pb
        LEFT JOIN users u ON pb.supervisor_id = u.id
    """
    conditions = []
    params = []
    
    if status:
        conditions.append("pb.status = ?")
        params.append(status)
    if date_from:
        conditions.append("pb.production_date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("pb.production_date <= ?")
        params.append(date_to)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY pb.production_date DESC"
    
    batches = db.execute_query(query, tuple(params))
    return render_template('production.html', batches=batches)

@app.route('/quality', methods=['GET', 'POST'])
def quality():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            data = {
                'batch_id': request.form.get('batch_id', type=int),
                'test_type': request.form.get('test_type'),
                'test_date': request.form.get('test_date'),
                'technician_id': session.get('user_id'),
                'length_mm': request.form.get('length_mm', type=float),
                'width_mm': request.form.get('width_mm', type=float),
                'thickness_mm': request.form.get('thickness_mm', type=float),
                'warping_percentage': request.form.get('warping_percentage', type=float),
                'water_absorption_percentage': request.form.get('water_absorption_percentage', type=float),
                'breaking_strength_n': request.form.get('breaking_strength_n', type=int),
                'abrasion_resistance_pei': request.form.get('abrasion_resistance_pei', type=int),
                'defect_type': request.form.get('defect_type'),
                'defect_count': request.form.get('defect_count', type=int),
                'defect_severity': request.form.get('defect_severity'),
                'defect_description': request.form.get('defect_description'),
                'equipment_used': request.form.get('equipment_used'),
                'test_notes': request.form.get('test_notes'),
                'status': 'completed'
            }
            
            # Handle photo upload
            defect_photo = request.files.get('defect_photo')
            if defect_photo and defect_photo.filename:
                try:
                    filename = secure_filename(defect_photo.filename)
                    # Create uploads directory if it doesn't exist
                    upload_dir = os.path.join('static', 'uploads', 'defects')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Generate unique filename with timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
                    new_filename = f"defect_{timestamp}.{file_extension}"
                    
                    file_path = os.path.join(upload_dir, new_filename)
                    defect_photo.save(file_path)
                    
                    # Store relative path in database
                    data['defect_image_url'] = f"uploads/defects/{new_filename}"
                    
                except Exception as e:
                    logger.error(f"Photo upload error: {e}")
                    flash('Photo upload failed, but test was recorded', 'warning')
            
            # Enhanced equipment tracking
            if data.get('equipment_used'):
                equipment_info = db.get_equipment_by_code(data['equipment_used'])
                if equipment_info:
                    data['equipment_calibration_date'] = equipment_info['last_calibration_date']
                    
                    # Check calibration status
                    if equipment_info['calibration_status'] == 'expired':
                        flash(f"ATTENTION: L'équipement {equipment_info['equipment_name']} a un calibrage expiré!", 'warning')
                    elif equipment_info['calibration_status'] == 'expires_soon':
                        flash(f"AVERTISSEMENT: L'équipement {equipment_info['equipment_name']} nécessite un calibrage prochainement", 'warning')
            
            # Remove empty values
            data = {k: v for k, v in data.items() if v is not None and v != ''}
            
            # Enhanced ISO compliance with scoring
            iso_compliance, compliance_score, corrective_actions = check_enhanced_iso_compliance(data)
            data['iso_compliant'] = iso_compliance
            data['pass_fail'] = 'PASS' if iso_compliance else 'FAIL'
            data['auto_pass_fail'] = True
            data['compliance_score'] = compliance_score
            data['corrective_actions'] = corrective_actions if corrective_actions else None
            
            test = db.insert_record('quality_tests', data)
            
            if test:
                flash('Quality test recorded successfully', 'success')
            else:
                flash('Failed to record quality test', 'error')
                
        except Exception as e:
            logger.error(f"Quality test error: {e}")
            flash('Error recording quality test', 'error')
    
    # Get data for the page
    iso_standards = db.execute_query("SELECT * FROM iso_standards WHERE is_active = 1 ORDER BY standard_code")
    available_batches = db.execute_query("SELECT id, batch_number, product_type FROM production_batches ORDER BY production_date DESC")
    technicians = db.execute_query("SELECT id, full_name FROM users WHERE role IN ('quality_technician', 'admin')")
    
    # Get available equipment
    available_equipment = db.execute_query("""
        SELECT equipment_code, equipment_name, calibration_status, calibration_due_date
        FROM equipment 
        WHERE is_active = 1 
        ORDER BY equipment_name
    """)
    
    # Update equipment calibration status
    db.update_equipment_calibration_status()
    
    tests = db.execute_query("""
        SELECT qt.*, pb.batch_number, pb.product_type, u.full_name as technician_name
        FROM quality_tests qt
        LEFT JOIN production_batches pb ON qt.batch_id = pb.id
        LEFT JOIN users u ON qt.technician_id = u.id
        ORDER BY qt.test_date DESC
    """)
    
    return render_template('quality.html', 
                         iso_standards=iso_standards,
                         available_batches=available_batches,
                         technicians=technicians,
                         available_equipment=available_equipment,
                         tests=tests)

@app.route('/energy', methods=['GET', 'POST'])
def energy():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            form_type = request.form.get('form_type')
            
            if form_type == 'energy_consumption':
                data = {
                    'source': request.form.get('source'),
                    'equipment_name': request.form.get('equipment_name'),
                    'department': request.form.get('department'),
                    'consumption_kwh': request.form.get('consumption_kwh', type=float),
                    'cost_amount': request.form.get('cost_amount', type=float),
                    'meter_reading': request.form.get('meter_reading', type=float),
                    'target_consumption': request.form.get('target_consumption', type=float),
                    'notes': request.form.get('notes'),
                    'recorded_by': session.get('user_id')
                }
                
                # Calculate efficiency
                if data.get('target_consumption') and data.get('consumption_kwh'):
                    efficiency = (data['target_consumption'] / data['consumption_kwh']) * 100
                    data['efficiency_percentage'] = round(efficiency, 2)
                
                # Remove empty values
                data = {k: v for k, v in data.items() if v is not None and v != ''}
                
                record = db.insert_record('energy_consumption', data)
                
                if record:
                    flash('Energy consumption recorded successfully', 'success')
                else:
                    flash('Failed to record energy consumption', 'error')
            
            elif form_type == 'heat_recovery':
                data = {
                    'kiln_id': request.form.get('kiln_id'),
                    'input_temperature': request.form.get('input_temperature', type=float),
                    'output_temperature': request.form.get('output_temperature', type=float),
                    'heat_recovered_kwh': request.form.get('heat_recovered_kwh', type=float),
                    'thermal_efficiency_percentage': request.form.get('thermal_efficiency_percentage', type=float),
                    'energy_savings_kwh': request.form.get('energy_savings_kwh', type=float),
                    'cost_savings': request.form.get('cost_savings', type=float),
                    'equipment_status': request.form.get('equipment_status'),
                    'recorded_by': session.get('user_id')
                }
                
                # Remove empty values
                data = {k: v for k, v in data.items() if v is not None and v != ''}
                
                record = db.insert_record('heat_recovery', data)
                
                if record:
                    flash('Heat recovery data recorded successfully', 'success')
                else:
                    flash('Failed to record heat recovery data', 'error')
                    
        except Exception as e:
            logger.error(f"Energy recording error: {e}")
            flash('Error recording energy data', 'error')
    
    # Get summary data
    today = date.today()
    month_start = today.replace(day=1)
    
    energy_summary = db.execute_single("""
        SELECT 
            SUM(consumption_kwh) as total_consumption,
            AVG(efficiency_percentage) as avg_efficiency,
            SUM(cost_amount) as total_cost
        FROM energy_consumption 
        WHERE recorded_date >= ?
    """, (month_start,)) or {}
    
    heat_recovery_summary = db.execute_single("""
        SELECT 
            SUM(heat_recovered_kwh) as total_heat_recovered,
            AVG(thermal_efficiency_percentage) as avg_thermal_efficiency,
            SUM(energy_savings_kwh) as total_energy_savings
        FROM heat_recovery 
        WHERE recorded_date >= ?
    """, (month_start,)) or {}
    
    consumption_records = db.execute_query("""
        SELECT ec.*, u.full_name as recorded_by_name
        FROM energy_consumption ec
        LEFT JOIN users u ON ec.recorded_by = u.id
        ORDER BY ec.recorded_date DESC, ec.recorded_time DESC
        LIMIT 50
    """)
    
    return render_template('energy.html', 
                         energy_summary=energy_summary,
                         heat_recovery_summary=heat_recovery_summary,
                         consumption_records=consumption_records)

@app.route('/waste', methods=['GET', 'POST'])
def waste():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            data = {
                'waste_type': request.form.get('waste_type'),
                'quantity_kg': request.form.get('quantity_kg', type=float),
                'source_department': request.form.get('source_department'),
                'disposal_method': request.form.get('disposal_method'),
                'recycling_percentage': request.form.get('recycling_percentage', type=float),
                'valorization_amount': request.form.get('valorization_amount', type=float),
                'cost_amount': request.form.get('cost_amount', type=float),
                'destination': request.form.get('destination'),
                'certificate_number': request.form.get('certificate_number'),
                'notes': request.form.get('notes'),
                'responsible_person_id': session.get('user_id')
            }
            
            # Remove empty values
            data = {k: v for k, v in data.items() if v is not None and v != ''}
            
            record = db.insert_record('waste_records', data)
            
            if record:
                flash('Waste data recorded successfully', 'success')
            else:
                flash('Failed to record waste data', 'error')
                
        except Exception as e:
            logger.error(f"Waste recording error: {e}")
            flash('Error recording waste data', 'error')
    
    # Get summary data
    today = date.today()
    month_start = today.replace(day=1)
    
    waste_summary = db.execute_single("""
        SELECT 
            SUM(quantity_kg) as total_waste,
            AVG(recycling_percentage) as avg_recycling_rate,
            SUM(valorization_amount) as total_valorization,
            SUM(cost_amount) as total_cost
        FROM waste_records 
        WHERE recorded_date >= ?
    """, (month_start,)) or {}
    
    waste_breakdown = db.execute_query("""
        SELECT 
            waste_type,
            SUM(quantity_kg) as total_quantity,
            (SUM(quantity_kg) * 100.0 / (SELECT SUM(quantity_kg) FROM waste_records WHERE recorded_date >= ?)) as percentage
        FROM waste_records 
        WHERE recorded_date >= ?
        GROUP BY waste_type
        ORDER BY total_quantity DESC
    """, (month_start, month_start))
    
    waste_records = db.execute_query("""
        SELECT wr.*, u.full_name as responsible_person_name
        FROM waste_records wr
        LEFT JOIN users u ON wr.responsible_person_id = u.id
        ORDER BY wr.recorded_date DESC
        LIMIT 50
    """)
    
    return render_template('waste.html', 
                         waste_summary=waste_summary,
                         waste_breakdown=waste_breakdown,
                         waste_records=waste_records)

@app.route('/users', methods=['GET', 'POST'])
def users():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            data = {
                'username': request.form.get('username'),
                'email': request.form.get('email'),
                'full_name': request.form.get('full_name'),
                'password_hash': db.hash_password(request.form.get('password')),
                'role': request.form.get('role'),
                'department': request.form.get('department'),
                'is_active': request.form.get('is_active', type=int)
            }
            
            # Check if user already exists
            existing_user = db.execute_single(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (data['username'], data['email'])
            )
            
            if existing_user:
                flash('User with this username or email already exists', 'error')
            else:
                user = db.insert_record('users', data)
                
                if user:
                    flash('User created successfully', 'success')
                else:
                    flash('Failed to create user', 'error')
                    
        except Exception as e:
            logger.error(f"User creation error: {e}")
            flash('Error creating user', 'error')
    
    users_list = db.execute_query("""
        SELECT id, username, email, full_name, role, department, is_active, created_at, last_login
        FROM users ORDER BY created_at DESC
    """)
    
    return render_template('users.html', users=users_list)

# ============================================================================
# API ROUTES (for external access)
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = db.execute_single("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
        
        if user and db.verify_password(password, user['password_hash']):
            # Update last login
            db.execute_single("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), user['id']))
            
            # Remove password from response
            user_response = {k: v for k, v in user.items() if k != 'password_hash'}
            
            return jsonify({
                'message': 'Login successful',
                'user': user_response
            })
        
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"API login failed: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        
        required_fields = ['username', 'email', 'password', 'full_name', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        existing_user = db.execute_single(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (data['username'], data['email'])
        )
        
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400
        
        # Hash password and create user
        user_data = data.copy()
        user_data['password_hash'] = db.hash_password(user_data.pop('password'))
        user_data['is_active'] = 1
        
        user = db.insert_record('users', user_data)
        
        if user:
            user_response = {k: v for k, v in user.items() if k != 'password_hash'}
            return jsonify({
                'message': 'User created successfully',
                'user': user_response
            }), 201
        
        return jsonify({'error': 'User creation failed'}), 500
    except Exception as e:
        logger.error(f"API registration failed: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/users', methods=['GET'])
def api_get_users():
    try:
        users_list = db.execute_query("""
            SELECT id, username, email, full_name, role, department, is_active, created_at, last_login
            FROM users ORDER BY created_at DESC
        """)
        return jsonify(users_list)
    except Exception as e:
        logger.error(f"API get users failed: {e}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@app.route('/api/dashboard/kpis', methods=['GET'])
def get_dashboard_kpis():
    try:
        today = date.today()
        month_start = today.replace(day=1)
        
        # Production KPIs
        production_stats = db.execute_single("""
            SELECT 
                COUNT(*) as total_batches,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_batches,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_batches,
                SUM(actual_quantity) as total_production
            FROM production_batches 
            WHERE production_date >= ?
        """, (month_start,))
        
        # Quality KPIs
        quality_stats = db.execute_single("""
            SELECT 
                COUNT(*) as total_tests,
                SUM(CASE WHEN pass_fail = 'PASS' THEN 1 ELSE 0 END) as passed_tests,
                AVG(CASE WHEN iso_compliant = 1 THEN 1.0 ELSE 0.0 END) * 100 as compliance_rate
            FROM quality_tests 
            WHERE test_date >= ?
        """, (month_start,))
        
        # Energy KPIs
        energy_stats = db.execute_single("""
            SELECT 
                SUM(consumption_kwh) as total_consumption,
                AVG(efficiency_percentage) as avg_efficiency,
                SUM(cost_amount) as total_cost
            FROM energy_consumption 
            WHERE recorded_date >= ?
        """, (month_start,))
        
        # Waste KPIs
        waste_stats = db.execute_single("""
            SELECT 
                SUM(quantity_kg) as total_waste,
                AVG(recycling_percentage) as avg_recycling_rate,
                SUM(valorization_amount) as total_valorization
            FROM waste_records 
            WHERE recorded_date >= ?
        """, (month_start,))
        
        return jsonify({
            'production': production_stats or {},
            'quality': quality_stats or {},
            'energy': energy_stats or {},
            'waste': waste_stats or {},
            'period': f"{month_start} to {today}"
        })
    except Exception as e:
        logger.error(f"Dashboard KPIs failed: {e}")
        return jsonify({'error': 'Failed to retrieve KPIs'}), 500

@app.route('/api/dashboard/alerts', methods=['GET'])
def get_active_alerts():
    try:
        alerts = db.execute_query("""
            SELECT a.*, u.full_name as assigned_to_name
            FROM alerts a
            LEFT JOIN users u ON a.assigned_to = u.id
            WHERE a.is_resolved = 0
            ORDER BY 
                CASE a.priority 
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END,
                a.created_at DESC
        """)
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Get alerts failed: {e}")
        return jsonify({'error': 'Failed to retrieve alerts'}), 500

# ============================================================================
# PRODUCTION ROUTES
# ============================================================================

@app.route('/api/production/batches', methods=['GET'])
def get_production_batches():
    try:
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = """
            SELECT pb.*, u.full_name as supervisor_name
            FROM production_batches pb
            LEFT JOIN users u ON pb.supervisor_id = u.id
        """
        conditions = []
        params = []
        
        if status:
            conditions.append("pb.status = ?")
            params.append(status)
        if date_from:
            conditions.append("pb.production_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("pb.production_date <= ?")
            params.append(date_to)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY pb.production_date DESC"
        
        batches = db.execute_query(query, tuple(params))
        return jsonify(batches)
    except Exception as e:
        logger.error(f"Get production batches failed: {e}")
        return jsonify({'error': 'Failed to retrieve production batches'}), 500

@app.route('/api/production/batches', methods=['POST'])
def create_production_batch():
    try:
        data = request.get_json()
        
        required_fields = ['batch_number', 'product_type', 'production_date', 'planned_quantity']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        batch = db.insert_record('production_batches', data)
        
        if not batch:
            return jsonify({'error': 'Batch creation failed'}), 500
        
        return jsonify({
            'message': 'Production batch created successfully',
            'batch': batch
        }), 201
    except Exception as e:
        logger.error(f"Create production batch failed: {e}")
        return jsonify({'error': 'Failed to create production batch'}), 500

# ============================================================================
# QUALITY CONTROL ROUTES
# ============================================================================

@app.route('/api/quality/tests', methods=['GET'])
def get_quality_tests():
    try:
        batch_id = request.args.get('batch_id', type=int)
        status = request.args.get('status')
        
        query = """
            SELECT qt.*, pb.batch_number, pb.product_type, u.full_name as technician_name
            FROM quality_tests qt
            LEFT JOIN production_batches pb ON qt.batch_id = pb.id
            LEFT JOIN users u ON qt.technician_id = u.id
        """
        conditions = []
        params = []
        
        if batch_id:
            conditions.append("qt.batch_id = ?")
            params.append(batch_id)
        if status:
            conditions.append("qt.status = ?")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY qt.test_date DESC"
        
        tests = db.execute_query(query, tuple(params))
        return jsonify(tests)
    except Exception as e:
        logger.error(f"Get quality tests failed: {e}")
        return jsonify({'error': 'Failed to retrieve quality tests'}), 500

@app.route('/api/quality/tests', methods=['POST'])
def create_quality_test():
    try:
        data = request.get_json()
        
        required_fields = ['batch_id', 'test_type']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check ISO compliance
        iso_compliance = check_iso_compliance(data)
        data['iso_compliant'] = iso_compliance
        data['pass_fail'] = 'PASS' if iso_compliance else 'FAIL'
        
        test = db.insert_record('quality_tests', data)
        
        if not test:
            return jsonify({'error': 'Quality test creation failed'}), 500
        
        return jsonify({
            'message': 'Quality test created successfully',
            'test': test
        }), 201
    except Exception as e:
        logger.error(f"Create quality test failed: {e}")
        return jsonify({'error': 'Failed to create quality test'}), 500

def check_iso_compliance(test_data):
    """Check if test results comply with ISO standards"""
    try:
        standards = db.execute_query("SELECT * FROM iso_standards WHERE is_active = 1")
        
        for standard in standards:
            param_name = standard['parameter_name'].lower()
            
            # Check various parameters
            if 'warping' in param_name and test_data.get('warping_percentage'):
                if standard['max_value'] and test_data['warping_percentage'] > standard['max_value']:
                    return False
            
            if 'water_absorption' in param_name and test_data.get('water_absorption_percentage'):
                if standard['max_value'] and test_data['water_absorption_percentage'] > standard['max_value']:
                    return False
            
            if 'breaking_strength' in param_name and test_data.get('breaking_strength_n'):
                if standard['min_value'] and test_data['breaking_strength_n'] < standard['min_value']:
                    return False
        
        return True
    except Exception as e:
        logger.error(f"ISO compliance check error: {e}")
        return False

@app.route('/api/quality/iso-standards', methods=['GET'])
def get_iso_standards():
    try:
        standards = db.execute_query("""
            SELECT * FROM iso_standards 
            WHERE is_active = 1 
            ORDER BY standard_code, parameter_name
        """)
        return jsonify(standards)
    except Exception as e:
        logger.error(f"Get ISO standards failed: {e}")
        return jsonify({'error': 'Failed to retrieve ISO standards'}), 500

# ============================================================================
# ENERGY MONITORING ROUTES
# ============================================================================

@app.route('/api/energy/consumption', methods=['GET'])
def get_energy_consumption():
    try:
        source = request.args.get('source')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = """
            SELECT ec.*, u.full_name as recorded_by_name
            FROM energy_consumption ec
            LEFT JOIN users u ON ec.recorded_by = u.id
        """
        conditions = []
        params = []
        
        if source:
            conditions.append("ec.source = ?")
            params.append(source)
        if date_from:
            conditions.append("ec.recorded_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("ec.recorded_date <= ?")
            params.append(date_to)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY ec.recorded_date DESC"
        
        consumption = db.execute_query(query, tuple(params))
        return jsonify(consumption)
    except Exception as e:
        logger.error(f"Get energy consumption failed: {e}")
        return jsonify({'error': 'Failed to retrieve energy consumption'}), 500

@app.route('/api/energy/consumption', methods=['POST'])
def record_energy_consumption():
    try:
        data = request.get_json()
        
        required_fields = ['source', 'consumption_kwh']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Calculate efficiency if target is provided
        if data.get('target_consumption'):
            actual = data['consumption_kwh']
            target = data['target_consumption']
            efficiency = (target / actual) * 100 if actual > 0 else 0
            data['efficiency_percentage'] = round(efficiency, 2)
        
        record = db.insert_record('energy_consumption', data)
        
        if not record:
            return jsonify({'error': 'Energy consumption recording failed'}), 500
        
        return jsonify({
            'message': 'Energy consumption recorded successfully',
            'record': record
        }), 201
    except Exception as e:
        logger.error(f"Record energy consumption failed: {e}")
        return jsonify({'error': 'Failed to record energy consumption'}), 500

# ============================================================================
# WASTE MANAGEMENT ROUTES
# ============================================================================

@app.route('/api/waste/records', methods=['GET'])
def get_waste_records():
    try:
        waste_type = request.args.get('waste_type')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = """
            SELECT wr.*, u.full_name as responsible_person_name
            FROM waste_records wr
            LEFT JOIN users u ON wr.responsible_person_id = u.id
        """
        conditions = []
        params = []
        
        if waste_type:
            conditions.append("wr.waste_type = ?")
            params.append(waste_type)
        if date_from:
            conditions.append("wr.recorded_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("wr.recorded_date <= ?")
            params.append(date_to)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY wr.recorded_date DESC"
        
        records = db.execute_query(query, tuple(params))
        return jsonify(records)
    except Exception as e:
        logger.error(f"Get waste records failed: {e}")
        return jsonify({'error': 'Failed to retrieve waste records'}), 500

@app.route('/api/waste/records', methods=['POST'])
def record_waste():
    try:
        data = request.get_json()
        
        required_fields = ['waste_type', 'quantity_kg']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        record = db.insert_record('waste_records', data)
        
        if not record:
            return jsonify({'error': 'Waste recording failed'}), 500
        
        return jsonify({
            'message': 'Waste data recorded successfully',
            'record': record
        }), 201
    except Exception as e:
        logger.error(f"Record waste failed: {e}")
        return jsonify({'error': 'Failed to record waste data'}), 500

# ============================================================================
# RAW MATERIAL MANAGEMENT ROUTES
# ============================================================================

@app.route('/raw-materials', methods=['GET', 'POST'])
def raw_materials():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            form_type = request.form.get('form_type')
            
            if form_type == 'supplier':
                supplier_data = {
                    'supplier_code': request.form.get('supplier_code'),
                    'supplier_name': request.form.get('supplier_name'),
                    'contact_person': request.form.get('contact_person'),
                    'phone': request.form.get('phone'),
                    'email': request.form.get('email'),
                    'address': request.form.get('address'),
                    'region': request.form.get('region'),
                    'certification_status': request.form.get('certification_status', 'pending'),
                    'quality_rating': request.form.get('quality_rating', type=float) or 5.0
                }
                
                # Remove empty values
                supplier_data = {k: v for k, v in supplier_data.items() if v is not None and v != ''}
                
                supplier = db.insert_record('suppliers', supplier_data)
                if supplier:
                    flash('Fournisseur ajouté avec succès', 'success')
                else:
                    flash('Erreur lors de l\'ajout du fournisseur', 'error')
            
            elif form_type == 'material':
                material_data = {
                    'material_code': request.form.get('material_code'),
                    'material_name': request.form.get('material_name'),
                    'material_type': request.form.get('material_type'),
                    'supplier_id': request.form.get('supplier_id', type=int),
                    'lot_number': request.form.get('lot_number'),
                    'quantity_kg': request.form.get('quantity_kg', type=float),
                    'unit_cost': request.form.get('unit_cost', type=float),
                    'humidity_percentage': request.form.get('humidity_percentage', type=float),
                    'particle_size_microns': request.form.get('particle_size_microns', type=float),
                    'chemical_composition': request.form.get('chemical_composition'),
                    'storage_location': request.form.get('storage_location'),
                    'expiry_date': request.form.get('expiry_date'),
                    'inspection_notes': request.form.get('inspection_notes'),
                    'status': 'en_attente',  # Default status
                    'inspected_by': session.get('user_id')
                }
                
                # Remove empty values
                material_data = {k: v for k, v in material_data.items() if v is not None and v != ''}
                
                material = db.insert_record('raw_materials', material_data)
                if material:
                    flash('Matière première enregistrée avec succès', 'success')
                else:
                    flash('Erreur lors de l\'enregistrement de la matière première', 'error')
                    
        except Exception as e:
            logger.error(f"Raw material form error: {e}")
            flash('Erreur lors du traitement du formulaire', 'error')
    
    # Get data for page
    try:
        suppliers = db.execute_query("SELECT * FROM suppliers WHERE is_active = 1 ORDER BY supplier_name")
        materials = db.execute_query("""
            SELECT rm.*, s.supplier_name, u.full_name as inspected_by_name
            FROM raw_materials rm
            LEFT JOIN suppliers s ON rm.supplier_id = s.id
            LEFT JOIN users u ON rm.inspected_by = u.id
            ORDER BY rm.reception_date DESC
        """)
        
        # Get material type counts
        material_stats = db.execute_query("""
            SELECT 
                material_type,
                COUNT(*) as count,
                SUM(quantity_kg) as total_quantity,
                AVG(unit_cost) as avg_cost
            FROM raw_materials 
            GROUP BY material_type
        """)
        
    except Exception as e:
        logger.error(f"Raw materials page error: {e}")
        suppliers = []
        materials = []
        material_stats = []
    
    return render_template('raw_materials.html', 
                         suppliers=suppliers, 
                         materials=materials,
                         material_stats=material_stats)

@app.route('/powder-preparation', methods=['GET', 'POST'])
def powder_preparation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            silo_data = {
                'silo_code': request.form.get('silo_code'),
                'silo_name': request.form.get('silo_name'),
                'capacity_kg': request.form.get('capacity_kg', type=float),
                'current_level_kg': request.form.get('current_level_kg', type=float),
                'material_type': request.form.get('material_type'),
                'humidity_sensor_id': request.form.get('humidity_sensor_id'),
                'target_humidity_min': request.form.get('target_humidity_min', type=float),
                'target_humidity_max': request.form.get('target_humidity_max', type=float),
                'current_humidity': request.form.get('current_humidity', type=float),
                'location': request.form.get('location'),
                'status': request.form.get('status', 'active')
            }
            
            # Remove empty values
            silo_data = {k: v for k, v in silo_data.items() if v is not None and v != ''}
            
            silo = db.insert_record('silos', silo_data)
            if silo:
                flash('Silo ajouté avec succès', 'success')
            else:
                flash('Erreur lors de l\'ajout du silo', 'error')
                
        except Exception as e:
            logger.error(f"Silo form error: {e}")
            flash('Erreur lors du traitement du formulaire', 'error')
    
    # Get silos data
    try:
        silos = db.execute_query("SELECT * FROM silos ORDER BY silo_code")
        
        # Calculate summary stats
        silo_stats = {
            'total_silos': len(silos),
            'total_capacity': sum(s['capacity_kg'] for s in silos if s['capacity_kg']),
            'total_content': sum(s['current_level_kg'] for s in silos if s['current_level_kg']),
            'avg_humidity': sum(s['current_humidity'] for s in silos if s['current_humidity']) / len(silos) if silos else 0
        }
        
        # Check humidity alerts
        humidity_alerts = []
        for silo in silos:
            if silo['current_humidity'] and silo['target_humidity_min'] and silo['target_humidity_max']:
                if silo['current_humidity'] < silo['target_humidity_min']:
                    humidity_alerts.append(f"Silo {silo['silo_code']}: Humidité trop faible ({silo['current_humidity']}%)")
                elif silo['current_humidity'] > silo['target_humidity_max']:
                    humidity_alerts.append(f"Silo {silo['silo_code']}: Humidité trop élevée ({silo['current_humidity']}%)")
        
    except Exception as e:
        logger.error(f"Powder preparation page error: {e}")
        silos = []
        silo_stats = {}
        humidity_alerts = []
    
    return render_template('powder_preparation.html', 
                         silos=silos,
                         silo_stats=silo_stats,
                         humidity_alerts=humidity_alerts)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = 5000
    host = '0.0.0.0'
    
    logger.info(f"Dersa EcoQuality (Local) serving on port {port}")
    app.run(host=host, port=port, debug=True)