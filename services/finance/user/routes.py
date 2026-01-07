from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth.decorators import login_required
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

finance_bp = Blueprint(
    "finance",
    __name__,
    url_prefix="/finance",
    template_folder="templates"
)

# --------------------------------------------------
# FINANCE HOME
# --------------------------------------------------
@finance_bp.route("/", methods=["GET"])
def home():
    return render_template("fin_home.html")

# --------------------------------------------------
# LOAN APPLICATION (PROTECTED)
# --------------------------------------------------
@finance_bp.route("/loans", methods=["GET", "POST"])
@login_required
def loans():
    from utils.database import (
        create_loan_application,
        save_personal_loan_details,
        save_business_loan_details,
        save_collateral_items,
        save_application_attachments,
        calculate_total_repayment,
        get_db_connection
    )

    if request.method == "POST":
        loan_type = request.form.get("loan_type")
        user_id = session.get("user_id")

        if loan_type not in ("personal", "business"):
            flash("Invalid loan type selected.", "danger")
            return redirect(url_for("finance.loans"))

        # 1. Create the Application Entry first
        application_id, application_number = create_loan_application(user_id, loan_type)

        if not application_id:
            flash("Failed to create loan application entry.", "danger")
            return redirect(url_for("finance.loans"))

        try:
            total_repayment = 0
            
            # --------------------------------------------------
            # CASE A: PERSONAL LOAN
            # --------------------------------------------------
            if loan_type == "personal":
                success = save_personal_loan_details(application_id, request.form)
                if not success:
                    flash("Missing required personal loan fields.", "danger")
                    return redirect(url_for("finance.loans"))

                amt_raw = request.form.get("ind-amt", "0").replace(',', '').replace('$', '')
                amt = float(amt_raw) if amt_raw else 0.0
                total_repayment = calculate_total_repayment(amt)

                collateral_items = []
                for item in request.form.getlist("collateral"):
                    if item and item != "other":
                        collateral_items.append({
                            "name": item,
                            "type": "personal",
                            "value": 0,
                            "condition": request.form.get("ind-description", "")
                        })
                if collateral_items:
                    save_collateral_items(application_id, "personal", collateral_items)

            # --------------------------------------------------
            # CASE B: BUSINESS LOAN
            # --------------------------------------------------
            else:
                success = save_business_loan_details(application_id, request.form)
                if not success:
                    flash("Failed to save business details.", "danger")
                    return redirect(url_for("finance.loans"))

                amt_raw = request.form.get("bus-amt", "0").replace(',', '').replace('$', '')
                amt = float(amt_raw) if amt_raw else 0.0
                total_repayment = calculate_total_repayment(amt)

                bus_collateral_name = request.form.get("bus-collateral-type")
                if bus_collateral_name:
                    save_collateral_items(application_id, "business", [{
                        "name": bus_collateral_name,
                        "type": "business",
                        "value": float(request.form.get("bus-collateral-value", 0) or 0),
                        "condition": request.form.get("bus-collateral-desc")
                    }])

            # --------------------------------------------------
            # 2. FINAL DB UPDATE
            # --------------------------------------------------
            conn = get_db_connection()
            conn.execute(
                "UPDATE loan_applications SET total_repayment=?, updated_date=CURRENT_TIMESTAMP WHERE id=?",
                (total_repayment, application_id)
            )
            conn.commit()
            conn.close()

            # --------------------------------------------------
            # 3. FILE ATTACHMENTS HANDLING (FIXED FOR ADMIN)
            # --------------------------------------------------
            # Define specific keys used in the HTML form for both types
            # Format: (Form Key, Admin Label)
            file_mapping = [
                # Personal Keys
                ('ind-identity', 'ID Copy'),
                ('ind-residence', 'Proof of Residence'),
                ('ind-income', 'Proof of Income'),
                ('ind-signature-data', 'Signature'),
                # Business Keys (Fixed mapping)
                ('bus-reg-cert', 'Business Registration'),
                ('bus-tax-cert', 'Tax Certificate'),
                ('bus-financials', 'Financial Statements'),
                ('bus-bank-stmts', 'Bank Statements'),
                ('bus-directors-id', 'Director ID'),
                ('bus-address-proof', 'Business Address Proof'),
                ('bus-collateral-docs', 'Collateral Documents'),
                ('bus-collateral-proof', 'Collateral Proof'),
                ('bus-collateral-photos', 'Collateral Photos'),
                ('attachments', 'General Attachment')
            ]

            upload_dir = os.path.join("static", "uploads", "loans", application_number)
            os.makedirs(upload_dir, exist_ok=True)

            for file_key, label in file_mapping:
                files = request.files.getlist(file_key)
                for file in files:
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        unique_fn = f"{uuid.uuid4().hex[:8]}_{filename}"
                        save_path = os.path.join(upload_dir, unique_fn)
                        
                        # Save actual file to disk
                        file.save(save_path)

                        # Save to database application_attachments table
                        # Store path as 'uploads/loans/APP_NUM/file.ext' for consistency
                        db_relative_path = f"uploads/loans/{application_number}/{unique_fn}"
                        
                        save_application_attachments(
                            application_id,
                            label, # This is the category the admin sees
                            filename,
                            db_relative_path
                        )

            flash(f"Application {application_number} submitted successfully!", "success")
            return redirect(url_for("finance.my_loans"))

        except Exception as e:
            print(f"CRITICAL LOAN ROUTE ERROR: {e}")
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for("finance.loans"))

    return render_template("fin_loans.html")

