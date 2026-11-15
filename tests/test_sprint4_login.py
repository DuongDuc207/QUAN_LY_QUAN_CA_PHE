"""Login regressions; no database writes or running SQL Server required."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("FLASK_SECRET_KEY", "test-only-" + "0" * 64)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sprint4"))

import pyodbc
from werkzeug.security import generate_password_hash

from api.auth import service
from app import create_app
from database import connection


class Sprint4LoginTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        app.logger.disabled = True
        self.client = app.test_client()
        self.row = {
            "TaiKhoanID": 12, "HoTen": "Test", "Email": "test@example.com",
            "VaiTroID": 1, "TenVaiTro": "Quan tri", "TrangThai": "HOAT_DONG",
            "MatKhauHash": generate_password_hash("secret123"),
        }
        self.conn = MagicMock()
        self.conn.__enter__.return_value = self.conn
        for mocked in (
            patch.object(service, "get_connection", return_value=self.conn),
            patch.object(service, "fetch_one", side_effect=lambda _: self.row.copy()),
            patch.object(service, "_quyen_cua_vai_tro", return_value=["inventory.view"]),
        ):
            mocked.start()
            self.addCleanup(mocked.stop)

    def login(self, password="secret123"):
        return self.client.post("/api/v1/auth/login", json={
            "email": " TEST@Example.com ", "password": password,
        })

    def test_login_session_dashboard_logout(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("MatKhauHash", response.json["data"])
        self.assertEqual(response.json["data"]["Quyens"], ["inventory.view"])
        self.conn.cursor.return_value.execute.assert_called_with(
            "SELECT t.*, v.TenVaiTro FROM dbo.TaiKhoan t "
            "JOIN dbo.VaiTro v ON v.VaiTroID = t.VaiTroID WHERE LOWER(t.Email) = ?",
            ("test@example.com",),
        )
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)
        self.assertEqual(self.client.get("/dashboard").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)

    def test_wrong_password_locked_or_missing_account(self):
        self.assertEqual(self.login("wrong").status_code, 401)
        self.row["TrangThai"] = "KHOA"
        self.assertEqual(self.login().status_code, 401)
        with patch.object(service, "fetch_one", return_value=None):
            self.assertEqual(self.login().status_code, 401)
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)

    def test_invalid_input_does_not_query_database(self):
        for payload in (None, [], [1], "text", 2, {},
                        {"email": 12, "password": "secret123"},
                        {"email": "test@example.com", "password": []},
                        {"email": " ", "password": "secret123"}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/v1/auth/login", json=payload)
                self.assertEqual(response.status_code, 400)
        service.get_connection.assert_not_called()

    def test_invalid_stored_hash_is_rejected(self):
        for stored in ("", "plaintext", "unknown$salt$hash", None,
                       "scrypt:invalid$salt$hash"):
            with self.subTest(stored=stored):
                self.row["MatKhauHash"] = stored
                self.assertEqual(self.login().status_code, 401)

    def test_database_failure_returns_json_then_retry_succeeds(self):
        with patch.object(service, "get_connection", side_effect=pyodbc.OperationalError(
            "Sensitive connection details",
        )):
            response = self.login()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json, {
            "success": False, "message": "Co so du lieu chua san sang",
        })
        self.assertNotIn("Sensitive", response.get_data(as_text=True))
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)
        self.assertEqual(self.login().status_code, 200)

    def test_connection_has_timeout(self):
        with patch.object(connection.pyodbc, "connect") as connect:
            connection.get_connection()
        self.assertEqual(connect.call_args.kwargs["timeout"], 5)


if __name__ == "__main__":
    unittest.main()
