"""Root-level routes."""
from flask import redirect, url_for
from . import app


@app.route('/')
def index():
    """Redirect root to login."""
    return redirect(url_for('auth.login'))
