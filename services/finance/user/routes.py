from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth.decorators import login_required
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
import base64
from utils.database import get_db_connection, calculate_total_repayment

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
# EDIT LOAN APPLICATION
# --------------------------------------------------
@finance_bp.route('/loans/edit/<int:loan_id>', methods=['GET', 'POST'])
@login_required
def edit_loan(loan_id):
    db = get_db_connection()
    
    # Ensure the loan belongs to the logged-in user
    loan = db.execute(
        "SELECT * FROM loan_applications WHERE id = ? AND user_id = ?", 
        (loan_id, session['user_id'])
    ).fetchone()

    if not loan:
        db.close()
        flash("Loan application not found.", "error")
        return redirect(url_for('finance.my_loans'))

    # Fetch existing details
    personal_details = db.execute("SELECT * FROM personal_loan_details WHERE application_id = ?", (loan_id,)).fetchone()
    business_details = db.execute("SELECT * FROM business_loan_details WHERE application_id = ?", (loan_id,)).fetchone()
    details = personal_details if loan['loan_type'] == 'personal' else business_details

    if request.method == 'POST':
        try:
            loan_type = request.form.get('loan_type')
            
            # 1. Clean Numeric Data
            raw_amt = request.form.get('ind-amt') if loan_type == 'personal' else request.form.get('bus-amt')
            loan_amount = float(str(raw_amt).replace(',', '').strip()) if raw_amt else 0.0
            
            # 2. Update Main Table
            db.execute("""
                UPDATE loan_applications 
                SET loan_amount = ?, updated_date = CURRENT_TIMESTAMP, status = 'pending' 
                WHERE id = ?
            """, (loan_amount, loan_id))

            # 3. Process Signature (if a new one was drawn)
            sig_data = request.form.get('ind-signature-data') or request.form.get('bus-signature-data')
            new_sig_path = None
            if sig_data and 'base64' in sig_data:
                header, encoded = sig_data.split(",", 1)
                data = base64.b64decode(encoded)
                sig_filename = f"sig_upd_{loan_id}_{int(time.time())}.png"
                sig_path = os.path.join(LOAN_UPLOAD_FOLDER, sig_filename)
                with open(sig_path, "wb") as f:
                    f.write(data)
                new_sig_path = sig_filename

            # 4. Update Detailed Tables
            if loan_type == 'personal':
                db.execute("""
                    UPDATE personal_loan_details SET 
                        full_name = ?, nrc_number = ?, dob = ?, email = ?, 
                        phone = ?, address = ?, purpose = ?, period = ?
                        {sig_query}
                    WHERE application_id = ?
                """.format(sig_query=", signature_path = ?" if new_sig_path else ""), 
                tuple(filter(None, [
                    request.form.get('ind-name'), request.form.get('ind-nrc'),
                    request.form.get('ind-dob'), request.form.get('ind-email'),
                    request.form.get('ind-phone'), request.form.get('ind-address'),
                    request.form.get('ind-purpose'), request.form.get('ind-period'),
                    new_sig_path, loan_id
                ])))
            else:
                # Business Update
                raw_rev = request.form.get('bus-revenue')
                monthly_revenue = float(str(raw_rev).replace(',', '').strip()) if raw_rev else 0.0
                
                db.execute("""
                    UPDATE business_loan_details SET 
                        business_name = ?, business_registration_number = ?,
                        contact_person_name = ?, contact_person_email = ?,
                        contact_person_phone = ?, contact_person_position = ?,
                        monthly_revenue = ?, loan_amount = ?
                        {sig_query}
                    WHERE application_id = ?
                """.format(sig_query=", signature_path = ?" if new_sig_path else ""),
                tuple(filter(None, [
                    request.form.get('bus-name'), request.form.get('bus-reg'),
                    request.form.get('bus-contact-name'), request.form.get('bus-contact-email'),
                    request.form.get('bus-contact-phone'), request.form.get('bus-contact-position'),
                    monthly_revenue, loan_amount, new_sig_path, loan_id
                ])))

            # 5. Handle File Replacements (KYC & Business Docs)
            file_fields = {
                'ind-identity': 'identity_proof_path',
                'ind-residence': 'address_proof_path',
                'ind-income': 'income_proof_path',
                'bus-reg-cert': 'bus_reg_cert',
                'bus-tax-cert': 'bus_tax_cert',
                'bus-bank-stmts': 'bus_bank_stmts'
            }
            
            for form_key, db_col in file_fields.items():
                file = request.files.get(form_key)
                if file and file.filename != '':
                    filename = secure_filename(f"upd_{loan_id}_{form_key}_{file.filename}")
                    file.save(os.path.join(LOAN_UPLOAD_FOLDER, filename))
                    table = "personal_loan_details" if loan_type == 'personal' else "business_loan_details"
                    db.execute(f"UPDATE {table} SET {db_col} = ? WHERE application_id = ?", (filename, loan_id))

            # 6. Handle New Collateral Photos (Multiple)
            collateral_files = request.files.getlist('ind-collateral-photos')
            for file in collateral_files:
                if file and file.filename != '':
                    filename = secure_filename(f"coll_{loan_id}_{int(time.time())}_{file.filename}")
                    file.save(os.path.join(LOAN_UPLOAD_FOLDER, filename))
                    db.execute("INSERT INTO application_attachments (application_id, document_category, file_path) VALUES (?, ?, ?)",
                               (loan_id, 'Collateral Image', filename))

            db.commit()
            flash("Application successfully updated and resubmitted!", "success")
            return redirect(url_for('finance.my_loans'))

        except Exception as e:
            db.rollback()
            current_app.logger.error(f"Edit Error: {e}")
            flash("An error occurred while saving your changes.", "error")
        finally:
            db.close()

    return render_template('fin_edit_loan.html', loan=loan, details=details)
