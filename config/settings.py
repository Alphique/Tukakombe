# config/settings.py

import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Flask settings
    DEBUG = True
    TESTING = False

    # Template & static defaults (Flask handles these automatically,
    # but explicit is better for large projects)
    TEMPLATES_AUTO_RELOAD = True

    # Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Future extensions (placeholders)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
