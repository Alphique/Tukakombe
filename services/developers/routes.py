# services/developers/routes.py
from flask import Blueprint, render_template

developers_bp = Blueprint(
    "developers",
    __name__,
    url_prefix="/developers",
    template_folder="templates"
)


@developers_bp.route("/")
def developers_home():
    return render_template("dev_home.html")


@developers_bp.route("/services")
def developers_services():
    return render_template("dev_services.html")


@developers_bp.route("/projects")
def developers_projects():
    return render_template("dev_projects.html")


@developers_bp.route("/trade")
def developers_trade():
    return render_template("dev_trade.html")


@developers_bp.route("/contact")
def developers_contact():
    return render_template("dev_contact.html")
