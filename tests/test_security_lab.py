"""Self-contained integration tests for Eduserve's local training modes.

These tests create their own temporary SQLite database and test-only passwords.
They never read, change, or require the owner's .env credentials or lab database.
"""
from __future__ import annotations

import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash
from app import app

ROOT = Path(__file__).resolve().parents[1]


class EduserveIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory(prefix="eduserve-tests-")
        cls.db_path = str(Path(cls.tempdir.name) / "test.sqlite3")
        cls.original_db = app.config.get("DATABASE")
        cls.original_mode = app.config.get("LAB_MODE", "vulnerable")
        cls.original_secret = app.config.get("SECRET_KEY")
        cls.test_password = secrets.token_urlsafe(24)
        cls.accounts = {
            "joshua@karunya.edu.in": ("student", "Joshua Mathew", "DSC-23-041"),
            "sabari@karunya.edu.in": ("student", "Sabari Kumar", "DSC-23-057"),
            "nithin@karunya.edu.in": ("student", "Nithin Raj", "DSC-23-063"),
            "admin@karunya.edu": ("admin", "Eduserve Academic Administrator", None),
        }
        app.config.update(TESTING=True, DATABASE=cls.db_path, SECRET_KEY=secrets.token_hex(32), LAB_MODE="vulnerable")
        cls._make_database()

    @classmethod
    def _make_database(cls):
        db = sqlite3.connect(cls.db_path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript((ROOT / "database" / "schema.sql").read_text(encoding="utf-8"))
        user_ids = {}
        for email, (role, display_name, registration) in cls.accounts.items():
            cur = db.execute(
                "INSERT INTO users(email,password_hash,role,display_name) VALUES(?,?,?,?)",
                (email, generate_password_hash(cls.test_password), role, display_name),
            )
            user_ids[email] = cur.lastrowid
            if role == "student":
                details = {
                    "joshua@karunya.edu.in": ("B.Tech Computer Science and Engineering", "Data Science and Cyber Security", 4, "+91-90000-10041", "Coimbatore, Tamil Nadu", "2004-02-14"),
                    "sabari@karunya.edu.in": ("B.Tech Computer Science and Engineering", "Data Science and Cyber Security", 4, "+91-90000-10057", "Coimbatore, Tamil Nadu", "2004-06-09"),
                    "nithin@karunya.edu.in": ("B.Tech Information Technology", "Computer Science and Technology", 4, "+91-90000-10063", "Coimbatore, Tamil Nadu", "2004-09-21"),
                }[email]
                db.execute(
                    "INSERT INTO student_profiles(user_id,registration_no,programme,department,year_of_study,phone,address,date_of_birth) VALUES(?,?,?,?,?,?,?,?)",
                    (cur.lastrowid, registration, *details),
                )
        current_term = db.execute(
            "INSERT INTO academic_terms(name,starts_on,ends_on,is_current) VALUES(?,?,?,1)",
            ("Odd Semester 2026–27", "2026-06-15", "2026-11-20"),
        ).lastrowid
        historical_term = db.execute(
            "INSERT INTO academic_terms(name,starts_on,ends_on,is_current) VALUES(?,?,?,0)",
            ("Even Semester 2024–25", "2025-01-06", "2025-05-16"),
        ).lastrowid
        courses = [
            ("23CS3012", "Web Application Security", "Cyber Security", 4),
            ("23CS3031", "Database Systems", "Computer Science", 4),
            ("23DC2046", "Agile Software Development", "Computer Science", 3),
        ]
        course_ids = {}
        for code, name, faculty, credits in courses:
            course_ids[code] = db.execute(
                "INSERT INTO courses(code,name,faculty,credits) VALUES(?,?,?,?)",
                (code, name, faculty, credits),
            ).lastrowid
        for email in list(cls.accounts)[:3]:
            uid = user_ids[email]
            offset = list(cls.accounts).index(email)
            db.execute(
                "INSERT INTO enrollments(student_id,course_id,term_id,status) VALUES(?,?,?,'enrolled')",
                (uid, course_ids["23CS3012"], current_term),
            )
            day = "2026-10-26" if offset == 0 else ("2026-10-24" if offset == 1 else "2026-10-22")
            codes = ("P", "P", "A", "U") if offset == 0 else (("A", "P", "M", "U") if offset == 1 else ("P", "P", "P", "P"))
            db.execute(
                "INSERT INTO attendance_records(student_id,term_id,course_id,class_date,assembly_status,hour1,hour2,hour3,hour4,note) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (uid, current_term, course_ids[courses[offset % len(courses)][0]], day,
                 "P" if offset != 1 else "A", *codes, "Synthetic test fixture"),
            )
            for assessment_type, date, marks in (("IA1", "2026-08-12", 31.0 + offset), ("IA2", "2026-09-14", 38.0 + offset)):
                exam_id = db.execute(
                    "INSERT INTO examinations(term_id,course_id,assessment_type,exam_date,max_marks) VALUES(?,?,?,?,50)",
                    (current_term, course_ids["23CS3012"], assessment_type, date),
                ).lastrowid
                db.execute(
                    "INSERT INTO assessment_results(student_id,examination_id,marks_obtained,status) VALUES(?,?,?,'Published')",
                    (uid, exam_id, marks),
                )
        db.execute(
            "INSERT INTO feedback_submissions(student_id,category,subject,message,status) VALUES(?,?,?,?,?)",
            (user_ids["sabari@karunya.edu.in"], "Course materials", "Sabari test feedback", "SABARI-FEEDBACK-CONTENT", "Received"),
        )
        db.commit()
        db.close()
        cls.user_ids = user_ids
        cls.current_term_id = current_term
        cls.historical_term_id = historical_term
        cls.course_ids = course_ids

    @classmethod
    def tearDownClass(cls):
        app.config.update(DATABASE=cls.original_db, LAB_MODE=cls.original_mode, SECRET_KEY=cls.original_secret, TESTING=False)
        cls.tempdir.cleanup()

    def setUp(self):
        app.config["LAB_MODE"] = "vulnerable"
        self.client = app.test_client()

    def login(self, email="joshua@karunya.edu.in"):
        response = self.client.post("/login", data={"email": email, "password": self.test_password}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        return response

    def test_database_initializer_seeds_synthetic_accounts_and_hashes_passwords(self):
        with tempfile.TemporaryDirectory(prefix="eduserve-init-test-") as tmp:
            db_path = str(Path(tmp) / "seeded.sqlite3")
            passwords = {
                "LAB_JOSHUA_PASSWORD": secrets.token_urlsafe(20),
                "LAB_SABARI_PASSWORD": secrets.token_urlsafe(20),
                "LAB_NITHIN_PASSWORD": secrets.token_urlsafe(20),
                "LAB_ADMIN_PASSWORD": secrets.token_urlsafe(20),
            }
            env = os.environ.copy()
            env.update(passwords)
            env["FLASK_SECRET_KEY"] = secrets.token_urlsafe(48)
            env["EDUSERVE_DATABASE"] = db_path
            result = subprocess.run(
                [sys.executable, "-m", "database.init_db"],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            with sqlite3.connect(db_path) as db:
                users = db.execute("SELECT email, role, password_hash FROM users").fetchall()
                self.assertEqual(len(users), 4)
                self.assertEqual(sum(role == "student" for _, role, _ in users), 3)
                self.assertEqual(sum(role == "admin" for _, role, _ in users), 1)
                password_by_email = {
                    "joshua@karunya.edu.in": passwords["LAB_JOSHUA_PASSWORD"],
                    "sabari@karunya.edu.in": passwords["LAB_SABARI_PASSWORD"],
                    "nithin@karunya.edu.in": passwords["LAB_NITHIN_PASSWORD"],
                    "admin@karunya.edu": passwords["LAB_ADMIN_PASSWORD"],
                }
                for email, _role, password_hash in users:
                    self.assertNotEqual(password_hash, password_by_email[email])
                    self.assertTrue(check_password_hash(password_hash, password_by_email[email]))
                self.assertEqual(db.execute("SELECT COUNT(*) FROM student_profiles").fetchone()[0], 3)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM attendance_records").fetchone()[0], 54)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0], 15)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM assessment_results").fetchone()[0], 30)

    def test_database_initializer_rejects_duplicate_passwords_before_creating_database(self):
        with tempfile.TemporaryDirectory(prefix="eduserve-duplicate-password-test-") as tmp:
            db_path = str(Path(tmp) / "must-not-exist.sqlite3")
            repeated = secrets.token_urlsafe(20)
            env = os.environ.copy()
            env.update({
                "FLASK_SECRET_KEY": secrets.token_urlsafe(48),
                "LAB_JOSHUA_PASSWORD": repeated,
                "LAB_SABARI_PASSWORD": repeated,
                "LAB_NITHIN_PASSWORD": secrets.token_urlsafe(20),
                "LAB_ADMIN_PASSWORD": secrets.token_urlsafe(20),
                "EDUSERVE_DATABASE": db_path,
            })
            result = subprocess.run(
                [sys.executable, "-m", "database.init_db"],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("must be unique", result.stderr)
            self.assertFalse(Path(db_path).exists())

    def test_topbar_has_notifications_and_role_appropriate_actions(self):
        self.login()
        student_home = self.client.get("/dashboard")
        self.assertIn(b"Upcoming assessments", student_home.data)
        self.assertIn(b"profile-menu", student_home.data)
        self.assertIn(b"Course Registration", student_home.data)

        admin = app.test_client()
        admin.post("/login", data={
            "email": "admin@karunya.edu", "password": self.test_password,
        }, follow_redirects=True)
        admin_home = admin.get("/dashboard")
        self.assertIn(b"Administration", admin_home.data)
        self.assertNotIn(b"Course Registration", admin_home.data)

    def test_login_dashboard_and_class_views(self):
        response = self.login()
        self.assertIn(b"Joshua Mathew", response.data)
        self.assertIn(b"Class attendance", response.data)
        for path in ("/classes/calendar", "/classes/assembly-attendance", "/classes/course-attendance", "/classes/timetable"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_invalid_login_is_rejected(self):
        response = self.client.post("/login", data={"email": "joshua@karunya.edu.in", "password": "incorrect"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"not recognized", response.data)

    def test_every_seeded_role_can_authenticate(self):
        for email in self.accounts:
            with self.subTest(email=email):
                client = app.test_client()
                response = client.post("/login", data={"email": email, "password": self.test_password}, follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Eduserve", response.data)

    def test_attendance_percentage_matches_stored_periods(self):
        self.login()
        response = self.client.get(f"/classes/attendance?term={self.current_term_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"66.7", response.data)
        self.assertIn(b"Recorded hours", response.data)

    def test_cross_student_resources_are_accessible_in_vulnerable_mode(self):
        self.login()
        self.assertIn(b"DSC-23-057", self.client.get("/profile?student_id=2").data)
        self.assertIn(b"23CS3031", self.client.get("/classes/attendance?student_id=2").data)
        results = self.client.get("/student/2/results")
        self.assertEqual(results.status_code, 200)
        self.assertIn(b"39.0", results.data)

    def test_cross_student_resources_are_blocked_in_patched_mode(self):
        self.login()
        app.config["LAB_MODE"] = "patched"
        for path in ("/profile?student_id=2", "/classes/attendance?student_id=2", "/student/2/results"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_admin_feedback_role_check_is_missing_only_in_vulnerable_mode(self):
        self.login()
        response = self.client.get("/admin/feedback")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SABARI-FEEDBACK-CONTENT", response.data)
        app.config["LAB_MODE"] = "patched"
        self.assertEqual(self.client.get("/admin/feedback").status_code, 403)
        self.assertEqual(self.client.get("/admin").status_code, 403)

    def test_boolean_sql_injection_changes_course_search_results_in_vulnerable_mode(self):
        self.login()
        vulnerable = self.client.get("/search?q=%27%20OR%201%3D1%20--")
        self.assertEqual(vulnerable.status_code, 200)
        self.assertIn(b"Web Application Security", vulnerable.data)
        app.config["LAB_MODE"] = "patched"
        patched = self.client.get("/search?q=%27%20OR%201%3D1%20--")
        self.assertEqual(patched.status_code, 200)
        self.assertNotIn(b"Web Application Security", patched.data)

    def test_feedback_is_persisted_and_html_is_interpreted_only_in_vulnerable_mode(self):
        self.login()
        marker = "<b>EDUSERVE-TEST-MARKER</b>"
        post = self.client.post("/classes/feedback", data={"category":"Other", "subject":"Output test", "message":marker}, follow_redirects=True)
        self.assertEqual(post.status_code, 200)
        self.assertIn(b"Output test", post.data)
        admin = app.test_client()
        admin.post("/login", data={"email":"admin@karunya.edu", "password":self.test_password}, follow_redirects=True)
        vulnerable = admin.get("/admin/feedback")
        self.assertIn(marker.encode(), vulnerable.data)
        app.config["LAB_MODE"] = "patched"
        patched = admin.get("/admin/feedback")
        self.assertNotIn(marker.encode(), patched.data)
        self.assertIn(b"&lt;b&gt;EDUSERVE-TEST-MARKER&lt;/b&gt;", patched.data)

    def test_historical_course_registration_persists_only_in_vulnerable_mode(self):
        self.login()
        course = self.course_ids["23CS3031"]
        payload = {"course_id":str(course), "term_id":str(self.historical_term_id)}
        vulnerable = self.client.post("/course-registration", data=payload, follow_redirects=True)
        self.assertEqual(vulnerable.status_code, 200)
        db = sqlite3.connect(self.db_path)
        count = db.execute("SELECT COUNT(*) FROM enrollments WHERE student_id=1 AND course_id=? AND term_id=?", (course, self.historical_term_id)).fetchone()[0]
        db.close()
        self.assertEqual(count, 1)
        db = sqlite3.connect(self.db_path)
        db.execute("DELETE FROM enrollments WHERE student_id=1 AND course_id=? AND term_id=?", (course, self.historical_term_id))
        db.commit()
        db.close()
        app.config["LAB_MODE"] = "patched"
        blocked_client = app.test_client()
        blocked_client.post("/login", data={"email":"joshua@karunya.edu.in", "password":self.test_password}, follow_redirects=True)
        blocked_client.post("/course-registration", data=payload, follow_redirects=True)
        db = sqlite3.connect(self.db_path)
        count_after = db.execute("SELECT COUNT(*) FROM enrollments WHERE student_id=1 AND course_id=? AND term_id=?", (course, self.historical_term_id)).fetchone()[0]
        db.close()
        self.assertEqual(count_after, 0)

    def test_admin_can_review_and_update_feedback(self):
        self.login("admin@karunya.edu")
        self.assertEqual(self.client.get("/admin").status_code, 200)
        response = self.client.post("/admin/feedback/1/status", data={"status":"Resolved"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        db = sqlite3.connect(self.db_path)
        status = db.execute("SELECT status FROM feedback_submissions WHERE id=1").fetchone()[0]
        db.close()
        self.assertEqual(status, "Resolved")

    def test_logout_invalidates_authenticated_cookie(self):
        self.login()
        self.assertEqual(self.client.get("/dashboard").status_code, 200)
        self.assertEqual(self.client.post("/logout", follow_redirects=True).status_code, 200)
        self.assertIn(b"Sign In to Student Portal", self.client.get("/login").data)
        self.assertNotEqual(self.client.get("/dashboard").status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
