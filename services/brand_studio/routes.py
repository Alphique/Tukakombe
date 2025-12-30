from flask import Blueprint, render_template

brand_bp = Blueprint(
    "brand_studio",
    __name__,
    url_prefix="/brand_studio",
    template_folder="templates"  # points directly to services/brand_studio/templates/
)

@brand_bp.route("/")
def home():
    return render_template("br_home.html")

@brand_bp.route("/services")
def services():
    return render_template("br_services.html")

@brand_bp.route("/portfolio")
def portfolio():
    return render_template("br_portfolio.html")

@brand_bp.route("/process")
def process():
    return render_template("br_process.html")

@brand_bp.route("/contact")
def contact():
    return render_template("br_contact.html")