# --------------------------------------------------
# ADDITIONAL PAGES
# --------------------------------------------------
#----------------------------
# Loan Eligibility Checker  
@finance_bp.route("/eligibility", methods=["GET", "POST"])
def eligibility():
    result = None

    INTEREST_MAP = {
        1: 0.15, 2: 0.20, 3: 0.35, 4: 0.40,
        5: 0.55, 6: 0.60, 7: 0.75, 8: 0.80,
        9: 0.95, 10: 1.00, 11: 1.15, 12: 1.20
    }

    if request.method == "POST":
        submission_type = request.form["submission_type"]
        period = int(request.form["period"])
        revenue = float(request.form["revenue"])
        amount = float(request.form["amount"])
        collateral_value = float(request.form["collateral_value"])

        interest_rate = INTEREST_MAP.get(period, 0)
        interest = amount * interest_rate
        total_due = amount + interest

        # Revenue calculation
        if submission_type == "weekly":
            total_revenue = revenue * period
        else:
            months = period / 4
            total_revenue = revenue * months

        # Revenue check
        if total_revenue < total_due:
            result = {
                "status": "danger",
                "message": (
                    "Request a lower amount. Your revenue only supports loans "
                    "equal to or below your income for this period."
                )
            }

        # Collateral check (+10% buffer)
        elif collateral_value < (total_due + (amount * 0.10)):
            result = {
                "status": "danger",
                "message": (
                    "Ineligible. Your collateral value is insufficient. "
                    "Add higher-value collateral or request a smaller loan."
                )
            }

        else:
            result = {
                "status": "success",
                "message": (
                    "Eligible! Your revenue and collateral meet the "
                    "requirements for this loan period."
                )
            }

    return render_template("fin_eligibility.html", result=result)

#----------------------------
# Frequntly asked questions
#----------------------------
@finance_bp.route("/faq")
def faq():
    return render_template("fin_faq.html")
#---------------------------------------------
# Contact Us Page (GET and POST)
#---------------------------------------------
@finance_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Message sent successfully.", "success")
        return redirect(url_for("finance.contact"))
    return render_template("fin_contact.html")