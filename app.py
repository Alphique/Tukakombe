# app.py
from flask import Flask
from config.settings import Config


# -----------------------------
# APPLICATION FACTORY
# -----------------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # -----------------------------
    # REGISTER CORE MODULE
    # -----------------------------
    from core.routes import core_bp
    app.register_blueprint(core_bp)

    # -----------------------------
    # REGISTER SERVICE MODULES
    # -----------------------------

    # =============================
    # TUKA DEVELOPERS
    # =============================
    from services.developers.routes.index import developers_index_bp
    from services.developers.routes.services import developers_services_bp
    from services.developers.routes.process import developers_process_bp
    from services.developers.routes.projects import developers_projects_bp
    from services.developers.routes.contact import developers_contact_bp

    app.register_blueprint(developers_index_bp)
    app.register_blueprint(developers_services_bp)
    app.register_blueprint(developers_process_bp)
    app.register_blueprint(developers_projects_bp)
    app.register_blueprint(developers_contact_bp)

    # =============================
    # TUKA BUSINESS ADVISORY
    # =============================
    from services.advisory.routes.index import advisory_index_bp
    from services.advisory.routes.services import advisory_services_bp
    from services.advisory.routes.engagement import advisory_engagement_bp
    from services.advisory.routes.case_studies import advisory_case_studies_bp
    from services.advisory.routes.contact import advisory_contact_bp

    app.register_blueprint(advisory_index_bp)
    app.register_blueprint(advisory_services_bp)
    app.register_blueprint(advisory_engagement_bp)
    app.register_blueprint(advisory_case_studies_bp)
    app.register_blueprint(advisory_contact_bp)

    # =============================
    # TUKA BRAND STUDIO
    # =============================
    from services.brand_studio.routes.index import brand_index_bp
    from services.brand_studio.routes.services import brand_services_bp
    from services.brand_studio.routes.portfolio import brand_portfolio_bp
    from services.brand_studio.routes.process import brand_process_bp
    from services.brand_studio.routes.contact import brand_contact_bp

    app.register_blueprint(brand_index_bp)
    app.register_blueprint(brand_services_bp)
    app.register_blueprint(brand_portfolio_bp)
    app.register_blueprint(brand_process_bp)
    app.register_blueprint(brand_contact_bp)

    # -----------------------------
    # FINANCE MODULE (PUBLIC)
    # -----------------------------
    from services.finance.public.routes.index import finance_index_bp
    from services.finance.public.routes.loans import finance_loans_bp
    from services.finance.public.routes.how_it_works import finance_how_it_works_bp
    from services.finance.public.routes.eligibility import finance_eligibility_bp
    from services.finance.public.routes.faq import finance_faq_bp
    from services.finance.public.routes.contact import finance_contact_bp

    app.register_blueprint(finance_index_bp)
    app.register_blueprint(finance_loans_bp)
    app.register_blueprint(finance_how_it_works_bp)
    app.register_blueprint(finance_eligibility_bp)
    app.register_blueprint(finance_faq_bp)
    app.register_blueprint(finance_contact_bp)

    # -----------------------------
    # FINANCE MODULE (SECURE APP)
    # -----------------------------
    from services.finance.app.routes.auth.login import finance_login_bp
    from services.finance.app.routes.auth.register import finance_register_bp
    from services.finance.app.routes.auth.reset_password import finance_reset_password_bp
    from services.finance.app.routes.dashboard import finance_dashboard_bp
    from services.finance.app.routes.apply.step_1_personal import finance_apply_step1_bp
    from services.finance.app.routes.apply.step_2_business import finance_apply_step2_bp
    from services.finance.app.routes.apply.step_3_financials import finance_apply_step3_bp
    from services.finance.app.routes.apply.step_4_documents import finance_apply_step4_bp
    from services.finance.app.routes.apply.review import finance_apply_review_bp
    from services.finance.app.routes.status import finance_status_bp
    from services.finance.app.routes.documents import finance_documents_bp

    app.register_blueprint(finance_login_bp)
    app.register_blueprint(finance_register_bp)
    app.register_blueprint(finance_reset_password_bp)
    app.register_blueprint(finance_dashboard_bp)
    app.register_blueprint(finance_apply_step1_bp)
    app.register_blueprint(finance_apply_step2_bp)
    app.register_blueprint(finance_apply_step3_bp)
    app.register_blueprint(finance_apply_step4_bp)
    app.register_blueprint(finance_apply_review_bp)
    app.register_blueprint(finance_status_bp)
    app.register_blueprint(finance_documents_bp)

    # -----------------------------
    # BLOG MODULE
    # -----------------------------
    from blog.routes.index import blog_index_bp
    from blog.routes.post import blog_post_bp

    app.register_blueprint(blog_index_bp)
    app.register_blueprint(blog_post_bp)

    # -----------------------------
    # CHATBOT MODULE (GLOBAL)
    # -----------------------------
    from chatbot.routes.widget_loader import chatbot_widget_bp
    from chatbot.routes.message import chatbot_message_bp
    from chatbot.routes.escalate import chatbot_escalate_bp
    from chatbot.routes.human_takeover import chatbot_human_bp

    app.register_blueprint(chatbot_widget_bp)
    app.register_blueprint(chatbot_message_bp)
    app.register_blueprint(chatbot_escalate_bp)
    app.register_blueprint(chatbot_human_bp)

    return app


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
