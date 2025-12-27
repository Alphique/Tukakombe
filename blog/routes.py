# blog/routes.py
from flask import Blueprint, render_template

blog_bp = Blueprint('blog', __name__, template_folder='templates')

@blog_bp.route('/blog')
def blog_home():
    return render_template('blog_home.html')

# Add other blog routes below
