# Eduserve — Cybersecurity Assessment Lab

This repository contains the complete locally hosted Eduserve student portal project archive. It is an independent cybersecurity training application inspired by university student portals and uses fictional data; it is not the official Karunya Eduserve system.

## Download the complete project

Download `Eduserve-Cybersecurity-Lab.zip` from this repository, then extract it. The ZIP contains the Flask application, SQLite schema and initialization, templates, CSS, JavaScript, tests, student assessment README, instructor notes, and remediation guide.

## Run locally

Inside the extracted `Eduserve/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and replace every example password and the secret key.
python -m database.init_db
python app.py
```

Open http://127.0.0.1:5000. Stop the server with Ctrl+C. Keep this deliberately vulnerable lab bound to localhost; do not expose it to the internet. Never put real university credentials or student data into it.

## Repository visibility

This repository is currently public. The ZIP includes `INSTRUCTOR_NOTES.md`, which contains assessment solutions. Change the repository to **Private** in GitHub Settings if you do not want those notes publicly accessible.
