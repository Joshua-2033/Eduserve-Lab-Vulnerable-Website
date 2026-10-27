PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('student','admin')),
 display_name TEXT NOT NULL,
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS student_profiles (
 user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 registration_no TEXT NOT NULL UNIQUE,
 programme TEXT NOT NULL,
 department TEXT NOT NULL,
 year_of_study INTEGER NOT NULL,
 phone TEXT NOT NULL,
 address TEXT NOT NULL,
 date_of_birth TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS academic_terms (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE,
 starts_on TEXT NOT NULL,
 ends_on TEXT NOT NULL,
 is_current INTEGER NOT NULL DEFAULT 0 CHECK(is_current IN (0,1))
);
CREATE TABLE IF NOT EXISTS courses (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 code TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 faculty TEXT NOT NULL,
 credits INTEGER NOT NULL DEFAULT 3 CHECK(credits > 0)
);
CREATE TABLE IF NOT EXISTS enrollments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 course_id INTEGER NOT NULL REFERENCES courses(id),
 term_id INTEGER NOT NULL REFERENCES academic_terms(id),
 status TEXT NOT NULL DEFAULT 'enrolled' CHECK(status IN ('enrolled','withdrawn','completed')),
 enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(student_id, course_id, term_id)
);
CREATE TABLE IF NOT EXISTS attendance_records (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 term_id INTEGER NOT NULL REFERENCES academic_terms(id),
 course_id INTEGER REFERENCES courses(id),
 class_date TEXT NOT NULL,
 assembly_status TEXT NOT NULL CHECK(assembly_status IN ('P','A','U','M','-')),
 hour1 TEXT NOT NULL CHECK(hour1 IN ('P','A','U','M','-')),
 hour2 TEXT NOT NULL CHECK(hour2 IN ('P','A','U','M','-')),
 hour3 TEXT NOT NULL CHECK(hour3 IN ('P','A','U','M','-')),
 hour4 TEXT NOT NULL CHECK(hour4 IN ('P','A','U','M','-')),
 note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_attendance_student_term ON attendance_records(student_id, term_id, class_date);
CREATE TABLE IF NOT EXISTS examinations (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 term_id INTEGER NOT NULL REFERENCES academic_terms(id),
 course_id INTEGER NOT NULL REFERENCES courses(id),
 assessment_type TEXT NOT NULL CHECK(assessment_type IN ('IA1','IA2','End Semester')),
 exam_date TEXT NOT NULL,
 max_marks INTEGER NOT NULL DEFAULT 50 CHECK(max_marks > 0)
);
CREATE TABLE IF NOT EXISTS assessment_results (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 examination_id INTEGER NOT NULL REFERENCES examinations(id) ON DELETE CASCADE,
 marks_obtained REAL NOT NULL CHECK(marks_obtained >= 0),
 status TEXT NOT NULL DEFAULT 'Published' CHECK(status IN ('Published','Pending')),
 UNIQUE(student_id, examination_id)
);
CREATE INDEX IF NOT EXISTS idx_results_student ON assessment_results(student_id, examination_id);
CREATE TABLE IF NOT EXISTS feedback_submissions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 category TEXT NOT NULL,
 subject TEXT NOT NULL,
 message TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'Received' CHECK(status IN ('Received','Under review','Resolved')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
