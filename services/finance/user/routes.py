from flask import Blueprint, render_template, request, redirect, url_for, flash
from auth.decorators import login_required

finance_bp = Blueprint(
    "finance",
    __name__,
    url_prefix="/finance",
    template_folder="templates"
)

# --- Finance Home (Public) ---
@finance_bp.route("/", methods=["GET"])
def home():
    return render_template("fin_home.html")


# --- Loans Page (Protected) ---
@finance_bp.route("/loans", methods=["GET", "POST"])
@login_required
def loans():
    if request.method == "POST":
        # Placeholder for loan form submission
        business_name = request.form.get("business_name")
        loan_amount = request.form.get("loan_amount")
        loan_purpose = request.form.get("loan_purpose")
        # Normally: save to DB
        flash(f"Loan request submitted successfully for {business_name}!", "success")
        return redirect(url_for("finance.loans"))

    return render_template("fin_loans.html")


# --- Eligibility Check Page (Public) ---
@finance_bp.route("/eligibility", methods=["GET", "POST"])
def eligibility():
    if request.method == "POST":
        business_name = request.form.get("business_name")
        annual_turnover = request.form.get("annual_turnover")
        flash(f"Eligibility check completed for {business_name}!", "success")
        return redirect(url_for("finance.eligibility"))

    return render_template("fin_eligibility.html")


# --- FAQ Page (Public) ---
@finance_bp.route("/faq", methods=["GET"])
def faq():
    faqs = [
        {"question": "What is the maximum loan amount?", "answer": "Loan amounts vary by product."},
        {"question": "How long does the approval process take?", "answer": "Typically 3–5 business days."},
        {"question": "Can I apply if my business is new?", "answer": "Yes, startups are eligible after 6 months."},
        {"question": "What documents are required?", "answer": "Business registration, bank statements, ID documents."},
        {"question": "How do I repay my loan?", "answer": "Flexible repayment options available."},
    ]
    return render_template("fin_faq.html", faqs=faqs)


# --- Contact Page (Public) ---
@finance_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        flash(f"Thank you {name}, your message has been sent!", "success")
        return redirect(url_for("finance.contact"))

    return render_template("fin_contact.html")
