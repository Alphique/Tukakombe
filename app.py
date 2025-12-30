from flask import Flask
from config.settings import Config
from utils.database import initialize_db

# Ensure tables exist
initialize_db()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from core.routes import core_bp
    app.register_blueprint(core_bp)

    from services.developers.routes import developers_bp
    app.register_blueprint(developers_bp)

    from services.advisory.routes import advisory_bp
    app.register_blueprint(advisory_bp)

    from services.brand_studio.routes import brand_bp
    app.register_blueprint(brand_bp)

    from services.finance.user.routes import finance_bp
    app.register_blueprint(finance_bp)

    from services.finance.admin.routes import finance_admin_bp
    app.register_blueprint(finance_admin_bp)

    from services.market_place.routes import market_bp
    app.register_blueprint(market_bp)

    from blog.routes import blog_bp
    app.register_blueprint(blog_bp)

    from chatbot.routes import chatbot_bp
    app.register_blueprint(chatbot_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
