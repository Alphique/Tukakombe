# core/routes.py
from datetime import datetime, timezone
import uuid
from flask import Blueprint, flash, redirect, render_template, request

from utils.database import get_db_connection

# Blueprint for core pages
core_bp = Blueprint('core', __name__, template_folder='templates')

# -----------------------------
# ROUTES
# -----------------------------

@core_bp.route('/')
def home():
    """Render the home page."""
    return render_template('home.html')

    
@core_bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@core_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO tukakula_queries (
                    id, full_name, company_name, email, phone, whatsapp,
                    inquiry_target, service, subject, reason, message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                request.form.get("full_name"),
                request.form.get("company_name"),
                request.form.get("email"),
                request.form.get("phone"),
                request.form.get("whatsapp"),
                request.form.get("inquiry_target"),
                request.form.get("service"),
                request.form.get("subject", "General Inquiry"), # Default if empty
                request.form.get("reason"),
                request.form.get("message"),
                datetime.now(timezone.utc).isoformat() # Fixed timezone issue
            ))

            conn.commit()
            flash("Your inquiry has been sent successfully.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"An error occurred: {str(e)}", "error")
        finally:
            conn.close()

        return redirect("contact")

    return render_template("contact.html")


# -----------------------------
# ERROR HANDLERS
# -----------------------------

@core_bp.app_errorhandler(404)
def not_found(error):
    """Render 404 error page."""
    return render_template('404.html'), 404


@core_bp.app_errorhandler(500)
def server_error(error):
    """Render 500 error page."""
    return render_template('500.html'), 500

# -----------------------------
# SERVICES
# -----------------------------

@core_bp.route('/brand-studio')
def brand_studio_home():
    """Render Brand Studio home page."""
    return render_template('br_home.html')

@core_bp.route('/developers')
def developer_tools_home():
    """Render Developer Tools home page."""
    return render_template('dev_home.html')

@core_bp.route('/advisory')
def advisory_services_home():
    """Render Advisory Services home page."""
    return render_template('adv_home.html')

@core_bp.route('/finance')
def finance_services_home():
    """Render Finance Services home page."""
    return render_template('fin_home.html')