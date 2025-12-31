from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.database import get_db_connection
from auth.utils import verify_password
from auth.decorators import login_required, role_required

admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates',
    url_prefix='/admin'
)


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        admin = db.execute(
            "SELECT * FROM users WHERE email = ? AND role IN ('admin','super_admin')",
            (email,)
        ).fetchone()
        db.close()

        if not admin or not verify_password(password, admin['password']):
            flash("Invalid admin credentials", "error")
            return redirect(request.url)

        session['user_id'] = admin['id']
        session['role'] = admin['role']

        return redirect(url_for('admin.dashboard'))

    return render_template('admin_login.html')


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    return render_template('dashboard.html')


@admin_bp.route('/users')
@login_required
@role_required('super_admin')
def users():
    db = get_db_connection()
    users = db.execute("SELECT id, email, role FROM users").fetchall()
    db.close()
    return render_template('users.html', users=users)
