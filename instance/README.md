# Local instance data

The SQLite database is generated locally by `python -m database.init_db` at `instance/eduserve.sqlite3` by default. The `.gitignore` excludes local SQLite database files and backups. Do not commit a real database, `.env` file, credentials, or assessment session evidence.
