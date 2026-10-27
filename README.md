# Eduserve — Functional Student Portal & Cybersecurity Assessment Lab

A standalone Flask + SQLite student portal and authorized local web-security training lab. It uses fictional academic records and is **not** the official Karunya Eduserve system. Source files are stored as normal editable project files in this repository.

## Run on Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and replace all four example passwords with unique private passwords of at least 12 characters. Set `FLASK_SECRET_KEY` to a random string of at least 32 characters. Then run:

```bash
python -m database.init_db
python app.py
```

Open http://127.0.0.1:5000 and stop with `Ctrl+C`. The server is configured for localhost only. Do not use real university credentials or records and do not expose vulnerable mode to a network.

## Documentation

- `ASSESSMENT_README.md` — student brief, setup, testing scope, clues, evidence template, and troubleshooting.
- `REMEDIATION.md` — controls and retest expectations for patched mode.
- `INSTRUCTOR_NOTES.md` — owner reference to the intended findings and their reproduction.

## Important repository visibility note

This GitHub repository is currently **public**, so `INSTRUCTOR_NOTES.md` is publicly readable. For a real class assessment, change the repository to **Private** in GitHub Settings before sharing it with students, or move the instructor reference to a separate private repository. No lab passwords are committed; configure them locally in `.env`.
