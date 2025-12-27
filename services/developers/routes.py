# services/developers/routes.py
from flask import Blueprint, render_template

developers_bp = Blueprint(
    "developers",
    __name__,
    url_prefix="/developers"
)

@developers_bp.route("/")
def home():
    return render_template("developers/dev_home.html")

@developers_bp.route("/services")
def services():
    return render_template("developers/dev_services.html")

@developers_bp.route("/projects")
def projects():
    return render_template("developers/dev_projects.html")

@developers_bp.route("/trade")
def trade():
    return render_template("developers/dev_trade.html")

@developers_bp.route("/contact")
def contact():
    return render_template("developers/dev_contact.html")
