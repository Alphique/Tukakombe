# services/finance/user/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash

finance_bp = Blueprint(
    "finance",
    __name__,
    url_prefix="/finance",
    template_folder="templates"
)

# --- Finance Home ---
@finance_bp.route("/", methods=["GET"])
def home():
    return render_template("fin_home.html")


# --- Loans Page ---
@finance_bp.route("/loans", methods=["GET", "POST"])
def loans():
    if request.method == "POST":
        # Placeholder for handling loan request form submission
        business_name = request.form.get("business_name")
        loan_amount = request.form.get("loan_amount")
        loan_purpose = request.form.get("loan_purpose")
        # Normally: save to DB, validate, send notifications, etc.
        flash(f"Loan request submitted successfully for {business_name}!", "success")
        return redirect(url_for("finance.loans"))

    return render_template("fin_loans.html")


# --- Eligibility Check Page ---
@finance_bp.route("/eligibility", methods=["GET", "POST"])
def eligibility():
    if request.method == "POST":
        # Placeholder for eligibility check logic
        business_name = request.form.get("business_name")
        annual_turnover = request.form.get("annual_turnover")
        # Normally: calculate eligibility, save request, etc.
        flash(f"Eligibility check completed for {business_name}!", "success")
        return redirect(url_for("finance.eligibility"))

    return render_template("fin_eligibility.html")


# --- FAQ Page ---
@finance_bp.route("/faq", methods=["GET"])
def faq():
    # Dynamic FAQs for the template
    faqs = [
        {"question": "What is the maximum loan amount?", "answer": "Loan amounts vary by product, typically ranging from K50,000 to K5,000,000."},
        {"question": "How long does the approval process take?", "answer": "Applications are typically reviewed within 3–5 business days."},
        {"question": "Can I apply if my business is new?", "answer": "Yes, startup loans are available for businesses operating at least 6 months."},
        {"question": "What documents are required?", "answer": "Business registration, bank statements, financial statements, and ID documents."},
        {"question": "How do I repay my loan?", "answer": "Flexible repayment options are available. Details will be provided upon loan approval."},
    ]
    return render_template("fin_faq.html", faqs=faqs)


# --- Contact Page ---
@finance_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # Capture form data
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        # Normally: save to DB or send email
        flash(f"Thank you {name}, your message has been sent!", "success")
        return redirect(url_for("finance.contact"))

    return render_template("fin_contact.html")
