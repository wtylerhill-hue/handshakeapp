"""Authentication blueprint: login, logout, register."""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, g
from app.functions import hash_password, verify_password, set_user_session

bp = Blueprint('auth', __name__)


@bp.get('/login')
def login():
    """Render login form; redirect authenticated users to their dashboard."""
    if 'user_id' in session:
        return _redirect_by_role(session.get('user_role'))
    return render_template('auth/login.html')


@bp.post('/login')
def login_post():
    """Authenticate user and start session."""
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    db = g.db
    if not db:
        flash('Database unavailable. Try again later.', 'error')
        return redirect(url_for('auth.login'))

    with db.cursor() as cur:
        cur.execute("SELECT * FROM user_profiles WHERE Email = %s", (email,))
        user = cur.fetchone()

    if not user or not verify_password(password, user['Password_Hash']):
        flash('Invalid email or password.', 'error')
        return redirect(url_for('auth.login'))

    with db.cursor() as cur:
        cur.execute(
            "UPDATE user_profiles SET Last_Login = NOW() WHERE ProfileID = %s",
            (user['ProfileID'],)
        )
    db.commit()

    set_user_session(user)
    return _redirect_by_role(user['Role'])


@bp.get('/logout')
def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for('auth.login'))


@bp.get('/register')
def register():
    """Render registration form."""
    if 'user_id' in session:
        return _redirect_by_role(session.get('user_role'))
    return render_template('auth/register.html')


@bp.post('/register')
def register_post():
    """Create a new user account."""
    first_name = request.form.get('first_name', '').strip()
    last_name  = request.form.get('last_name', '').strip()
    email      = request.form.get('email', '').strip()
    password   = request.form.get('password', '')
    confirm    = request.form.get('confirm_password', '')
    role       = request.form.get('role', '')

    if not all([first_name, last_name, email, password, role]):
        flash('All required fields must be filled.', 'error')
        return redirect(url_for('auth.register'))

    if password != confirm:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('auth.register'))

    if role not in ('Student', 'Advisor', 'Employer'):
        flash('Invalid role selected.', 'error')
        return redirect(url_for('auth.register'))

    db = g.db
    with db.cursor() as cur:
        cur.execute("SELECT ProfileID FROM user_profiles WHERE Email = %s", (email,))
        if cur.fetchone():
            flash('An account with that email already exists.', 'error')
            return redirect(url_for('auth.register'))

    major         = request.form.get('major', '').strip() or None
    grad_year_raw = request.form.get('graduation_year', '').strip()
    grad_year     = int(grad_year_raw) if grad_year_raw.isdigit() else None
    skills        = request.form.get('skills', '').strip() or None
    location_pref = request.form.get('location_preference', '').strip() or None
    job_type_pref = request.form.get('job_type_preference', '').strip() or None
    department    = request.form.get('department', '').strip() or None

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO user_profiles
                (First_Name, Last_Name, Email, Password_Hash, Role,
                 Major, Graduation_Year, Skills,
                 Location_Preference, Job_Type_Preference, Department)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (first_name, last_name, email, hash_password(password), role,
              major, grad_year, skills, location_pref, job_type_pref, department))
    db.commit()

    flash('Account created. Please sign in.', 'success')
    return redirect(url_for('auth.login'))


def _redirect_by_role(role):
    """Return a redirect response to the correct dashboard for a given role."""
    if role == 'Student':
        return redirect(url_for('students.dashboard'))
    if role == 'Advisor':
        return redirect(url_for('advisors.advisor_view'))
    if role == 'Employer':
        return redirect(url_for('employers.my_postings'))
    return redirect(url_for('auth.login'))
