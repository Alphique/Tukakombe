# chatbot/routes.py
from flask import Blueprint, render_template

chatbot_bp = Blueprint('chatbot', __name__, template_folder='templates')

@chatbot_bp.route('/chat')
def chat_home():
    return render_template('chat_home.html')

# Add other chatbot routes here
