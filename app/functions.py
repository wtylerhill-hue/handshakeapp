"""Shared helpers: auth decorators, password utilities, session access."""
from functools import wraps
from flask import session, redirect, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    """Return a Werkzeug-hashed password string."""
    return generate_password_hash(password)


def verify_password(password, password_hash):
    """Return True if password matches hash."""
    return check_password_hash(password_hash, password)


def require_login(f):
    """Redirect unauthenticated requests to login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    """Abort 403 if the current user's role is not in allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if session.get('user_role') not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_session_user():
    """Return a dict of the current user from session data, or None."""
    if 'user_id' not in session:
        return None
    return {
        'ProfileID':          session['user_id'],
        'Role':               session.get('user_role', ''),
        'First_Name':         session.get('first_name', ''),
        'Last_Name':          session.get('last_name', ''),
        'Email':              session.get('email', ''),
        'Major':              session.get('major', ''),
        'Graduation_Year':    session.get('graduation_year'),
        'Skills':             session.get('skills', ''),
        'Department':         session.get('department', ''),
        'Location_Preference':  session.get('location_preference', ''),
        'Job_Type_Preference':  session.get('job_type_preference', ''),
    }


def set_user_session(user):
    """Populate session from a user_profiles row dict."""
    session.clear()
    session['user_id']           = user['ProfileID']
    session['user_role']         = user['Role']
    session['first_name']        = user['First_Name']
    session['last_name']         = user['Last_Name']
    session['email']             = user['Email']
    session['major']             = user.get('Major') or ''
    session['graduation_year']   = user.get('Graduation_Year')
    session['skills']            = user.get('Skills') or ''
    session['department']        = user.get('Department') or ''
    session['location_preference']  = user.get('Location_Preference') or ''
    session['job_type_preference']  = user.get('Job_Type_Preference') or ''
