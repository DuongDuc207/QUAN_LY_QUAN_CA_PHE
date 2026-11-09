import os
from pathlib import Path

from dotenv import load_dotenv

# Ca app, terminal va test deu doc cung file, khong phu thuoc thu muc dang chay.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DB_SERVER = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")
DB_NAME = os.getenv("DB_NAME", "QuanLyCaPhe")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_TRUSTED = os.getenv("DB_TRUSTED", "yes").lower() in ("1", "true", "yes")

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "").strip()
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "FLASK_SECRET_KEY must be set to a unique value of at least 32 characters. "
        "Generate one with: py -c \"import secrets; print(secrets.token_hex(32))\""
    )
