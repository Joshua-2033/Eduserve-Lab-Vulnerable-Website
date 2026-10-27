"""Reset Eduserve's local synthetic database after explicit confirmation.

This deletes only the configured local lab database after creating a timestamped
backup. It does not change passwords or any remote service.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
DB = Path(os.getenv('EDUSERVE_DATABASE', str(ROOT / 'instance' / 'eduserve.sqlite3'))).expanduser().resolve()
password_names = ('LAB_JOSHUA_PASSWORD', 'LAB_SABARI_PASSWORD', 'LAB_NITHIN_PASSWORD', 'LAB_ADMIN_PASSWORD')
passwords = [os.getenv(name, '') for name in password_names]
secret = os.getenv('FLASK_SECRET_KEY', '')
if any(len(value) < 12 or value.startswith('change-this-') for value in passwords):
    print('Reset cancelled: configure four unique LAB_*_PASSWORD values of at least 12 characters in .env.', file=sys.stderr)
    raise SystemExit(2)
if len(secret) < 32 or secret.startswith('replace-with-'):
    print('Reset cancelled: configure a random FLASK_SECRET_KEY of at least 32 characters in .env.', file=sys.stderr)
    raise SystemExit(2)
if DB == Path('/') or DB == ROOT or ROOT not in DB.parents:
    print(f'Reset cancelled: refusing to remove a database path outside this project: {DB}', file=sys.stderr)
    raise SystemExit(2)
if DB.exists():
    print(f'This will replace the local synthetic database at: {DB}')
    confirm = input('Type RESET to continue: ').strip()
    if confirm != 'RESET':
        print('Cancelled; database left unchanged.')
        raise SystemExit(1)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = DB.with_name(f'{DB.stem}.backup-{stamp}{DB.suffix}')
    shutil.copy2(DB, backup)
    print(f'Backup created: {backup}')
    DB.unlink()
DB.parent.mkdir(parents=True, exist_ok=True)
env = dict(os.environ)
env['EDUSERVE_DATABASE'] = str(DB)
result = subprocess.run([sys.executable, '-m', 'database.init_db'], cwd=ROOT, env=env)
if result.returncode:
    print('Initialization failed. If a backup was created, restore it manually from the printed backup path.', file=sys.stderr)
    raise SystemExit(result.returncode)
print(f'Synthetic database initialized: {DB}')
