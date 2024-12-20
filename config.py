import os

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Database configuration
    # Defines the URI for the SQLite database. The database file will be located in the base directory of the project.
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'tasknest.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for CSRF and session management
    # Retrieves the secret key from an environment variable or defaults to a hardcoded value.
    SECRET_KEY = os.environ.get("SECRET_KEY", "a-very-secret-key")

    # Email server configuration
    MAIL_SERVER = 'smtp.gmail.com'  # Specifies the email server (Gmail SMTP server in this case)
    MAIL_PORT = 587  # Port for the email server
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "your-email@gmail.com")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "your-app-password")
