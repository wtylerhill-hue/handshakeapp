"""Student blueprint: dashboard, applications, document library, notifications."""
from datetime import date, datetime, timedelta
from flask import (Blueprint, render_template, request, session,
                   redirect, url_for, flash, g, abort)
from app.functions import require_role

bp = Blueprint('students', __name__)


@bp.get('/dashboard')
@require_role('Student')
def dashboard():
    """Student dashboard: stats strip, application table, auto-generate deadline alerts."""
    db = g.db
    user_id = session['user_id']

    with db.cursor() as cur:
        cur.execute("""
            SELECT ar.*,
                   COALESCE(jp.Job_Title, 'N/A') AS Job_Title,
                   COALESCE(ci.Company_Name, ar.External_Company, 'N/A') AS Company_Name
            FROM application_records ar
            LEFT JOIN job_postings jp ON ar.PostingID = jp.PostingID
            LEFT JOIN contact_information ci ON jp.ContactID = ci.ContactID
            WHERE ar.ProfileID = %s
            ORDER BY ar.Date_Applied DESC
        """, (user_id,))
        applications = cur.fetchall()

    # Auto-generate deadline reminder notifications
    today     = date.today()
    threshold = today + timedelta(days=3)
    for app in applications:
        dl     = app.get('Deadline')
        status = app.get('Status')
        if dl and dl <= threshold and status not in ('Offered', 'Rejected'):
            with db.cursor() as cur:
                cur.execute("""
                    SELECT NotificationID FROM notifications
                    WHERE ApplicationID = %s
                      AND Notification_Type = 'Deadline Reminder'
                      AND Acknowledged = FALSE
                """, (app['ApplicationID'],))
                exists = cur.fetchone()
            if not exists:
                with db.cursor() as cur:
                    cur.execute("""
                        INSERT INTO notifications
                            (Notification_Type, Delivery_Method, Sent_Date, Acknowledged, ProfileID, ApplicationID)
                        VALUES ('Deadline Reminder','In-Platform',%s,FALSE,%s,%s)
                    """, (datetime.utcnow(), user_id, app['ApplicationID']))
    db.commit()

    stats = {
        'total':        len(applications),
        'active':       sum(1 for a in applications if a['Status'] in ('Applied', 'Interviewing')),
        'interviewing': sum(1 for a in applications if a['Status'] == 'Interviewing'),
        'offered':      sum(1 for a in applications if a['Status'] == 'Offered'),
    }

    return render_template('student/dashboard.html',
                           applications=applications,
                           stats=stats,
                           today=today,
                           threshold=threshold)


@bp.get('/application/new')
@require_role('Student')
def new_application():
    """Render blank application form."""
    db = g.db
    user_id = session['user_id']
    with db.cursor() as cur:
        cur.execute("""
            SELECT jp.PostingID,
                   CONCAT(ci.Company_Name, ' — ', jp.Job_Title) AS Label
            FROM job_postings jp
            JOIN contact_information ci ON jp.ContactID = ci.ContactID
            WHERE jp.Posting_Status = 'Active'
            ORDER BY ci.Company_Name
        """)
        postings = cur.fetchall()
        cur.execute("""
            SELECT DocumentID, File_Label, Document_Type
            FROM documents WHERE ProfileID = %s
            ORDER BY Upload_Date DESC
        """, (user_id,))
        documents = cur.fetchall()

    return render_template('student/application_form.html',
                           postings=postings, documents=documents,
                           app=None, edit=False)


@bp.post('/application/new')
@require_role('Student')
def create_application():
    """Save new application record."""
    db = g.db
    user_id = session['user_id']

    source           = request.form.get('source', '').strip()
    status           = request.form.get('status', '').strip()
    date_applied     = request.form.get('date_applied', '').strip()
    deadline         = request.form.get('deadline', '').strip() or None
    notes            = request.form.get('notes', '').strip() or None
    external_company = request.form.get('external_company', '').strip() or None
    posting_id       = request.form.get('posting_id', '').strip() or None

    if not all([source, status, date_applied]):
        flash('Source, status, and date applied are required.', 'error')
        return redirect(url_for('students.new_application'))

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO application_records
                (Source, Status, Date_Applied, Deadline, Notes,
                 External_Company, ProfileID, PostingID)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (source, status, date_applied, deadline, notes,
              external_company, user_id, posting_id))
        app_id = cur.lastrowid

    # Optionally link documents
    _link_document(db, request.form.get('resume_id'), app_id, user_id)
    _link_document(db, request.form.get('cover_letter_id'), app_id, user_id)
    db.commit()

    flash('Application added.', 'success')
    return redirect(url_for('students.dashboard'))


@bp.get('/application/<int:app_id>/edit')
@require_role('Student')
def edit_application(app_id):
    """Render pre-filled application edit form."""
    db = g.db
    user_id = session['user_id']

    with db.cursor() as cur:
        cur.execute("""
            SELECT * FROM application_records
            WHERE ApplicationID = %s AND ProfileID = %s
        """, (app_id, user_id))
        app = cur.fetchone()
    if not app:
        abort(404)

    with db.cursor() as cur:
        cur.execute("""
            SELECT jp.PostingID,
                   CONCAT(ci.Company_Name, ' — ', jp.Job_Title) AS Label
            FROM job_postings jp
            JOIN contact_information ci ON jp.ContactID = ci.ContactID
            WHERE jp.Posting_Status = 'Active'
            ORDER BY ci.Company_Name
        """)
        postings = cur.fetchall()
        cur.execute("""
            SELECT DocumentID, File_Label, Document_Type
            FROM documents WHERE ProfileID = %s
            ORDER BY Upload_Date DESC
        """, (user_id,))
        documents = cur.fetchall()

    return render_template('student/application_form.html',
                           postings=postings, documents=documents,
                           app=app, edit=True)


