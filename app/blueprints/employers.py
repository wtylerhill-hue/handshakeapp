"""Employer blueprint: post a job, view all postings, toggle status."""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, g, jsonify, abort
from app.functions import require_role

bp = Blueprint('employers', __name__)


@bp.get('/employer/post')
@require_role('Employer')
def post_job():
    """Render job posting form."""
    return render_template('employer/post_job.html')


@bp.post('/employer/post')
@require_role('Employer')
def create_posting():
    """Save contact and job posting records."""
    db = g.db

    company_name           = request.form.get('company_name', '').strip()
    contact_name           = request.form.get('contact_name', '').strip()
    contact_email          = request.form.get('contact_email', '').strip()
    contact_phone          = request.form.get('contact_phone', '').strip() or None
    job_title              = request.form.get('job_title', '').strip()
    description            = request.form.get('description', '').strip()
    location_type          = request.form.get('location_type', '').strip()
    salary_range           = request.form.get('salary_range', '').strip()
    required_quals         = request.form.get('required_qualifications', '').strip()
    deadline               = request.form.get('application_deadline', '').strip()

    required = [company_name, contact_name, contact_email, job_title,
                description, location_type, salary_range, required_quals, deadline]
    if not all(required):
        flash('All fields are required.', 'error')
        return redirect(url_for('employers.post_job'))

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO contact_information (Company_Name, Contact_Name, Contact_Email, Contact_Phone)
            VALUES (%s,%s,%s,%s)
        """, (company_name, contact_name, contact_email, contact_phone))
        contact_id = cur.lastrowid

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO job_postings
                (Job_Title, Description, Location_Type, Salary_Range,
                 Required_Qualifications, Application_Deadline, Posting_Status, ContactID)
            VALUES (%s,%s,%s,%s,%s,%s,'Active',%s)
        """, (job_title, description, location_type, salary_range,
              required_quals, deadline, contact_id))
    db.commit()

    flash('Job posting created.', 'success')
    return redirect(url_for('employers.my_postings'))


@bp.get('/employer/my-postings')
@require_role('Employer')
def my_postings():
    """List all job postings with application counts."""
    db = g.db
    with db.cursor() as cur:
        cur.execute("""
            SELECT jp.*,
                   ci.Company_Name, ci.Contact_Name,
                   (SELECT COUNT(*) FROM application_records ar
                    WHERE ar.PostingID = jp.PostingID) AS Application_Count
            FROM job_postings jp
            JOIN contact_information ci ON jp.ContactID = ci.ContactID
            ORDER BY jp.PostingID DESC
        """)
        postings = cur.fetchall()
    return render_template('employer/my_postings.html', postings=postings)


@bp.post('/employer/posting/<int:posting_id>/toggle')
@require_role('Employer')
def toggle_posting(posting_id):
    """Flip a posting's status between Active and Closed; returns JSON."""
    db = g.db
    with db.cursor() as cur:
        cur.execute("SELECT Posting_Status FROM job_postings WHERE PostingID=%s", (posting_id,))
        posting = cur.fetchone()
    if not posting:
        abort(404)

    new_status = 'Closed' if posting['Posting_Status'] == 'Active' else 'Active'
    with db.cursor() as cur:
        cur.execute(
            "UPDATE job_postings SET Posting_Status=%s WHERE PostingID=%s",
            (new_status, posting_id))
    db.commit()
    return jsonify(status=new_status)
