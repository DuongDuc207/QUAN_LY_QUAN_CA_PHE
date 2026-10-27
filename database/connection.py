import pyodbc

from config.settings import (
    DB_DRIVER,
    DB_NAME,
    DB_PASSWORD,
    DB_SERVER,
    DB_TRUSTED,
    DB_USER,
)


def get_connection():
    """Tao ket noi moi toi SQL Server."""
    if DB_TRUSTED or not DB_USER:
        conn_str = (
            f"DRIVER={{{DB_DRIVER}}};SERVER={DB_SERVER};DATABASE={DB_NAME};"
            "Trusted_Connection=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={{{DB_DRIVER}}};SERVER={DB_SERVER};DATABASE={DB_NAME};"
            f"UID={DB_USER};PWD={DB_PASSWORD};"
        )
    return pyodbc.connect(conn_str)


def fetch_all(cursor):
    """Chuyen tat ca cac dong thanh list dict."""
    columns = [col[0] for col in cursor.description] if cursor.description else []
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_one(cursor):
    """Chuyen 1 dong thanh dict, None neu khong co."""
    if not cursor.description:
        return None
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None
