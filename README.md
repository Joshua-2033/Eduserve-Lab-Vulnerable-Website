# Eduserve — Student Portal & Cybersecurity Lab

Independent locally hosted cybersecurity training project with fictional academic records. This is not the official Karunya Eduserve system.

## Start locally

1. Create a Python virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env`; set unique private passwords for all four accounts and a random `FLASK_SECRET_KEY`.
3. Run `python -m database.init_db`, then `python app.py`.
4. Open http://127.0.0.1:5000. Stop with Ctrl+C.

Read `ASSESSMENT_README.md` for the student brief and investigation clues. Read `REMEDIATION.md` for remediation mode. The instructor reference is separate. Vulnerable mode is localhost-only; do not use real credentials/data or expose the app to a network.
