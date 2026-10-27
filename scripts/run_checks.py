"""Run low-dependency integrity checks and the application integration suite."""
from __future__ import annotations

import compileall
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    print("[1/3] Compiling Python sources…")
    if not compileall.compile_dir(str(ROOT), quiet=1, maxlevels=8,
                                  rx=__import__('re').compile(r"(^|[/\\])(\.venv|__pycache__)([/\\]|$)")):
        print("Python compilation failed.", file=sys.stderr)
        return 1

    print("[2/3] Validating SQLite schema…")
    try:
        with sqlite3.connect(":memory:") as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.executescript((ROOT / "database" / "schema.sql").read_text(encoding="utf-8"))
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            expected = {"users", "student_profiles", "academic_terms", "courses", "enrollments",
                        "attendance_records", "examinations", "assessment_results", "feedback_submissions"}
            missing = expected - tables
            if missing:
                print("Missing schema tables: " + ", ".join(sorted(missing)), file=sys.stderr)
                return 1
    except sqlite3.Error as exc:
        print(f"SQLite schema validation failed: {exc}", file=sys.stderr)
        return 1

    print("[3/3] Running integration tests…")
    completed = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