@bp.post('/application/<int:app_id>/edit')
@require_role('Student')
def update_application(app_id):
    """Update an existing application record."""
    db = g.db
    user_id = session['user_id']

    with db.cursor() as cur:
        cur.execute("""
            SELECT ApplicationID FROM application_records
            WHERE ApplicationID = %s AND ProfileID = %s
        """, (app_id, user_id))
        if not cur.fetchone():
            abort(404)

    source           = request.form.get('source', '').strip()
    status           = request.form.get('status', '').strip()
    date_applied     = request.form.get('date_applied', '').strip()
    deadline         = request.form.get('deadline', '').strip() or None
    notes            = request.form.get('notes', '').strip() or None
    external_company = request.form.get('external_company', '').strip() or None
    posting_id       = request.form.get('posting_id', '').strip() or None

    with db.cursor() as cur:
        cur.execute("""
            UPDATE application_records
            SET Source=%s, Status=%s, Date_Applied=%s, Deadline=%s,
                Notes=%s, External_Company=%s, PostingID=%s
            WHERE ApplicationID=%s AND ProfileID=%s
        """, (source, status, date_applied, deadline, notes,
              external_company, posting_id, app_id, user_id))
    db.commit()

    flash('Application updated.', 'success')
    return redirect(url_for('students.dashboard'))


@bp.post('/application/<int:app_id>/delete')
@require_role('Student')
def delete_application(app_id):
    """Delete an application and its related notifications."""
    db = g.db
    user_id = session['user_id']
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM notifications WHERE ApplicationID=%s AND ProfileID=%s",
            (app_id, user_id))
        cur.execute(
            "UPDATE documents SET ApplicationID=NULL WHERE ApplicationID=%s AND ProfileID=%s",
            (app_id, user_id))
        cur.execute(
            "DELETE FROM application_records WHERE ApplicationID=%s AND ProfileID=%s",
            (app_id, user_id))
    db.commit()
    flash('Application deleted.', 'success')
    return redirect(url_for('students.dashboard'))


@bp.get('/documents')
@require_role('Student')
def document_library():
    """Render document library with upload form and document table."""
    db = g.db
    user_id = session['user_id']
    with db.cursor() as cur:
        cur.execute("""
            SELECT d.*,
                   COALESCE(ci.Company_Name, ar.External_Company) AS Linked_Company
            FROM documents d
            LEFT JOIN application_records ar ON d.ApplicationID = ar.ApplicationID
            LEFT JOIN job_postings jp ON ar.PostingID = jp.PostingID
            LEFT JOIN contact_information ci ON jp.ContactID = ci.ContactID
            WHERE d.ProfileID = %s
            ORDER BY d.Upload_Date DESC
        """, (user_id,))
        documents = cur.fetchall()
    return render_template('student/document_library.html', documents=documents)


@bp.post('/documents/upload')
@require_role('Student')
def upload_document():
    """Create a new document record."""
    db = g.db
    user_id    = session['user_id']
    doc_type   = request.form.get('document_type', '').strip()
    file_label = request.form.get('file_label', '').strip()
    version_raw = request.form.get('version_number', '1').strip()

    if not doc_type or not file_label:
        flash('Document type and label are required.', 'error')
        return redirect(url_for('students.document_library'))

    version = int(version_raw) if version_raw.isdigit() else 1

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO documents (Document_Type, Version_Number, File_Label, Upload_Date, ProfileID)
            VALUES (%s,%s,%s,%s,%s)
        """, (doc_type, version, file_label, datetime.utcnow(), user_id))
    db.commit()
    flash('Document added.', 'success')
    return redirect(url_for('students.document_library'))


@bp.post('/documents/<int:doc_id>/delete')
@require_role('Student')
def delete_document(doc_id):
    """Delete a document record."""
    db = g.db
    user_id = session['user_id']
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM documents WHERE DocumentID=%s AND ProfileID=%s",
            (doc_id, user_id))
    db.commit()
    flash('Document deleted.', 'success')
    return redirect(url_for('students.document_library'))


@bp.post('/notifications/<int:notif_id>/acknowledge')
@require_role('Student')
def acknowledge_notification(notif_id):
    """Mark a notification acknowledged; returns 204 No Content."""
    db = g.db
    user_id = session['user_id']
    with db.cursor() as cur:
        cur.execute("""
            UPDATE notifications SET Acknowledged = TRUE
            WHERE NotificationID=%s AND ProfileID=%s
        """, (notif_id, user_id))
    db.commit()
    return '', 204


# ---- helpers ----

def _link_document(db, doc_id_raw, app_id, user_id):
    """Set ApplicationID on a document row if doc_id_raw is a valid int."""
    if not doc_id_raw or not str(doc_id_raw).isdigit():
        return
    with db.cursor() as cur:
        cur.execute("""
            UPDATE documents SET ApplicationID=%s
            WHERE DocumentID=%s AND ProfileID=%s
        """, (app_id, int(doc_id_raw), user_id))
