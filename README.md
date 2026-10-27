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

## Setup and operation (Linux)

Use the first-time procedure for a new checkout or a database that has not yet been created. For an already configured project, use **Restarting the application**; do not repeat initialization.

### 1. Create the Python environment and install dependencies

From the project root (the directory containing `app.py` and `requirements.txt`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run `python3 -m venv .venv` when creating the environment for the first time. On later launches, activate the existing environment with `source .venv/bin/activate`. Re-run the dependency installation if you recreate the environment or change `requirements.txt`.

### 2. Create `.env` and configure it **before database initialization**

Create the local configuration file once. Do not copy the example over an existing `.env`, because that would overwrite your settings.

```bash
if [ ! -f .env ]; then cp .env.example .env; else echo ".env already exists; leaving it unchanged."; fi
python -c "import secrets; print(secrets.token_urlsafe(48))"
nano .env
```

The second command prints a random secret; it does **not** edit the file. Copy its output into `FLASK_SECRET_KEY=` in `.env`, replacing the example value. Then replace all four password values with different passwords of at least 12 characters. Keep the setting names on the left of `=` unchanged.

```dotenv
FLASK_SECRET_KEY=PASTE_THE_GENERATED_SECRET_HERE
LAB_JOSHUA_PASSWORD=SET_A_UNIQUE_PASSWORD_AT_LEAST_12_CHARS
LAB_SABARI_PASSWORD=SET_A_DIFFERENT_PASSWORD_AT_LEAST_12_CHARS
LAB_NITHIN_PASSWORD=SET_ANOTHER_PASSWORD_AT_LEAST_12_CHARS
LAB_ADMIN_PASSWORD=SET_A_FOURTH_PASSWORD_AT_LEAST_12_CHARS
EDUSERVE_LAB_MODE=vulnerable
```

The values above are placeholders, not values to use literally. The four passwords must be unique and must not start with `change-this-`; the secret must be at least 32 characters and must not start with `replace-with-`. Save the file in Nano with `Ctrl+O`, `Enter`, then `Ctrl+X`.

**Important:** edit `.env` in the same project root as `app.py`. The website login uses email addresses as usernames, but those email addresses are not the password-setting names. The mapping is listed below.

### 3. Validate the configuration before creating the database

Run this from the project root with `.venv` active. It checks the effective configuration without printing the secret or any password.

```bash
python - <<'PY'
import os
from dotenv import load_dotenv

load_dotenv(".env")
keys = [
    "LAB_JOSHUA_PASSWORD", "LAB_SABARI_PASSWORD",
    "LAB_NITHIN_PASSWORD", "LAB_ADMIN_PASSWORD",
]
passwords = [os.getenv(k, "") for k in keys]
problems = [k for k, p in zip(keys, passwords)
            if len(p) < 12 or p.startswith("change-this-")]
if len(set(passwords)) != len(passwords):
    problems.append("Passwords must all be different")
secret = os.getenv("FLASK_SECRET_KEY", "")
if len(secret) < 32 or secret.startswith("replace-with-"):
    problems.append("FLASK_SECRET_KEY is missing or still a placeholder")
if problems:
    print("Fix these .env settings before continuing:")
    print("\n".join(f" - {p}" for p in problems))
    raise SystemExit(1)
print("Configuration check passed.")
PY
```

Do not continue until it prints `Configuration check passed.`. If it identifies a password setting, check its value in `.env`, save the file, and rerun this check.

### 4. Initialize the database **once for a new database**

Only after the configuration check passes:

```bash
python -m database.init_db
```

This creates `instance/eduserve.sqlite3`, seeds three fictional student accounts and one administrator, and stores password hashes. Do not run this command at every launch. If it says the database already exists, leave it in place and follow **Restarting the application** below. To recreate it intentionally, follow **Changing passwords or resetting the database**.

If the initializer reports missing or placeholder values for account identifiers, it is referring to the corresponding `.env` setting:

| Login identifier | Required setting in `.env` |
|---|---|
| `joshua@karunya.edu.in` | `LAB_JOSHUA_PASSWORD` |
| `sabari@karunya.edu.in` | `LAB_SABARI_PASSWORD` |
| `nithin@karunya.edu.in` | `LAB_NITHIN_PASSWORD` |
| `admin@karunya.edu` | `LAB_ADMIN_PASSWORD` |

That error means one or more effective values are missing, shorter than 12 characters, or still use the example prefix. Verify that you edited and saved the correct `.env` file and used the exact setting name. Run Step 3 again before retrying initialization.

### 5. Start the application

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The health endpoint is [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health). Keep the terminal running while you use the site; stop the server with `Ctrl+C`. By default it binds to `127.0.0.1`. Do not bind it to `0.0.0.0` or expose vulnerable mode to a network.

### Login identifiers

Use these identifiers on the website's login form. The corresponding passwords are the values you saved in `.env`; they are never printed or committed.

| Role | Login identifier | Password setting |
|---|---|---|
| Student | `joshua@karunya.edu.in` | `LAB_JOSHUA_PASSWORD` |
| Student | `sabari@karunya.edu.in` | `LAB_SABARI_PASSWORD` |
| Student | `nithin@karunya.edu.in` | `LAB_NITHIN_PASSWORD` |
| Administrator | `admin@karunya.edu` | `LAB_ADMIN_PASSWORD` |

The administrator display name is **Eduserve Academic Administrator**. Its email address is also visible in Contact Administration; the email itself does not grant administrator privileges.

## Restarting the application

For an already initialized project, open a terminal in the project root and run:

```bash
source .venv/bin/activate
python app.py
```

Then visit [http://127.0.0.1:5000](http://127.0.0.1:5000). Do **not** run `cp .env.example .env` or `python -m database.init_db` again. Your database and submitted feedback persist between restarts. If this is a new terminal, activate `.venv` there as well.

## Changing passwords or resetting the database

Editing a password in `.env` does **not** update its existing SQLite password hash. The configured passwords are applied when a database is initialized.

To apply new passwords or deliberately restore a clean lab:

1. Stop the server with `Ctrl+C`.
2. Edit and save `.env` as in Step 2; all four passwords must be different and at least 12 characters.
3. Run the configuration check in Step 3 and ensure it passes.
4. Run:

   ```bash
   python scripts/reset_database.py
   ```

5. Review the prompt. Type `RESET` only if you intend to replace the active database. The script creates a timestamped backup before recreating the database. Any other response cancels the reset.

The reset replaces active synthetic records and seeds new account password hashes from the current configuration. Review/manage the backup files in `instance/`. Do not run this script casually; it changes the active lab database.

To remove the local environment after use, stop the server, run `deactivate`, then `rm -rf .venv instance`. This leaves `.env` in place. To remove local secrets as well, separately run `rm -f .env` after confirming you no longer need them.

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
