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
# LOANS (PROTECTED)
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

        flash("DEBUG: Loan form submitted", "info")

        loan_type = request.form.get("loan_type")
        user_id = session.get("user_id")

        flash(f"DEBUG: loan_type={loan_type}", "info")
        flash(f"DEBUG: user_id={user_id}", "info")

        if loan_type not in ("personal", "business"):
            flash("Invalid loan type selected.", "danger")
            return redirect(url_for("finance.loans"))

        # --------------------------------------------------
        # CREATE CORE APPLICATION
        # --------------------------------------------------
        application_id, application_number = create_loan_application(
            user_id, loan_type
        )

        if not application_id:
            flash("Failed to create loan application.", "danger")
            return redirect(url_for("finance.loans"))

        flash(f"DEBUG: Application #{application_number}", "info")

        try:
            # --------------------------------------------------
            # PERSONAL LOAN
            # --------------------------------------------------
            if loan_type == "personal":
                form_data = {
                    "loan_amount": float(request.form.get("loan_amount", 0)),
                    "purpose": request.form.get("purpose"),
                    "repayment_period": int(request.form.get("repayment_days", 30)),
                    "full_name": request.form.get("full_name"),
                    "dob": request.form.get("date_of_birth"),
                    "nrc": request.form.get("nrc_number"),
                    "email": request.form.get("email"),
                    "phone": request.form.get("phone_number"),
                    "address": request.form.get("residential_address"),
                }

                save_personal_loan_details(application_id, form_data)

                total_repayment = calculate_total_repayment(form_data["loan_amount"])

                collateral_items = []
                for item in request.form.getlist("collateral"):
                    if item != "other":
                        collateral_items.append({
                            "name": item,
                            "type": "personal",
                            "value": 0,
                            "condition": request.form.get("item_description", "")
                        })

                if collateral_items:
                    save_collateral_items(application_id, loan_type, collateral_items)

            # --------------------------------------------------
            # BUSINESS LOAN
            # --------------------------------------------------
            else:
                form_data = {
                    "business_name": request.form.get("business_name"),
                    "reg_number": request.form.get("business_reg_no"),
                    "loan_amount": float(request.form.get("loan_amount", 0)),
                    "purpose": request.form.get("purpose"),
                    "repayment_period": int(request.form.get("repayment_days", 30)),
                    "contact_name": request.form.get("contact_name"),
                    "email": request.form.get("contact_email"),
                    "phone": request.form.get("contact_phone"),
                    "address": request.form.get("business_address"),
                }

                save_business_loan_details(application_id, form_data)

                total_repayment = calculate_total_repayment(form_data["loan_amount"])

                save_collateral_items(application_id, loan_type, [{
                    "name": request.form.get("collateral_type"),
                    "type": "business",
                    "value": float(request.form.get("collateral_value", 0)),
                    "condition": request.form.get("collateral_description")
                }])

            # --------------------------------------------------
            # UPDATE TOTAL REPAYMENT
            # --------------------------------------------------
                conn = get_db_connection()
                conn.execute(
                     "UPDATE loan_applications SET total_repayment=?, updated_date=CURRENT_TIMESTAMP WHERE id=?",
                  (total_repayment, application_id)
                    )
                conn.commit()
                conn.close()
            # --------------------------------------------------
            # FILE ATTACHMENTS
            # --------------------------------------------------
            upload_dir = os.path.join(
                "static", "uploads", "loans", application_number
            )
            os.makedirs(upload_dir, exist_ok=True)

            for file in request.files.getlist("attachments"):
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique = f"{uuid.uuid4().hex}_{filename}"
                    path = os.path.join(upload_dir, unique)
                    file.save(path)

                    save_application_attachments(
                        application_id,
                        "loan_document",
                        filename,
                        path.replace("static/", "")
                    )

            flash(f"Loan application {application_number} submitted successfully!", "success")
            return redirect(url_for("finance.loans"))

        except Exception as e:
            flash(f"Submission failed: {str(e)}", "danger")
            return redirect(url_for("finance.loans"))

    return render_template("fin_loans.html")

# --------------------------------------------------
# MY LOANS (PROTECTED)
# --------------------------------------------------
@finance_bp.route("/loans/edit/<int:loan_id>", methods=["GET", "POST"])
@login_required
def edit_loan(loan_id):
    from utils.database import get_db_connection, calculate_total_repayment
    user_id = session.get("user_id")
    db = get_db_connection()

    # 1. Fetch existing application and verify ownership + status
    loan = db.execute("""
        SELECT * FROM loan_applications 
        WHERE id = ? AND user_id = ? AND status = 'pending'
    """, (loan_id, user_id)).fetchone()

    if not loan:
        flash("Application not found or cannot be edited (already processed).", "danger")
        return redirect(url_for("finance.my_loans"))

    if request.method == "POST":
        loan_amount = float(request.form.get("loan_amount", 0))
        total_repayment = calculate_total_repayment(loan_amount)
        
        # 2. Update Main Application
        db.execute("""
            UPDATE loan_applications 
            SET total_repayment = ?, updated_date = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (total_repayment, loan_id))

        # 3. Update Specific Details based on type
        if loan['loan_type'] == 'personal':
            db.execute("""
                UPDATE personal_loan_details SET 
                loan_amount=?, purpose=?, repayment_period_days=?, full_name=?, phone_number=?, residential_address=?
                WHERE application_id=?
            """, (loan_amount, request.form.get("purpose"), int(request.form.get("repayment_days", 30)),
                  request.form.get("full_name"), request.form.get("phone_number"), 
                  request.form.get("residential_address"), loan_id))
        else:
            db.execute("""
                UPDATE business_loan_details SET 
                loan_amount=?, purpose=?, business_name=?, contact_phone=?, business_address=?
                WHERE application_id=?
            """, (loan_amount, request.form.get("purpose"), request.form.get("business_name"),
                  request.form.get("contact_phone"), request.form.get("business_address"), loan_id))
        
        db.commit()
        db.close()
        flash("Application updated successfully!", "success")
        return redirect(url_for("finance.my_loans"))

    # Fetch details for pre-filling the form
    details = None
    if loan['loan_type'] == 'personal':
        details = db.execute("SELECT * FROM personal_loan_details WHERE application_id=?", (loan_id,)).fetchone()
    else:
        details = db.execute("SELECT * FROM business_loan_details WHERE application_id=?", (loan_id,)).fetchone()
    
    db.close()
    return render_template("fin_edit_loan.html", loan=loan, details=details)
# --------------------------------------------------
# ELIGIBILITY
# --------------------------------------------------
@finance_bp.route("/eligibility", methods=["GET", "POST"])
def eligibility():
    if request.method == "POST":
        flash("Eligibility check completed.", "success")
        return redirect(url_for("finance.eligibility"))
    return render_template("fin_eligibility.html")

# --------------------------------------------------
# FAQ
# --------------------------------------------------
@finance_bp.route("/faq")
def faq():
    return render_template("fin_faq.html")

# --------------------------------------------------
# CONTACT
# --------------------------------------------------
@finance_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Message sent successfully.", "success")
        return redirect(url_for("finance.contact"))
    return render_template("fin_contact.html")
