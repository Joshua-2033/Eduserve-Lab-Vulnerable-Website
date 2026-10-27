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

## First-time setup and start (Linux)

Follow these steps **in order** from the project directory. The most important point is that the password values must be saved in the project's local `.env` file **before** the database is initialized.

### Step 1 — Open the project folder and create the Python environment

Open a terminal in the folder that contains `app.py`, `requirements.txt`, and `.env.example`. If you downloaded the ZIP, extract it first and open the extracted `Eduserve-Lab-Vulnerable-Website` folder.

Check that you are in the right place:

```bash
pwd
ls
```

Create and activate the virtual environment. Run the creation command only the first time; on later starts, just activate the existing environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

After activation, the terminal prompt normally begins with `.venv`. If `python3 -m venv .venv` says the environment already exists, that is fine—do not delete it just to continue.

### Step 2 — Create the local `.env` file once

The application reads configuration from `.env` in the project root. Create it only if it does not already exist:

```bash
if [ ! -f .env ]; then cp .env.example .env; else echo ".env already exists; keeping it unchanged."; fi
```

**Do not repeatedly copy `.env.example` over an existing `.env`.** Doing so would overwrite the configuration you already entered. The `.env` file is local configuration and must not be committed to GitHub.

### Step 3 — Set the secret key and all four passwords

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

This command only **prints** a secret; it does not put it into `.env` automatically. Copy the output, then open the configuration file:

```bash
nano .env
```

Find the five settings below and replace their example values with your own values. Keep the setting names exactly as written on the left of `=`.

```dotenv
FLASK_SECRET_KEY=paste_the_generated_secret_here
LAB_JOSHUA_PASSWORD=choose_a_unique_password_at_least_12_chars
LAB_SABARI_PASSWORD=choose_a_different_unique_password_at_least_12_chars
LAB_NITHIN_PASSWORD=choose_another_unique_password_at_least_12_chars
LAB_ADMIN_PASSWORD=choose_a_fourth_unique_password_at_least_12_chars
EDUSERVE_LAB_MODE=vulnerable
```

These are examples of the **format**, not passwords to use literally. Replace each example value. All four passwords must be at least 12 characters, must be different from one another, and must not begin with the example prefix `change-this-`. Set `FLASK_SECRET_KEY` to the generated output (at least 32 characters), not the example placeholder.

Do not put the account email addresses in place of the setting names. The emails are the login identifiers used **inside the website**; they are not the environment-variable names or the passwords.

Save and close Nano with `Ctrl+O`, press `Enter`, then `Ctrl+X`.

### Step 4 — Check the configuration before initializing the database

Run this check from the project directory, with the virtual environment active. It reports whether a setting needs attention without printing any password or the secret key:

```bash
python - <<'PY'
from dotenv import dotenv_values

cfg = dotenv_values(".env")
password_keys = [
    "LAB_JOSHUA_PASSWORD",
    "LAB_SABARI_PASSWORD",
    "LAB_NITHIN_PASSWORD",
    "LAB_ADMIN_PASSWORD",
]
passwords = [cfg.get(key) or "" for key in password_keys]
secret = cfg.get("FLASK_SECRET_KEY") or ""

problems = []
for key, value in zip(password_keys, passwords):
    if len(value) < 12 or value.startswith("change-this-"):
        problems.append(f"{key}: missing, placeholder, or shorter than 12 characters")

if len(set(passwords)) != len(passwords):
    problems.append("The four passwords must all be different")

if len(secret) < 32 or secret.startswith("replace-with-"):
    problems.append("FLASK_SECRET_KEY: missing, placeholder, or shorter than 32 characters")

if problems:
    print("Configuration needs attention:")
    for problem in problems:
        print(" - " + problem)
    raise SystemExit(1)

print("Configuration check passed. No secrets were displayed.")
PY
```

Do not continue until the check says `Configuration check passed`. If it reports an issue, reopen `.env` and correct the named setting.

### Step 5 — Initialize the database for the first time only

Only after Step 4 passes, run:

```bash
python -m database.init_db
```

This creates the local SQLite database, seeds three fictional student accounts and one administrator, and stores password hashes. **You normally run this command once per fresh database—not every time you start the website.**

If it reports `Missing/placeholder values for: joshua@karunya.edu.in` (or another account), the initializer has not received a valid value for that account's corresponding setting:

- `joshua@karunya.edu.in` → `LAB_JOSHUA_PASSWORD`
- `sabari@karunya.edu.in` → `LAB_SABARI_PASSWORD`
- `nithin@karunya.edu.in` → `LAB_NITHIN_PASSWORD`
- `admin@karunya.edu` → `LAB_ADMIN_PASSWORD`

That message means the setting in `.env` is missing, still an example value, or too short. Check that you edited the `.env` in the same project folder, saved the file, and used the exact setting names shown in Step 3. Run Step 4 again before retrying initialization.

If the initializer says the database already exists, do not keep rerunning it. Follow **Restarting the application** below, or use **Changing passwords or resetting the database** if you intentionally need a fresh database.

### Step 6 — Start the website

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The health endpoint is [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health). Leave the terminal running while using the site. To stop the server, return to that terminal and press `Ctrl+C`.

The app binds to `127.0.0.1` by default. Do not change it to `0.0.0.0` or expose vulnerable mode to a network.

### Seeded account identifiers

Use these email addresses in the website's login form. The passwords are the four values you configured in `.env`; they are not printed or committed.

| Role | Login identifier | Password setting in `.env` |
|---|---|---|
| Student | `joshua@karunya.edu.in` | `LAB_JOSHUA_PASSWORD` |
| Student | `sabari@karunya.edu.in` | `LAB_SABARI_PASSWORD` |
| Student | `nithin@karunya.edu.in` | `LAB_NITHIN_PASSWORD` |
| Administrator | `admin@karunya.edu` | `LAB_ADMIN_PASSWORD` |

The administrator display name is **Eduserve Academic Administrator**. The address is also shown under **Contact Administration**. An email address is not a credential and does not grant administrator privileges.

## Restarting the application

Use these steps each time you want to run an **already initialized** copy of the project:

1. Open a terminal in the project folder (the folder containing `app.py`).
2. Activate the existing virtual environment.
3. Start the application. Do **not** copy `.env.example` again and do **not** run the database initializer again.

```bash
source .venv/bin/activate
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000). Stop it with `Ctrl+C`. Your database, enrolled courses, attendance, results, and feedback remain stored locally between restarts.

If you open a new terminal, activate `.venv` in that terminal before running the app. If you have not installed the dependencies in that environment yet, run `python -m pip install -r requirements.txt` once.

## Changing passwords or resetting the database

Changing a password in `.env` **does not change the password hash already stored in an existing database**. The new values are used when the database is freshly initialized.

If you want the new configured passwords to become the login passwords, or you deliberately want to restore a clean lab:

1. Stop the running application with `Ctrl+C`.
2. Edit and save `.env` as in Step 3. Keep all four passwords unique and at least 12 characters.
3. Run the configuration check in Step 4.
4. Run the reset script:

```bash
python scripts/reset_database.py
```

5. Read the confirmation prompt. Type `RESET` only if you intend to replace the current synthetic database. The script makes a timestamped backup before recreating the database. If you do not want to reset, type anything else to cancel.

Resetting removes the existing local lab data from the active database and seeds a fresh set of records using the currently configured passwords. Review and manage the backup files in `instance/` yourself. **Do not run the reset script casually**; it is destructive to the active database.

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
