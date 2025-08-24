"""
Dersa EcoQuality - Authentication Routes
User login, logout, and session management
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from data.database import DatabaseManager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

db = DatabaseManager()

@auth_bp.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('main.dashboard'))
        
        flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))