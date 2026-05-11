"""Advisor blueprint: student lookup, student detail (JSON), search."""
from flask import Blueprint, render_template, request, g, jsonify, abort
from app.functions import require_role

bp = Blueprint('advisors', __name__)


@bp.get('/advisor')
@require_role('Advisor')
def advisor_view():
    """Render the student lookup page (empty state)."""
    return render_template('advisor/advisor_view.html')


@bp.get('/advisor/search')
@require_role('Advisor')
def search_students():
    """Return JSON list of students matching query string ?q=."""
    q  = request.args.get('q', '').strip()
    db = g.db
    pattern = f'%{q}%'
    with db.cursor() as cur:
        cur.execute("""
            SELECT ProfileID, First_Name, Last_Name, Email, Major, Graduation_Year
            FROM user_profiles
            WHERE Role = 'Student'
              AND (CONCAT(First_Name,' ',Last_Name) LIKE %s
                   OR Email LIKE %s
                   OR First_Name LIKE %s
                   OR Last_Name LIKE %s)
            ORDER BY Last_Name, First_Name
            LIMIT 10
        """, (pattern, pattern, pattern, pattern))
        students = cur.fetchall()
    return jsonify(students)


@bp.get('/advisor/student/<int:student_id>')
@require_role('Advisor')
def student_detail(student_id):
    """Return JSON: student profile, application history, recommended postings."""
    db = g.db

    with db.cursor() as cur:
        cur.execute("""
            SELECT ProfileID, First_Name, Last_Name, Email, Major, Graduation_Year,
                   Skills, Location_Preference, Job_Type_Preference
            FROM user_profiles
            WHERE ProfileID = %s AND Role = 'Student'
        """, (student_id,))
        student = cur.fetchone()
    if not student:
        abort(404)

    with db.cursor() as cur:
        cur.execute("""
            SELECT ar.ApplicationID, ar.Source, ar.Status,
                   ar.Date_Applied, ar.Deadline, ar.Notes,
                   COALESCE(jp.Job_Title, 'N/A') AS Job_Title,
                   COALESCE(ci.Company_Name, ar.External_Company, 'N/A') AS Company_Name
            FROM application_records ar
            LEFT JOIN job_postings jp ON ar.PostingID = jp.PostingID
            LEFT JOIN contact_information ci ON jp.ContactID = ci.ContactID
            WHERE ar.ProfileID = %s
            ORDER BY ar.Date_Applied DESC
        """, (student_id,))
        applications = cur.fetchall()

    with db.cursor() as cur:
        cur.execute("""
            SELECT jp.PostingID, jp.Job_Title, jp.Location_Type,
                   jp.Salary_Range, jp.Match_Score, ci.Company_Name
            FROM job_postings jp
            JOIN contact_information ci ON jp.ContactID = ci.ContactID
            WHERE jp.Posting_Status = 'Active'
            ORDER BY jp.Match_Score DESC
        """)
        postings = cur.fetchall()

    # Serialize dates for JSON
    for row in applications:
        for key in ('Date_Applied', 'Deadline'):
            val = row.get(key)
            row[key] = val.isoformat() if val and hasattr(val, 'isoformat') else (str(val) if val else None)

    stats = {
        'total':        len(applications),
        'active':       sum(1 for a in applications if a['Status'] in ('Applied', 'Interviewing')),
        'interviewing': sum(1 for a in applications if a['Status'] == 'Interviewing'),
        'offered':      sum(1 for a in applications if a['Status'] == 'Offered'),
    }

    return jsonify(student=student, applications=applications,
                   postings=postings, stats=stats)
