"""
Dersa EcoQuality - Flask Application
Comprehensive quality management system for ceramic tile manufacturing
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import logging
from datetime import datetime, date, timedelta
from models import DatabaseManager
from services import AuthService, ProductionService, QualityService, EnergyService, WasteService, DashboardService
import json
from io import BytesIO
import csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize services
try:
    db = DatabaseManager()
    auth_service = AuthService(db)
    production_service = ProductionService(db)
    quality_service = QualityService(db)
    energy_service = EnergyService(db)
    waste_service = WasteService(db)
    dashboard_service = DashboardService(db)
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Service initialization failed: {e}")

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

# Root route
@app.route('/')
def home():
    return jsonify({
        'application': 'Dersa EcoQuality',
        'description': 'Quality management system for ceramic tile manufacturing',
        'version': '1.0.0',
        'company': 'Ceramica Dersa - Tétouan, Morocco',
        'status': 'running',
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
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = auth_service.authenticate_user(username, password)
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        return jsonify({
            'message': 'Login successful',
            'user': user
        })
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        required_fields = ['username', 'email', 'password', 'full_name', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        existing_user = db.execute_single(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (data['username'], data['email'])
        )
        
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400
        
        user = auth_service.create_user(data)
        
        if not user:
            return jsonify({'error': 'User creation failed'}), 500
        
        return jsonify({
            'message': 'User created successfully',
            'user': user
        }), 201
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/users', methods=['GET'])
def get_users():
    try:
        users = db.execute_query("""
            SELECT id, username, email, full_name, role, department, is_active, created_at, last_login
            FROM users ORDER BY created_at DESC
        """)
        return jsonify(users)
    except Exception as e:
        logger.error(f"Get users failed: {e}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@app.route('/api/dashboard/kpis', methods=['GET'])
def get_dashboard_kpis():
    try:
        kpis = dashboard_service.get_kpi_summary()
        return jsonify(kpis)
    except Exception as e:
        logger.error(f"Dashboard KPIs failed: {e}")
        return jsonify({'error': 'Failed to retrieve KPIs'}), 500

@app.route('/api/dashboard/trends/<metric>', methods=['GET'])
def get_trend_data(metric):
    try:
        days = request.args.get('days', 30, type=int)
        trends = dashboard_service.get_trend_data(metric, days)
        return jsonify(trends)
    except Exception as e:
        logger.error(f"Trend data failed: {e}")
        return jsonify({'error': 'Failed to retrieve trend data'}), 500

@app.route('/api/dashboard/alerts', methods=['GET'])
def get_active_alerts():
    try:
        alerts = db.execute_query("""
            SELECT a.*, u.full_name as assigned_to_name
            FROM alerts a
            LEFT JOIN users u ON a.assigned_to = u.id
            WHERE a.is_resolved = false
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
        filters = {
            'status': request.args.get('status'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to')
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        batches = production_service.get_production_batches(filters)
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
        
        batch = production_service.create_production_batch(data)
        
        if not batch:
            return jsonify({'error': 'Batch creation failed'}), 500
        
        return jsonify({
            'message': 'Production batch created successfully',
            'batch': batch
        }), 201
    except Exception as e:
        logger.error(f"Create production batch failed: {e}")
        return jsonify({'error': 'Failed to create production batch'}), 500

@app.route('/api/production/batches/<int:batch_id>/status', methods=['PUT'])
def update_batch_status(batch_id):
    try:
        data = request.get_json()
        status = data.get('status')
        notes = data.get('notes')
        
        if not status:
            return jsonify({'error': 'Status is required'}), 400
        
        success = production_service.update_batch_status(batch_id, status, notes)
        
        if not success:
            return jsonify({'error': 'Status update failed'}), 500
        
        return jsonify({'message': 'Status updated successfully'})
    except Exception as e:
        logger.error(f"Update batch status failed: {e}")
        return jsonify({'error': 'Failed to update batch status'}), 500

# ============================================================================
# QUALITY CONTROL ROUTES
# ============================================================================

@app.route('/api/quality/tests', methods=['GET'])
def get_quality_tests():
    try:
        filters = {
            'batch_id': request.args.get('batch_id', type=int),
            'status': request.args.get('status'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to')
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        tests = quality_service.get_quality_tests(filters)
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
        
        test = quality_service.create_quality_test(data)
        
        if not test:
            return jsonify({'error': 'Quality test creation failed'}), 500
        
        return jsonify({
            'message': 'Quality test created successfully',
            'test': test
        }), 201
    except Exception as e:
        logger.error(f"Create quality test failed: {e}")
        return jsonify({'error': 'Failed to create quality test'}), 500

@app.route('/api/quality/iso-standards', methods=['GET'])
def get_iso_standards():
    try:
        standards = db.execute_query("""
            SELECT * FROM iso_standards 
            WHERE is_active = true 
            ORDER BY standard_code, parameter_name
        """)
        return jsonify(standards)
    except Exception as e:
        logger.error(f"Get ISO standards failed: {e}")
        return jsonify({'error': 'Failed to retrieve ISO standards'}), 500

@app.route('/api/quality/defect-analysis', methods=['GET'])
def get_defect_analysis():
    try:
        period_days = request.args.get('days', 30, type=int)
        start_date = date.today() - timedelta(days=period_days)
        
        analysis = db.execute_query("""
            SELECT 
                defect_type,
                COUNT(*) as count,
                AVG(defect_count) as avg_count_per_test,
                SUM(defect_count) as total_defects
            FROM quality_tests 
            WHERE test_date >= %s AND defect_type != 'none'
            GROUP BY defect_type
            ORDER BY count DESC
        """, (start_date,))
        
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Defect analysis failed: {e}")
        return jsonify({'error': 'Failed to retrieve defect analysis'}), 500

# ============================================================================
# ENERGY MONITORING ROUTES
# ============================================================================

@app.route('/api/energy/consumption', methods=['GET'])
def get_energy_consumption():
    try:
        filters = {
            'source': request.args.get('source'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'department': request.args.get('department')
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        consumption = energy_service.get_energy_consumption(filters)
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
        
        record = energy_service.record_energy_consumption(data)
        
        if not record:
            return jsonify({'error': 'Energy consumption recording failed'}), 500
        
        return jsonify({
            'message': 'Energy consumption recorded successfully',
            'record': record
        }), 201
    except Exception as e:
        logger.error(f"Record energy consumption failed: {e}")
        return jsonify({'error': 'Failed to record energy consumption'}), 500

@app.route('/api/energy/heat-recovery', methods=['GET'])
def get_heat_recovery():
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = """
            SELECT hr.*, u.full_name as recorded_by_name
            FROM heat_recovery hr
            LEFT JOIN users u ON hr.recorded_by = u.id
        """
        params = []
        
        conditions = []
        if date_from:
            conditions.append("hr.recorded_date >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("hr.recorded_date <= %s")
            params.append(date_to)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY hr.recorded_date DESC"
        
        recovery_data = db.execute_query(query, tuple(params))
        return jsonify(recovery_data)
    except Exception as e:
        logger.error(f"Get heat recovery failed: {e}")
        return jsonify({'error': 'Failed to retrieve heat recovery data'}), 500

@app.route('/api/energy/heat-recovery', methods=['POST'])
def record_heat_recovery():
    try:
        data = request.get_json()
        
        required_fields = ['kiln_id', 'input_temperature', 'output_temperature']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        record = energy_service.record_heat_recovery(data)
        
        if not record:
            return jsonify({'error': 'Heat recovery recording failed'}), 500
        
        return jsonify({
            'message': 'Heat recovery data recorded successfully',
            'record': record
        }), 201
    except Exception as e:
        logger.error(f"Record heat recovery failed: {e}")
        return jsonify({'error': 'Failed to record heat recovery data'}), 500

# ============================================================================
# WASTE MANAGEMENT ROUTES
# ============================================================================

@app.route('/api/waste/records', methods=['GET'])
def get_waste_records():
    try:
        filters = {
            'waste_type': request.args.get('waste_type'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to')
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        records = waste_service.get_waste_records(filters)
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
        
        record = waste_service.record_waste(data)
        
        if not record:
            return jsonify({'error': 'Waste recording failed'}), 500
        
        return jsonify({
            'message': 'Waste data recorded successfully',
            'record': record
        }), 201
    except Exception as e:
        logger.error(f"Record waste failed: {e}")
        return jsonify({'error': 'Failed to record waste data'}), 500

@app.route('/api/waste/summary', methods=['GET'])
def get_waste_summary():
    try:
        period_days = request.args.get('days', 30, type=int)
        start_date = date.today() - timedelta(days=period_days)
        
        summary = db.execute_query("""
            SELECT 
                waste_type,
                SUM(quantity_kg) as total_quantity,
                AVG(recycling_percentage) as avg_recycling_rate,
                SUM(valorization_amount) as total_valorization,
                COUNT(*) as record_count
            FROM waste_records 
            WHERE recorded_date >= %s
            GROUP BY waste_type
            ORDER BY total_quantity DESC
        """, (start_date,))
        
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Waste summary failed: {e}")
        return jsonify({'error': 'Failed to retrieve waste summary'}), 500

# ============================================================================
# COMPLIANCE & DOCUMENTS ROUTES
# ============================================================================

@app.route('/api/compliance/documents', methods=['GET'])
def get_compliance_documents():
    try:
        doc_type = request.args.get('type')
        status = request.args.get('status')
        
        query = """
            SELECT cd.*, u.full_name as uploaded_by_name
            FROM compliance_documents cd
            LEFT JOIN users u ON cd.uploaded_by = u.id
        """
        params = []
        conditions = []
        
        if doc_type:
            conditions.append("cd.document_type = %s")
            params.append(doc_type)
        
        if status:
            conditions.append("cd.status = %s")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY cd.created_at DESC"
        
        documents = db.execute_query(query, tuple(params))
        return jsonify(documents)
    except Exception as e:
        logger.error(f"Get compliance documents failed: {e}")
        return jsonify({'error': 'Failed to retrieve compliance documents'}), 500

@app.route('/api/compliance/documents', methods=['POST'])
def create_compliance_document():
    try:
        data = request.get_json()
        
        required_fields = ['document_name', 'document_type']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        document = db.insert_record('compliance_documents', data)
        
        if not document:
            return jsonify({'error': 'Document creation failed'}), 500
        
        return jsonify({
            'message': 'Compliance document created successfully',
            'document': document
        }), 201
    except Exception as e:
        logger.error(f"Create compliance document failed: {e}")
        return jsonify({'error': 'Failed to create compliance document'}), 500

# ============================================================================
# TESTING CAMPAIGNS ROUTES
# ============================================================================

@app.route('/api/campaigns', methods=['GET'])
def get_testing_campaigns():
    try:
        status = request.args.get('status')
        
        query = """
            SELECT tc.*, u.full_name as created_by_name
            FROM testing_campaigns tc
            LEFT JOIN users u ON tc.created_by = u.id
        """
        params = []
        
        if status:
            query += " WHERE tc.status = %s"
            params.append(status)
        
        query += " ORDER BY tc.created_at DESC"
        
        campaigns = db.execute_query(query, tuple(params))
        return jsonify(campaigns)
    except Exception as e:
        logger.error(f"Get testing campaigns failed: {e}")
        return jsonify({'error': 'Failed to retrieve testing campaigns'}), 500

@app.route('/api/campaigns', methods=['POST'])
def create_testing_campaign():
    try:
        data = request.get_json()
        
        required_fields = ['campaign_name', 'start_date']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        campaign = db.insert_record('testing_campaigns', data)
        
        if not campaign:
            return jsonify({'error': 'Campaign creation failed'}), 500
        
        return jsonify({
            'message': 'Testing campaign created successfully',
            'campaign': campaign
        }), 201
    except Exception as e:
        logger.error(f"Create testing campaign failed: {e}")
        return jsonify({'error': 'Failed to create testing campaign'}), 500

# ============================================================================
# REPORTING ROUTES
# ============================================================================

@app.route('/api/reports/quality/<int:batch_id>', methods=['GET'])
def generate_quality_report(batch_id):
    try:
        # Get batch info
        batch = db.execute_single("""
            SELECT pb.*, u.full_name as supervisor_name
            FROM production_batches pb
            LEFT JOIN users u ON pb.supervisor_id = u.id
            WHERE pb.id = %s
        """, (batch_id,))
        
        if not batch:
            return jsonify({'error': 'Batch not found'}), 404
        
        # Get quality tests for batch
        tests = db.execute_query("""
            SELECT qt.*, u.full_name as technician_name
            FROM quality_tests qt
            LEFT JOIN users u ON qt.technician_id = u.id
            WHERE qt.batch_id = %s
            ORDER BY qt.test_date, qt.created_at
        """, (batch_id,))
        
        report = {
            'batch': batch,
            'tests': tests,
            'summary': {
                'total_tests': len(tests),
                'passed_tests': len([t for t in tests if t['pass_fail'] == 'PASS']),
                'failed_tests': len([t for t in tests if t['pass_fail'] == 'FAIL']),
                'iso_compliant': all(t['iso_compliant'] for t in tests if t['iso_compliant'] is not None)
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify(report)
    except Exception as e:
        logger.error(f"Generate quality report failed: {e}")
        return jsonify({'error': 'Failed to generate quality report'}), 500

@app.route('/api/reports/export/<report_type>', methods=['GET'])
def export_report(report_type):
    try:
        date_from = request.args.get('date_from', (date.today() - timedelta(days=30)).isoformat())
        date_to = request.args.get('date_to', date.today().isoformat())
        format_type = request.args.get('format', 'json')  # json, csv
        
        if report_type == 'quality':
            data = db.execute_query("""
                SELECT qt.*, pb.batch_number, pb.product_type, u.full_name as technician_name
                FROM quality_tests qt
                LEFT JOIN production_batches pb ON qt.batch_id = pb.id
                LEFT JOIN users u ON qt.technician_id = u.id
                WHERE qt.test_date BETWEEN %s AND %s
                ORDER BY qt.test_date DESC
            """, (date_from, date_to))
        
        elif report_type == 'energy':
            data = db.execute_query("""
                SELECT * FROM energy_consumption
                WHERE recorded_date BETWEEN %s AND %s
                ORDER BY recorded_date DESC
            """, (date_from, date_to))
        
        elif report_type == 'waste':
            data = db.execute_query("""
                SELECT * FROM waste_records
                WHERE recorded_date BETWEEN %s AND %s
                ORDER BY recorded_date DESC
            """, (date_from, date_to))
        
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        if format_type == 'csv':
            # Generate CSV
            if not data:
                return jsonify({'error': 'No data found'}), 404
            
            output = BytesIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys(), extrasaction='ignore')
            writer.writeheader()
            
            for row in data:
                # Convert datetime objects to strings
                csv_row = {}
                for key, value in row.items():
                    if isinstance(value, (datetime, date)):
                        csv_row[key] = value.isoformat()
                    else:
                        csv_row[key] = value
                writer.writerow(csv_row)
            
            output.seek(0)
            return send_file(
                BytesIO(output.getvalue()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{report_type}_report_{date_from}_to_{date_to}.csv'
            )
        
        else:
            return jsonify({
                'report_type': report_type,
                'date_range': f"{date_from} to {date_to}",
                'total_records': len(data),
                'data': data
            })
    
    except Exception as e:
        logger.error(f"Export report failed: {e}")
        return jsonify({'error': 'Failed to export report'}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    # ALWAYS serve the app on port 5000
    # this serves the API.
    # It is the only port that is not firewalled.
    port = 5000
    host = '0.0.0.0'
    
    logger.info(f"Dersa EcoQuality serving on port {port}")
    app.run(host=host, port=port, debug=os.getenv('FLASK_ENV') == 'development')