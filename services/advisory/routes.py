# services/advisory/routes.py
from flask import Blueprint, render_template

advisory_bp = Blueprint(
    "advisory",
    __name__,
    url_prefix="/advisory",
    template_folder="templates"
)

@advisory_bp.route("/")
def home():
    return render_template("adv_home.html")

@advisory_bp.route("/services")
def services():
    return render_template("adv_services.html")

@advisory_bp.route("/engagement")
def engagement():
    return render_template("adv_engagement.html")

@advisory_bp.route("/case-studies")
def case_studies():
    return render_template("adv_case_studies.html")

@advisory_bp.route("/contact")
def contact():
    return render_template("adv_contact.html")
