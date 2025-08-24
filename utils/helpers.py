"""
Dersa EcoQuality - Helper Utilities
Common utility functions for the application
"""

import os
import logging
from datetime import datetime, date
from werkzeug.utils import secure_filename
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def allowed_file(filename: str, allowed_extensions: set = {'png', 'jpg', 'jpeg', 'gif'}) -> bool:
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, upload_folder: str = 'uploads') -> Optional[str]:
    """
    Save an uploaded file and return the relative path
    Returns None if save fails
    """
    if not file or not file.filename:
        return None
        
    try:
        filename = secure_filename(file.filename)
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join('static', upload_folder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
        new_filename = f"{timestamp}.{file_extension}"
        
        file_path = os.path.join(upload_dir, new_filename)
        file.save(file_path)
        
        # Return relative path for database storage
        return f"{upload_folder}/{new_filename}"
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return None

def format_date(date_obj) -> str:
    """Format date object for display"""
    if isinstance(date_obj, str):
        return date_obj
    elif isinstance(date_obj, (date, datetime)):
        return date_obj.strftime('%Y-%m-%d')
    return str(date_obj) if date_obj else ''

def format_datetime(datetime_obj) -> str:
    """Format datetime object for display"""
    if isinstance(datetime_obj, str):
        return datetime_obj
    elif isinstance(datetime_obj, datetime):
        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(datetime_obj, date):
        return datetime_obj.strftime('%Y-%m-%d')
    return str(datetime_obj) if datetime_obj else ''

def calculate_pass_rate(passed: int, total: int) -> float:
    """Calculate pass rate percentage"""
    if total == 0:
        return 0.0
    return (passed / total) * 100

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> list:
    """
    Validate that required fields are present and not empty
    Returns list of missing field names
    """
    missing_fields = []
    for field in required_fields:
        value = data.get(field, '')
        if not value or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)
    return missing_fields

def safe_float_convert(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float with fallback"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int_convert(value: Any, default: int = 0) -> int:
    """Safely convert value to int with fallback"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def get_status_badge_class(status: str) -> str:
    """Return CSS class for status badges"""
    status_classes = {
        'planned': 'badge-secondary',
        'in_production': 'badge-primary',
        'quality_testing': 'badge-warning',
        'approved': 'badge-success',
        'rejected': 'badge-danger',
        'shipped': 'badge-info',
        'PASS': 'badge-success',
        'FAIL': 'badge-danger',
        'pending': 'badge-warning',
        'completed': 'badge-success'
    }
    return status_classes.get(status, 'badge-secondary')

def get_priority_badge_class(priority: str) -> str:
    """Return CSS class for priority badges"""
    priority_classes = {
        'low': 'badge-success',
        'medium': 'badge-warning',
        'high': 'badge-danger',
        'critical': 'badge-dark'
    }
    return priority_classes.get(priority, 'badge-secondary')