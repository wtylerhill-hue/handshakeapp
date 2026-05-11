"""Flask application factory."""
import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-in-prod')
    app.config['WTF_CSRF_ENABLED'] = True
    return app
