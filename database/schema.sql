-- Handshake Application Management Hub — Database Schema
-- Run: mysql -h [host] -u [user] -p [database] < database/schema.sql

DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS application_records;
DROP TABLE IF EXISTS job_postings;
DROP TABLE IF EXISTS contact_information;
DROP TABLE IF EXISTS user_profiles;

CREATE TABLE user_profiles (
    ProfileID        INT AUTO_INCREMENT PRIMARY KEY,
    First_Name       VARCHAR(100) NOT NULL,
    Last_Name        VARCHAR(100) NOT NULL,
    Email            VARCHAR(255) UNIQUE NOT NULL,
    Password_Hash    VARCHAR(255) NOT NULL,
    Role             ENUM('Student','Advisor','Employer') NOT NULL,
    Major            VARCHAR(100),
    Graduation_Year  INT,
    Skills           TEXT,
    Location_Preference  VARCHAR(255),
    Job_Type_Preference  VARCHAR(255),
    Department       VARCHAR(100),
    Session_Token    VARCHAR(255),
    Last_Login       DATETIME
);

CREATE TABLE contact_information (
    ContactID        INT AUTO_INCREMENT PRIMARY KEY,
    Company_Name     VARCHAR(255) NOT NULL,
    Contact_Name     VARCHAR(255) NOT NULL,
    Contact_Email    VARCHAR(255) NOT NULL,
    Contact_Phone    VARCHAR(50)
);

CREATE TABLE job_postings (
    PostingID              INT AUTO_INCREMENT PRIMARY KEY,
    Job_Title              VARCHAR(255) NOT NULL,
    Description            TEXT NOT NULL,
    Location_Type          ENUM('Remote','Hybrid','In-Person') NOT NULL,
    Salary_Range           VARCHAR(100) NOT NULL,
    Required_Qualifications TEXT NOT NULL,
    Application_Deadline   DATE NOT NULL,
    Posting_Status         ENUM('Active','Closed') NOT NULL DEFAULT 'Active',
    Match_Score            INT DEFAULT 0,
    ContactID              INT NOT NULL,
    FOREIGN KEY (ContactID) REFERENCES contact_information(ContactID)
);

CREATE TABLE application_records (
    ApplicationID    INT AUTO_INCREMENT PRIMARY KEY,
    Source           ENUM('Internal','External') NOT NULL,
    Status           ENUM('Applied','Interviewing','Offered','Rejected') NOT NULL,
    Date_Applied     DATE NOT NULL,
    Deadline         DATE,
    Notes            TEXT,
    External_Company VARCHAR(255),
    ProfileID        INT NOT NULL,
    PostingID        INT,
    FOREIGN KEY (ProfileID) REFERENCES user_profiles(ProfileID),
    FOREIGN KEY (PostingID) REFERENCES job_postings(PostingID)
);

CREATE TABLE documents (
    DocumentID       INT AUTO_INCREMENT PRIMARY KEY,
    Document_Type    ENUM('Resume','Cover Letter','Other') NOT NULL,
    Version_Number   INT DEFAULT 1,
    File_Label       VARCHAR(255) NOT NULL,
    Upload_Date      DATETIME NOT NULL,
    ApplicationID    INT,
    ProfileID        INT NOT NULL,
    FOREIGN KEY (ApplicationID) REFERENCES application_records(ApplicationID),
    FOREIGN KEY (ProfileID) REFERENCES user_profiles(ProfileID)
);

CREATE TABLE notifications (
    NotificationID     INT AUTO_INCREMENT PRIMARY KEY,
    Notification_Type  ENUM('Deadline Reminder','Status Change') NOT NULL,
    Delivery_Method    ENUM('In-Platform','Calendar Sync') NOT NULL DEFAULT 'In-Platform',
    Sent_Date          DATETIME NOT NULL,
    Acknowledged       BOOLEAN NOT NULL DEFAULT FALSE,
    ProfileID          INT NOT NULL,
    ApplicationID      INT NOT NULL,
    FOREIGN KEY (ProfileID) REFERENCES user_profiles(ProfileID),
    FOREIGN KEY (ApplicationID) REFERENCES application_records(ApplicationID)
);
