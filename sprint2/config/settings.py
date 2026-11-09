import os
from pathlib import Path

from dotenv import load_dotenv

# Always read this sprint's configuration, including from CLI tools and tests.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DB_SERVER = os.getenv("DB_SERVER", r"localhost\SQL2022EXP")
DB_NAME = os.getenv("DB_NAME", "QuanLyCaPhe")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_TRUSTED = os.getenv("DB_TRUSTED", "yes").lower() in ("1", "true", "yes")

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "quanlycaphe-secret-key")
