import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)
    DATABASE = os.getenv('EDUSERVE_DATABASE', str(ROOT / 'instance' / 'eduserve.sqlite3'))
    LAB_MODE = os.getenv('EDUSERVE_LAB_MODE', 'vulnerable').lower()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # The lab runs on localhost over HTTP; Secure cookies would prevent local testing.
    SESSION_COOKIE_SECURE = False
