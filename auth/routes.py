# auth/routes.py
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from auth.utils import hash_password, verify_password
from auth.models import create_users_table
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
# Init
# -------------------------------------------------------------------
create_users_table()

# -------------------------------------------------------------------
# LOGIN
# -------------------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Prevent logged-in users from re-accessing login
    if session.get('user_id'):
        return redirect(url_for('core.home'))

    next_page = request.args.get('next')

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

        # Reset session securely
        session.clear()
        session['user_id'] = user['id']
        session['role'] = user['role']

        flash("Login successful.", "success")

        # Redirect to originally requested page if available
        if next_page:
            return redirect(next_page)

        return redirect(url_for('core.home'))

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

        if not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for('auth.register'))

        db = get_db_connection()
        try:
            db.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
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
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))


# -------------------------------------------------------------------
# FORGOT PASSWORD (STUB)
# -------------------------------------------------------------------
@auth_bp.route('/forgot-password')
def forgot_password():
    """
    Placeholder route to prevent BuildError.
    Full reset flow to be implemented later.
    """
    return render_template('forgot_password.html')