# --------------------------------------------------
# DASHBOARD & LISTINGS
# --------------------------------------------------
@finance_bp.route("/dashboard")
@login_required
def client_dashboard():
    from utils.database import get_db_connection
    user_id = session.get("user_id")
    db = get_db_connection()
    
    loan_stats = db.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
        FROM loan_applications WHERE user_id = ?
    """, (user_id,)).fetchone()
    
    recent_loans = db.execute("""
        SELECT la.*, COALESCE(p.full_name, b.business_name, 'Applicant') as display_name
        FROM loan_applications la
        LEFT JOIN personal_loan_details p ON la.id = p.application_id
        LEFT JOIN business_loan_details b ON la.id = b.application_id
        WHERE la.user_id = ? 
        ORDER BY la.applied_date DESC LIMIT 3
    """, (user_id,)).fetchall()
    
    db.close()
    return render_template("fin_client_dashboard.html", stats=loan_stats, recent_loans=recent_loans)

@finance_bp.route("/my-loans")
@login_required
def my_loans():
    from utils.database import get_db_connection
    user_id = session.get("user_id")
    db = get_db_connection()
    
    loans = db.execute("""
        SELECT la.*, COALESCE(p.full_name, b.business_name, 'Applicant') as display_name
        FROM loan_applications la
        LEFT JOIN personal_loan_details p ON la.id = p.application_id
        LEFT JOIN business_loan_details b ON la.id = b.application_id
        WHERE la.user_id = ? 
        ORDER BY la.applied_date DESC
    """, (user_id,)).fetchall()
    
    db.close()
    return render_template("fin_my_loans.html", loans=loans)

# --------------------------------------------------
# EDITING & UTILITIES
# --------------------------------------------------
@finance_bp.route("/loans/edit/<int:loan_id>", methods=["GET", "POST"])
@login_required
def edit_loan(loan_id):
    from utils.database import get_db_connection, calculate_total_repayment
    user_id = session.get("user_id")
    db = get_db_connection()

    loan = db.execute("""
        SELECT * FROM loan_applications 
        WHERE id = ? AND user_id = ? AND status = 'pending'
    """, (loan_id, user_id)).fetchone()

    if not loan:
        flash("Application not found or is already being processed.", "danger")
        db.close()
        return redirect(url_for("finance.my_loans"))

    if request.method == "POST":
        loan_amount = float(request.form.get("loan_amount", 0).replace(',', ''))
        total_repayment = calculate_total_repayment(loan_amount)
        
        db.execute("UPDATE loan_applications SET total_repayment = ?, updated_date = CURRENT_TIMESTAMP WHERE id = ?", 
                   (total_repayment, loan_id))

        if loan['loan_type'] == 'personal':
            db.execute("""
                UPDATE personal_loan_details SET loan_amount=?, purpose=?, full_name=? WHERE application_id=?
            """, (loan_amount, request.form.get("purpose"), request.form.get("full_name"), loan_id))
        else:
            db.execute("""
                UPDATE business_loan_details SET loan_amount=?, purpose=?, business_name=? WHERE application_id=?
            """, (loan_amount, request.form.get("purpose"), request.form.get("business_name"), loan_id))
        
        db.commit()
        db.close()
        flash("Application updated successfully!", "success")
        return redirect(url_for("finance.my_loans"))

    details = None
    if loan['loan_type'] == 'personal':
        details = db.execute("SELECT * FROM personal_loan_details WHERE application_id=?", (loan_id,)).fetchone()
    else:
        details = db.execute("SELECT * FROM business_loan_details WHERE application_id=?", (loan_id,)).fetchone()
    
    db.close()
    return render_template("fin_edit_loan.html", loan=loan, details=details)

@finance_bp.route("/eligibility", methods=["GET", "POST"])
def eligibility():
    if request.method == "POST":
        flash("Eligibility check complete.", "success")
        return redirect(url_for("finance.eligibility"))
    return render_template("fin_eligibility.html")

@finance_bp.route("/faq")
def faq():
    return render_template("fin_faq.html")

@finance_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Message sent successfully.", "success")
        return redirect(url_for("finance.contact"))
    return render_template("fin_contact.html")