"""Application package: creates the app, registers blueprints and hooks."""
import os
from flask import Flask, g, session
from .app_factory import create_app
from .db_connect import close_db, get_db
from .functions import get_session_user

app = create_app()

from flask_wtf.csrf import CSRFProtect
CSRFProtect(app)


@app.context_processor
def inject_globals():
    """Inject current_user and sidebar notifications into every template."""
    notifications = []
    if session.get('user_role') == 'Student' and session.get('user_id'):
        db = getattr(g, 'db', None)
        if db:
            try:
                with db.cursor() as cur:
                    cur.execute("""
                        SELECT n.NotificationID,
                               COALESCE(ci.Company_Name, ar.External_Company) AS Company_Name,
                               ar.Deadline, jp.Job_Title
                        FROM notifications n
                        JOIN application_records ar ON n.ApplicationID = ar.ApplicationID
                        LEFT JOIN job_postings jp ON ar.PostingID = jp.PostingID
                        LEFT JOIN contact_information ci ON jp.ContactID = ci.ContactID
                        WHERE n.ProfileID = %s AND n.Acknowledged = FALSE
                        ORDER BY n.Sent_Date DESC
                        LIMIT 5
                    """, (session['user_id'],))
                    notifications = cur.fetchall()
            except Exception:
                pass
    return {
        'current_user': get_session_user(),
        'sidebar_notifications': notifications,
    }


# Blueprints
from app.blueprints.auth import bp as auth_bp
from app.blueprints.students import bp as students_bp
from app.blueprints.advisors import bp as advisors_bp
from app.blueprints.employers import bp as employers_bp

app.register_blueprint(auth_bp)
app.register_blueprint(students_bp)
app.register_blueprint(advisors_bp)
app.register_blueprint(employers_bp)

from . import routes


@app.before_request
def before_request():
    g.db = get_db()


@app.teardown_appcontext
def teardown_db(exception=None):
    close_db(exception)
