from datetime import datetime, timezone
import uuid
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from utils.database import get_db_connection

developers_bp = Blueprint(
    "developers",
    __name__,
    url_prefix="/developers",
    template_folder="templates"  # REQUIRED
)

@developers_bp.route("/")
def home():
    return render_template("dev_home.html")

@developers_bp.route("/services")
def services():
    return render_template("dev_services.html")

@developers_bp.route("/projects")
def projects():
    return render_template("dev_projects.html")

@developers_bp.route("/trade")
def trade():
    return render_template("dev_trade.html")

@developers_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            full_name = request.form.get('full_name')
            company_name = request.form.get('company_name', '')
            email = request.form.get('email')
            phone = request.form.get('phone', '')
            whatsapp = request.form.get('whatsapp', '')
            inquiry_target = request.form.get('inquiry_target')
            service = request.form.get('service', '')
            subject = request.form.get('subject', 'General Inquiry')
            reason = request.form.get('reason')
            message = request.form.get('message')

            # Map developer form fields to inquiry fields
            # The developer form doesn't include `inquiry_target`/`reason` fields,
            # so set sensible defaults and map `project_type` to `reason`.
            if not inquiry_target:
                inquiry_target = 'developers'
            if not service:
                service = 'developers'
            if not reason:
                reason = request.form.get('project_type') or request.form.get('reason') or ''

            # basic validation: require name, email and message
            if not all([full_name, email, message]):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify(success=False, message='Please fill in all required fields.'), 400
                flash('Please fill in all required fields.', 'error')
                return redirect(request.referrer or url_for('developers.contact'))

            cursor.execute("""
                INSERT INTO tukakula_queries (
                    id, full_name, company_name, email, phone, whatsapp,
                    inquiry_target, service, subject, reason, message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                full_name,
                company_name,
                email,
                phone,
                whatsapp,
                inquiry_target,
                service,
                subject,
                reason,
                message,
                datetime.now(timezone.utc).isoformat()
            ))

            conn.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True, message='Inquiry received. We will contact you shortly.'), 200
            flash('Thank you for your inquiry! We will contact you shortly.', 'success')
            return redirect(request.referrer or url_for('developers.contact'))

        except Exception as e:
            conn.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, message=str(e)), 500
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            conn.close()

    return render_template('dev_contact.html')
