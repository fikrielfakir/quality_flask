from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from database import DatabaseStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize database storage
storage = DatabaseStorage()

# Root route
@app.route('/')
def home():
    return jsonify({
        'message': 'Flask API Server',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/login, /api/auth/register',
            'quality_tests': '/api/quality-tests',
            'production_lots': '/api/production-lots',
            'energy_consumption': '/api/energy-consumption',
            'waste_records': '/api/waste-records',
            'compliance_documents': '/api/compliance-documents',
            'testing_campaigns': '/api/testing-campaigns'
        }
    })

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

# Authentication routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = storage.authenticate_user(email, password)
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        return jsonify({'user': user})
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('fullName')
        department = data.get('department')
        role = data.get('role', 'operator')
        
        # Check if user already exists
        existing_user = storage.get_profile_by_email(email)
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400
        
        user = storage.create_profile({
            'email': email,
            'password': password,
            'full_name': full_name,
            'department': department,
            'role': role
        })
        
        return jsonify({'user': user})
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return jsonify({'error': 'Registration failed'}), 500

# Quality tests routes
@app.route('/api/quality-tests', methods=['GET'])
def get_quality_tests():
    try:
        tests = storage.get_quality_tests()
        return jsonify(tests)
    except Exception as e:
        logger.error(f"Failed to fetch quality tests: {e}")
        return jsonify({'error': 'Failed to fetch quality tests'}), 500

@app.route('/api/quality-tests', methods=['POST'])
def create_quality_test():
    try:
        data = request.get_json()
        test = storage.create_quality_test(data)
        return jsonify(test)
    except Exception as e:
        logger.error(f"Failed to create quality test: {e}")
        return jsonify({'error': 'Failed to create quality test'}), 500

@app.route('/api/quality-tests/<test_id>', methods=['PUT'])
def update_quality_test(test_id):
    try:
        data = request.get_json()
        test = storage.update_quality_test(test_id, data)
        return jsonify(test)
    except Exception as e:
        logger.error(f"Failed to update quality test: {e}")
        return jsonify({'error': 'Failed to update quality test'}), 500

# Production lots routes
@app.route('/api/production-lots', methods=['GET'])
def get_production_lots():
    try:
        lots = storage.get_production_lots()
        return jsonify(lots)
    except Exception as e:
        logger.error(f"Failed to fetch production lots: {e}")
        return jsonify({'error': 'Failed to fetch production lots'}), 500

@app.route('/api/production-lots', methods=['POST'])
def create_production_lot():
    try:
        data = request.get_json()
        lot = storage.create_production_lot(data)
        return jsonify(lot)
    except Exception as e:
        logger.error(f"Failed to create production lot: {e}")
        return jsonify({'error': 'Failed to create production lot'}), 500

# Energy consumption routes
@app.route('/api/energy-consumption', methods=['GET'])
def get_energy_consumption():
    try:
        records = storage.get_energy_consumption()
        return jsonify(records)
    except Exception as e:
        logger.error(f"Failed to fetch energy consumption: {e}")
        return jsonify({'error': 'Failed to fetch energy consumption'}), 500

@app.route('/api/energy-consumption', methods=['POST'])
def create_energy_record():
    try:
        data = request.get_json()
        record = storage.create_energy_record(data)
        return jsonify(record)
    except Exception as e:
        logger.error(f"Failed to create energy record: {e}")
        return jsonify({'error': 'Failed to create energy record'}), 500

# Waste records routes
@app.route('/api/waste-records', methods=['GET'])
def get_waste_records():
    try:
        records = storage.get_waste_records()
        return jsonify(records)
    except Exception as e:
        logger.error(f"Failed to fetch waste records: {e}")
        return jsonify({'error': 'Failed to fetch waste records'}), 500

@app.route('/api/waste-records', methods=['POST'])
def create_waste_record():
    try:
        data = request.get_json()
        record = storage.create_waste_record(data)
        return jsonify(record)
    except Exception as e:
        logger.error(f"Failed to create waste record: {e}")
        return jsonify({'error': 'Failed to create waste record'}), 500

# Compliance documents routes
@app.route('/api/compliance-documents', methods=['GET'])
def get_compliance_documents():
    try:
        documents = storage.get_compliance_documents()
        return jsonify(documents)
    except Exception as e:
        logger.error(f"Failed to fetch compliance documents: {e}")
        return jsonify({'error': 'Failed to fetch compliance documents'}), 500

@app.route('/api/compliance-documents', methods=['POST'])
def create_compliance_document():
    try:
        data = request.get_json()
        document = storage.create_compliance_document(data)
        return jsonify(document)
    except Exception as e:
        logger.error(f"Failed to create compliance document: {e}")
        return jsonify({'error': 'Failed to create compliance document'}), 500

# Testing campaigns routes
@app.route('/api/testing-campaigns', methods=['GET'])
def get_testing_campaigns():
    try:
        campaigns = storage.get_testing_campaigns()
        return jsonify(campaigns)
    except Exception as e:
        logger.error(f"Failed to fetch testing campaigns: {e}")
        return jsonify({'error': 'Failed to fetch testing campaigns'}), 500

@app.route('/api/testing-campaigns', methods=['POST'])
def create_testing_campaign():
    try:
        data = request.get_json()
        campaign = storage.create_testing_campaign(data)
        return jsonify(campaign)
    except Exception as e:
        logger.error(f"Failed to create testing campaign: {e}")
        return jsonify({'error': 'Failed to create testing campaign'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    # ALWAYS serve the app on port 5000
    # this serves the API.
    # It is the only port that is not firewalled.
    port = 5000
    host = '0.0.0.0'
    
    logger.info(f"serving on port {port}")
    app.run(host=host, port=port, debug=os.getenv('FLASK_ENV') == 'development')