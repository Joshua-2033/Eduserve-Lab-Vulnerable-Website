# Eduserve — Functional Student Portal & Cybersecurity Assessment Lab

Eduserve is a locally hosted Flask/SQLite training application for authorized web application security assessment. It uses fictional students and synthetic academic records. **It is not the official Karunya Institute of Technology and Sciences portal**, is not operated by the university, and does not connect to university services or APIs. The visual direction is university-inspired; the mark is an original text treatment, not an official university logo.

The default `vulnerable` lab mode intentionally contains selected implementation mistakes for hands-on assessment. Use it only on your own machine and only with the seeded synthetic records. Do not expose it to a LAN or the public internet.

## Features

- Local password authentication and role-specific student/admin accounts.
- Student dashboard and profile; class timetable and date calendar; term-filtered class, assembly, and course-wise attendance with database-derived summaries; IA1/IA2 results; upcoming assessments; feedback form/history; fees, leave, hostel, and course registration views.
- SQLite persistence, hashed passwords, foreign-key constraints, and synthetic records for three students.
- Admin overview and feedback status workflow.
- Security assessment routes for object-level authorization, role enforcement, input/query handling, stored output handling, and business-state validation.
- `EDUSERVE_LAB_MODE=vulnerable` (default) and `EDUSERVE_LAB_MODE=patched` to compare selected vulnerable behavior with defensive controls.

## Local setup (Linux)

Python 3.10+ is recommended. From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Edit `.env`. Set `FLASK_SECRET_KEY` to the generated random value and set four unique passwords (at least 12 characters) for `LAB_JOSHUA_PASSWORD`, `LAB_SABARI_PASSWORD`, `LAB_NITHIN_PASSWORD`, and `LAB_ADMIN_PASSWORD`. Do not reuse real university, Google, or personal passwords. Never commit `.env`.

Initialize the database once:

```bash
python -m database.init_db
```

Start the application:

```bash
python app.py
```

Open http://127.0.0.1:5000. Health check: http://127.0.0.1:5000/health. Stop with `Ctrl+C`. The app explicitly binds to `127.0.0.1`; do not change this to `0.0.0.0`.

### Seeded account identifiers

Passwords are intentionally not printed or committed. Configure each locally in `.env` before database initialization.

| Role | Login identifier |
|---|---|
| Student | `joshua@karunya.edu.in` |
| Student | `sabari@karunya.edu.in` |
| Student | `nithin@karunya.edu.in` |
| Administrator | `admin@karunya.edu` |

The administrator display name is **Eduserve Academic Administrator**. The address is also shown under **Contact Administration**. An email address is not a credential and does not grant administrator privileges.

If a database already exists, the initializer will refuse to overwrite it. To deliberately reset all synthetic data, ensure `.env` has the intended passwords and run:

```bash
python scripts/reset_database.py
```

The reset script validates the local configuration first, keeps a timestamped backup of an existing database in `instance/`, then creates a fresh database. Review the backup policy before deleting any backup files. To remove the generated local database, backups, and virtual environment afterward: run `deactivate`, then `rm -rf .venv instance`. This leaves your `.env` file in place. To remove the local secrets too, run `rm -f .env` separately after confirming you no longer need them.

## Database overview

`database/schema.sql` defines `users`, `student_profiles`, `academic_terms`, `courses`, `enrollments`, `attendance_records`, `examinations`, `assessment_results`, and `feedback_submissions`. Relationships use foreign keys, status fields use `CHECK` constraints, and frequently filtered student/term relationships have indexes. Passwords are stored as Werkzeug password hashes, never plaintext. The database path defaults to `instance/eduserve.sqlite3`; `EDUSERVE_DATABASE` can override it for isolated testing.

Attendance summary values are calculated from the stored rows. Present percentage uses `P / (P + A)`; medical and unmarked hours are excluded from that denominator. A dash means no class was scheduled for that period.

## Authorized scope and tools

Scope is limited to the local instance at `http://127.0.0.1:5000` and the synthetic records seeded by this project. You may use browser developer tools, Burp Suite Community Edition, `curl`, and local route enumeration tools such as Gobuster or Feroxbuster. Configure tools to target only the local address. Do not scan public hosts, the real university portal, or unrelated systems.

Suggested process:

1. Map the application's routes and roles using ordinary navigation first.
2. Capture requests in Burp and compare requests made by the three seeded student accounts.
3. Record a hypothesis before changing a parameter or workflow state.
4. Save the request and response, response status, and relevant rendered behavior.
5. Confirm impact using only the synthetic records. Avoid destructive or high-volume tests.
6. Switch to patched mode and repeat the same request as a regression check.

## Progressive clue trail

These clues are intentionally broad and require students to test the running application. Keep instructor notes and remediation material outside any student-facing distribution.

