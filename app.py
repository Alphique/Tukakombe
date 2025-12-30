# app.py
from flask import Flask
from config.settings import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # =============================
    # CORE (TUKAKOMBE PLATFORM)
    # =============================
    from core.routes import core_bp
    app.register_blueprint(core_bp)

    # =============================
    # TUKA DEVELOPERS
    # =============================
    from services.developers.routes import developers_bp
    app.register_blueprint(developers_bp)

    # =============================
    # TUKA BUSINESS ADVISORY
    # =============================
    from services.advisory.routes import advisory_bp
    app.register_blueprint(advisory_bp)

    # =============================
    # TUKA BRAND STUDIO
    # =============================
    from services.brand_studio.routes import brand_bp
    app.register_blueprint(brand_bp)

    # =============================
    # FINANCE (USER)
    # =============================
    from services.finance.user.routes import finance_bp
    app.register_blueprint(finance_bp)

    # =============================
    # FINANCE (ADMIN) - secure admin panel
    # =============================
    from services.finance.admin.routes import finance_admin_bp
    app.register_blueprint(finance_admin_bp)

     # =============================
    # MARKET PLACE SERVICES 
    # =============================
    from services.market_place.routes import market_bp
    app.register_blueprint(market_bp)

    # =============================
    # BLOG
    # =============================
    from blog.routes import blog_bp
    app.register_blueprint(blog_bp)

    # =============================
    # CHATBOT (GLOBAL)
    # =============================
    from chatbot.routes import chatbot_bp
    app.register_blueprint(chatbot_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
