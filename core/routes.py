# core/routes.py
from flask import Blueprint, render_template

core_bp = Blueprint("core", __name__)

@core_bp.route("/")
def home():
    return render_template("home.html")

@core_bp.route("/about")
def about():
    return render_template("about.html")

@core_bp.route("/contact")
def contact():
    return render_template("contact.html")


# -----------------------------
# ERROR HANDLERS
# -----------------------------
@core_bp.app_errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

@core_bp.app_errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500