### Challenge A — Academic record boundaries
- Hint 1: Related academic records may be retrieved through different application paths.
- Hint 2: Compare how the portal identifies the current account with how a requested record is selected.
- Hint 3: In Burp, compare an authenticated request for your own record with a request that refers to another seeded student. Check both response content and status.

### Challenge B — Administrative workflow boundaries
- Hint 1: Navigation options do not define the server's complete permission model.
- Hint 2: Some support pages can be reached directly rather than through a dashboard card.
- Hint 3: Use a student session and request the feedback review route directly; compare the result with the expected role policy.

### Challenge C — Catalogue search
- Hint 1: Trace a search term from the URL to the server-side query.
- Hint 2: Consider whether the query treats user input as data or as part of its expression.
- Hint 3: Compare a normal search with a carefully chosen boolean expression, and capture the actual response. Do not use destructive statements.

### Challenge D — Feedback display context
- Hint 1: User-submitted text may travel through storage before it is displayed elsewhere.
- Hint 2: Check whether a message is rendered in the same context as ordinary text.
- Hint 3: Submit a harmless HTML marker in your own feedback and inspect its rendering in the review workflow. Do not use external callbacks or steal data.

### Challenge E — Workflow state
- Hint 1: An operation may depend on the current academic term.
- Hint 2: Compare the term selector with the rules the server should enforce when saving a registration.
- Hint 3: Try registering a course in a past term using the normal form, then verify the row in the database. Reset the lab if needed.

## Evidence collection

For each finding, capture:

- Finding ID and short title; severity rationale; lab mode and timestamp.
- Preconditions and account role used (never include passwords or session cookies in a report).
- The raw HTTP request with cookies and secrets redacted, response status/headers/body, and a screenshot if useful.
- Expected behavior, observed behavior, and the synthetic-data impact.
- Reproduction steps, remediation, and retest evidence from patched mode.
- Clearly label unsuccessful hypotheses as **not confirmed**. Label observations without demonstrated impact as **informational**, not as vulnerabilities.

Do not fabricate tool output. Save Burp items or sanitized `curl` transcripts from your own run in a private evidence folder outside version control.

## Vulnerability report template

```text
Finding ID / Title:
Category and severity:
Affected route(s):
Lab mode / date:
Preconditions and role:
Expected behavior:
Observed behavior:
Reproduction steps:
Evidence (sanitized request/response and screenshot reference):
Impact demonstrated using synthetic data:
Root cause hypothesis:
Recommended remediation:
Retest steps and result:
Status: Confirmed / Not confirmed / Informational
```

## Run checks

The tests create their own temporary SQLite database and use a random test-only password, so they do not require your `.env` credentials or touch the lab database. With the virtual environment active, run either the focused test suite:

```bash
python -m unittest discover -s tests -v
```

Or run the static/schema checks followed by the integration suite:

```bash
python scripts/run_checks.py
```

A test result reflects only the checks actually run; it is not a certification that the application is secure.

## Troubleshooting

- **Initializer says passwords are missing or placeholders:** set all four `LAB_*_PASSWORD` values in `.env`, each at least 12 characters, and retry.
- **Database already exists:** use `python scripts/reset_database.py` only when you intend to delete and recreate all local records.
- **`ModuleNotFoundError`:** activate `.venv` and run `pip install -r requirements.txt`.
- **Port 5000 is busy:** stop the other local service or run `PORT=5050 python app.py`; then use `http://127.0.0.1:5050`.
- **Login fails after changing `.env`:** changing a password in `.env` does not change an existing database hash. Reset the database to seed the new values.
- **No results or attendance for a selected term:** verify the selected term and account. Data is intentionally synthetic and term-scoped.
- **Browser does not keep login:** confirm cookies are enabled and use the same localhost hostname consistently.

## Lab mode and remediation

`EDUSERVE_LAB_MODE=vulnerable` intentionally enables selected flaws. For a defensive comparison, change `.env` to `EDUSERVE_LAB_MODE=patched`, restart the server, and repeat the same test. After recording a confirmed behavior, repeat the same request in patched mode and compare the actual response and database state. Do not assume a control is effective without retesting it. This is a teaching patch set, **not a claim that the whole application is production secure**. Keep owner-side remediation notes separate from the student brief and rerun all checks after code changes.

## Repository privacy and student distribution

This is the owner-side project repository and contains intentionally vulnerable source code plus owner-only assessment and remediation notes. **Keep the owner repository private and do not grant students access to it while those files are present.** Prepare a separate student distribution containing the application and this assessment guide, but excluding INSTRUCTOR_NOTES.md and REMEDIATION.md. Do not publish an answer-key copy publicly. If the repository has previously been public, making it private prevents future unauthorised browsing but does not guarantee that old commits, cloned copies, or cached material disappear; review the repository history before using it for a graded assessment.
