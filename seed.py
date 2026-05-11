#!/usr/bin/env python3
"""Seed the AMH database with sample data. Run: python seed.py"""
import os
import pymysql
import pymysql.cursors
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    url = os.getenv('JAWSDB_URL')
    if not url:
        raise ValueError("JAWSDB_URL not set in .env")
    p = urlparse(url)
    return pymysql.connect(
        host=p.hostname,
        user=p.username,
        password=p.password,
        database=p.path.lstrip('/'),
        port=p.port or 3306,
        cursorclass=pymysql.cursors.DictCursor
    )


def seed():
    conn = get_connection()
    pw = generate_password_hash('password123')

    with conn.cursor() as cur:
        # Clear existing data in dependency order
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in ['notifications', 'documents', 'application_records',
                      'job_postings', 'contact_information', 'user_profiles']:
            cur.execute(f"TRUNCATE TABLE {table}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")

        # --- Users ---
        users = [
            ('Tucker', 'Balch', 'tucker.balch@bobcats.gcsu.edu', pw, 'Student',
             'Marketing', 2026, None, None, None, None),
            ('Thomas', 'Cupolo', 'thomas.cupolo@bobcats.gcsu.edu', pw, 'Student',
             'MIS', 2027, None, None, None, None),
            ('Tyler', 'Hill', 'william.hill@bobcats.gcsu.edu', pw, 'Student',
             'MIS', 2026, 'SQL,Python,Tableau,Power BI,Process Mining', None, None, None),
            ('Daniela', 'Pittman', 'daniella.pittman@gcsu.edu', pw, 'Advisor',
             None, None, None, None, None, 'Career Center'),
            ('Stephen', 'Surles', 'stephen.surles@gcsu.edu', pw, 'Employer',
             None, None, None, None, None, None),
        ]
        cur.executemany("""
            INSERT INTO user_profiles
                (First_Name, Last_Name, Email, Password_Hash, Role,
                 Major, Graduation_Year, Skills, Location_Preference,
                 Job_Type_Preference, Department)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, users)

        # --- Contacts ---
        contacts = [
            ('Lockheed Martin', 'James Walker', 'jwalk@lockheed.com', '321-555-0101'),
            ('Deloitte', 'Rachel Kim', 'rkim@deloitte.com', '404-555-0192'),
            ('MITRE Corporation', 'David Chen', 'dchen@mitre.com', '703-555-0148'),
            ('IBM', 'Laura Scott', 'lscott@ibm.com', '512-555-0177'),
            ('Booz Allen Hamilton', 'Marcus Hill', 'marcushill@boozallen.com', '571-555-0163'),
        ]
        cur.executemany("""
            INSERT INTO contact_information (Company_Name, Contact_Name, Contact_Email, Contact_Phone)
            VALUES (%s,%s,%s,%s)
        """, contacts)

        # --- Job Postings (ContactIDs 1–5) ---
        postings = [
            ('Systems Analyst',
             'Analyze and design information systems for enterprise clients.',
             'Hybrid', '$65,000–$80,000',
             'Bachelor\'s in MIS or CS; SQL; systems documentation experience',
             '2026-05-31', 'Active', 10, 1),
            ('Business Analyst',
             'Bridge business needs and technology solutions for Deloitte clients.',
             'Remote', '$70,000–$85,000',
             'Bachelor\'s in Business or MIS; process modeling; Agile methodology',
             '2026-06-15', 'Active', 20, 2),
            ('IT Project Manager',
             'Lead technology projects for government and defense clients at MITRE.',
             'In-Person', '$80,000–$95,000',
             'PMP certification preferred; 2+ years project management; security clearance eligible',
             '2026-06-01', 'Active', 15, 3),
            ('Data Analyst',
             'Transform raw data into actionable insights for IBM enterprise clients.',
             'Hybrid', '$60,000–$75,000',
             'Python or R; SQL; Tableau or Power BI; statistics background',
             '2026-05-15', 'Closed', 30, 4),
            ('Junior Developer',
             'Build and maintain web applications for Booz Allen Hamilton clients.',
             'Remote', '$55,000–$70,000',
             'Python or Java; REST APIs; Git; Agile team experience a plus',
             '2026-06-30', 'Active', 5, 5),
        ]
        cur.executemany("""
            INSERT INTO job_postings
                (Job_Title, Description, Location_Type, Salary_Range,
                 Required_Qualifications, Application_Deadline, Posting_Status,
                 Match_Score, ContactID)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, postings)

        # --- Applications ---
        # Tucker (ProfileID 1): Apps 1, 2, 3
        # Thomas (ProfileID 2): Apps 4, 5, 6
        applications = [
            ('Internal', 'Applied',      '2026-04-15', '2026-05-13', None, None,          1, 1),
            ('External', 'Interviewing', '2026-04-10', '2026-05-15', None, 'Deloitte',    1, None),
            ('External', 'Rejected',     '2026-03-28', '2026-05-07', None, 'IBM',         1, None),
            ('Internal', 'Offered',      '2026-04-01', '2026-05-14', None, None,          2, 3),
            ('External', 'Rejected',     '2026-03-28', '2026-05-07', None, 'Google',      2, None),
            ('Internal', 'Applied',      '2026-04-20', '2026-05-29', None, None,          2, 5),
        ]
        cur.executemany("""
            INSERT INTO application_records
                (Source, Status, Date_Applied, Deadline, Notes, External_Company, ProfileID, PostingID)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, applications)

        # --- Documents ---
        # AppIDs are 1-indexed matching insert order above
        documents = [
            ('Resume',       1, 'Resume_Lockheed',     '2026-04-14 09:00:00', 1, 1),
            ('Cover Letter', 1, 'CoverLetter_Lockheed','2026-04-14 09:05:00', 1, 1),
            ('Resume',       2, 'Resume_Deloitte',     '2026-04-09 14:00:00', 2, 1),
            ('Resume',       1, 'Resume_MITRE',        '2026-03-31 10:00:00', 4, 2),
            ('Cover Letter', 1, 'CoverLetter_Booz',    '2026-04-19 11:00:00', 6, 2),
        ]
        cur.executemany("""
            INSERT INTO documents
                (Document_Type, Version_Number, File_Label, Upload_Date, ApplicationID, ProfileID)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, documents)

        # --- Notifications ---
        notifications = [
            ('Deadline Reminder', 'In-Platform',   '2026-04-12 08:00:00', True,  1, 1),
            ('Status Change',     'Calendar Sync', '2026-04-11 10:00:00', True,  1, 2),
            ('Deadline Reminder', 'In-Platform',   '2026-03-29 08:00:00', False, 2, 4),
            ('Status Change',     'In-Platform',   '2026-03-30 09:00:00', True,  2, 5),
            ('Deadline Reminder', 'Calendar Sync', '2026-04-18 08:00:00', False, 2, 6),
        ]
        cur.executemany("""
            INSERT INTO notifications
                (Notification_Type, Delivery_Method, Sent_Date, Acknowledged, ProfileID, ApplicationID)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, notifications)

    conn.commit()
    conn.close()
    print("Database seeded successfully.")
    print("\nTest accounts (password: password123):")
    print("  Student:  tucker.balch@bobcats.gcsu.edu")
    print("  Student:  thomas.cupolo@bobcats.gcsu.edu")
    print("  Student:  william.hill@bobcats.gcsu.edu")
    print("  Advisor:  daniella.pittman@gcsu.edu")
    print("  Employer: stephen.surles@gcsu.edu")


if __name__ == '__main__':
    seed()
