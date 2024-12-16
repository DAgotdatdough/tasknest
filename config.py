import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'tasknest.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for CSRF and session management
    SECRET_KEY = os.environ.get("SECRET_KEY", "a-very-secret-key")

    # Email server configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "your-email@gmail.com")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "your-app-password")




