from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from auth.utils import hash_password, verify_password
from auth.models import create_users_table
from utils.database import get_db_connection

auth_bp = Blueprint('auth', __name__, template_folder='templates')

create_users_table()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        user = db.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email,)
        ).fetchone()
        db.close()

        if not user or not verify_password(password, user['password']):
            flash("Invalid credentials", "error")
            return redirect(request.url)

        session['user_id'] = user['id']
        session['role'] = user['role']

        return redirect(url_for('core.home'))

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['password_confirm']

        if password != confirm:
            flash("Passwords do not match", "error")
            return redirect(request.url)

        db = get_db_connection()
        try:
            db.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, hash_password(password))
            )
            db.commit()
        except:
            flash("Email already exists", "error")
            return redirect(request.url)
        finally:
            db.close()

        flash("Account created. Login now.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
