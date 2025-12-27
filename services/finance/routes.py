# services/finance/routes.py
from flask import Blueprint, render_template

finance_bp = Blueprint(
    "finance",
    __name__,
    url_prefix="/finance",
    template_folder="templates"
)

@finance_bp.route("/")
def home():
    return render_template("fin_home.html")

@finance_bp.route("/loans")
def loans():
    return render_template("fin_loans.html")

@finance_bp.route("/eligibility")
def eligibility():
    return render_template("fin_eligibility.html")

@finance_bp.route("/faq")
def faq():
    return render_template("fin_faq.html")

@finance_bp.route("/contact")
def contact():
    return render_template("fin_contact.html")
