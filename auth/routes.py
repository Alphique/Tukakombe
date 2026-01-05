# auth/routes.py
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from auth.utils import hash_password, verify_password
from auth.decorators import login_required
from utils.database import get_db_connection

# -------------------------------------------------------------------
# Blueprint
# -------------------------------------------------------------------
auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth',
    template_folder='templates'
)

# -------------------------------------------------------------------
# LOGIN (UPDATED REDIRECTS)
# -------------------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. Prevent logged-in users from accessing login again
    if session.get('user_id'):
        if session.get('role') in ('admin', 'super_admin'):
            return redirect(url_for('admin.dashboard'))
        # Updated: redirect active client sessions to their dashboard
        return redirect(url_for('finance.client_dashboard'))

    # Secure "next" redirect
    next_page = request.args.get('next')
    if next_page and not next_page.startswith('/'):
        next_page = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for('auth.login'))

        db = get_db_connection()
        user = db.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email,)
        ).fetchone()
        db.close()

        if not user or not verify_password(password, user['password']):
            flash("Invalid email or password.", "error")
            return redirect(url_for('auth.login'))

        # Secure session reset
        session.clear()
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['user_email'] = user['email'] # Useful for displaying on dashboard

        flash("Login successful.", "success")

        # 2. Priority redirect (e.g., if they were trying to access a protected link)
        if next_page:
            return redirect(next_page)

        # 3. Role-Based Dashboard Landing
        if user['role'] in ('admin', 'super_admin'):
            return redirect(url_for('admin.dashboard'))
        
        # Updated: Send regular clients to the finance dashboard
        return redirect(url_for('finance.client_dashboard'))

    return render_template('login.html')

# -------------------------------------------------------------------
# REGISTER
# -------------------------------------------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('core.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('password_confirm', '')

        if not email or not password or not confirm:
            flash("All fields are required.", "error")
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for('auth.register'))

        db = get_db_connection()
        try:
            db.execute(
                """
                INSERT INTO users (email, password, role)
                VALUES (?, ?, 'client')
                """,
                (email, hash_password(password))
            )
            db.commit()
        except Exception:
            flash("Email already exists.", "error")
            return redirect(url_for('auth.register'))
        finally:
            db.close()

        flash("Account created successfully. Please login.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# -------------------------------------------------------------------
# LOGOUT
# -------------------------------------------------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))


# -------------------------------------------------------------------
# FORGOT PASSWORD (SAFE STUB)
# -------------------------------------------------------------------
@auth_bp.route('/forgot-password')
def forgot_password():
    """
    Placeholder route to prevent BuildError.
    Password reset flow to be implemented later.
    """
    return render_template('forgot_password.html')
