"""Chay toan bo test tren CSDL tam, tu don dep khi ket thuc.

Chay tu sprint3: .venv\Scripts\python.exe tests/run_isolated.py
"""

import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database.connection import get_connection  # noqa: E402


def main():
    name = "QLCP_test_" + uuid.uuid4().hex
    # Ten duoc sinh noi bo, chi chua chu/so/_; khong nhan ten CSDL that tu tham so.
    assert re.fullmatch(r"QLCP_test_[0-9a-f]{32}", name)
    conn = get_connection()
    created = False
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("USE master")
        cur.execute(f"CREATE DATABASE [{name}]")
        created = True
        print(f"Test database: {name}", flush=True)
        cur.execute(f"USE [{name}]")
        for filename in ("schema.sql", "schema_sprint2.sql", "schema_sprint3.sql", "seed.sql"):
            script = (ROOT / "database" / filename).read_text(encoding="utf-8-sig")
            for batch in re.split(r"^\s*GO\s*$", script, flags=re.MULTILINE | re.IGNORECASE):
                if batch.strip():
                    cur.execute(batch)
                    while cur.nextset():
                        pass
        env = os.environ.copy()
        env["DB_NAME"] = name
        return subprocess.call([sys.executable, "-m", "pytest", "tests", "-q", *sys.argv[1:]],
                               cwd=ROOT, env=env)
    finally:
        try:
            if created:
                cur = conn.cursor()
                cur.execute("USE master")
                cur.execute(f"ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
                cur.execute(f"DROP DATABASE [{name}]")
                print(f"Removed test database: {name}", flush=True)
        finally:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
