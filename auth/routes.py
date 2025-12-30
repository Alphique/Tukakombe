# auth/routes.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)
from utils.database import get_db_connection
from auth.utils import hash_password, verify_password
from auth.models import create_users_table

auth_bp = Blueprint(
    'auth',
    __name__,
    template_folder='templates'  # points to auth/templates/
)

# Ensure users table exists
create_users_table()


# =========================
# REGISTER ROUTE
# =========================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'client')  # default role is client

        if not email or not password:
            flash('All fields are required', 'error')
            return redirect(request.url)

        # Ensure role is valid
        valid_roles = ['client', 'blog_admin', 'finance_admin', 'super_admin']
        if role not in valid_roles:
            flash('Invalid role selected', 'error')
            role = 'client'

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
                (email, hash_password(password), role)
            )
            conn.commit()
        except Exception:
            flash('Email already registered', 'error')
            conn.close()
            return redirect(request.url)

        conn.close()
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# =========================
# LOGIN ROUTE
# =========================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email,)
        ).fetchone()
        conn.close()

        if not user or not verify_password(password, user['password']):
            flash('Invalid credentials', 'error')
            return redirect(request.url)

        # Store user info in session
        session['user_id'] = user['id']
        session['role'] = user['role']

        flash('Logged in successfully', 'success')

        # Redirect based on role
        if user['role'] == 'client':
            return redirect(url_for('core.home'))
        elif user['role'] in ['blog_admin', 'finance_admin', 'super_admin']:
            return redirect(url_for('core.dashboard'))  # admin dashboard route
        else:
            return redirect(url_for('core.home'))

    return render_template('login.html')


# =========================
# LOGOUT ROUTE
# =========================
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))
