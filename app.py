from flask import Flask
from config.settings import Config
from utils.database import initialize_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # --------------------------
    # Initialize database
    # --------------------------
    # Make sure DB init runs inside app context
    with app.app_context():
        initialize_db()

    # --------------------------
    # AUTH (USERS)
    # --------------------------
    from auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    # --------------------------
    # ADMIN (GLOBAL)
    # --------------------------
    from admin.routes import admin_bp
    app.register_blueprint(admin_bp)

    # --------------------------
    # CORE
    # --------------------------
    from core.routes import core_bp
    app.register_blueprint(core_bp)

    # --------------------------
    # SERVICES
    # --------------------------
    from services.developers.routes import developers_bp
    from services.advisory.routes import advisory_bp
    from services.brand_studio.routes import brand_bp
    from services.finance.user.routes import finance_bp
    from services.market_place.routes import market_bp

    app.register_blueprint(developers_bp)
    app.register_blueprint(advisory_bp)
    app.register_blueprint(brand_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(market_bp)

    # --------------------------
    # BLOG
    # --------------------------
    from blog.routes import blog_bp
    app.register_blueprint(blog_bp)

    # --------------------------
    # Flash & Session Check
    # --------------------------
    # Ensure SECRET_KEY is set (required for flash messages)
    if not app.secret_key:
        app.secret_key = Config.SECRET_KEY or "replace_with_secure_random_string"

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
