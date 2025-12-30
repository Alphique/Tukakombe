from flask import Blueprint, render_template

market_bp = Blueprint(
    "market_place",
    __name__,
    url_prefix="/market_place",
    template_folder="templates"  # points directly to services/market_place/templates/
)


@market_bp.route("/")
def home():
    return render_template("mp_home.html")

@market_bp.route("/services")
def services():
    return render_template("mp_services.html")

@market_bp.route("/portfolio")
def portfolio():
    return render_template("mp_portfolio.html")

@market_bp.route("/process")
def process():
    return render_template("mp_process.html")

@market_bp.route("/contact")
def contact():
    return render_template("mp_contact.html")