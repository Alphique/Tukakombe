from flask import Blueprint, render_template

# Blueprint for core pages
core_bp = Blueprint('core', __name__, template_folder='templates')

# -----------------------------
# ROUTES
# -----------------------------

@core_bp.route('/')
def home():
    """Render the home page."""
    return render_template('home.html')


@core_bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')


@core_bp.route('/contact')
def contact():
    """Render the contact page."""
    return render_template('contact.html')


# -----------------------------
# ERROR HANDLERS
# -----------------------------

@core_bp.app_errorhandler(404)
def not_found(error):
    """Render 404 error page."""
    return render_template('404.html'), 404


@core_bp.app_errorhandler(500)
def server_error(error):
    """Render 500 error page."""
    return render_template('500.html'), 500
