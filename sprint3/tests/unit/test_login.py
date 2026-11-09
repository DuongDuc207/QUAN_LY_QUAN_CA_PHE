from unittest.mock import MagicMock

import pyodbc
import pytest
from werkzeug.security import generate_password_hash

from api.auth import service
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def account(monkeypatch):
    row = {"TaiKhoanID": 12, "HoTen": "Test", "Email": "test@example.com",
           "VaiTroID": 1, "TenVaiTro": "Quan tri", "TrangThai": "HOAT_DONG",
           "MatKhauHash": generate_password_hash("secret123")}
    connection = MagicMock()
    connection.__enter__.return_value = connection
    monkeypatch.setattr(service, "get_connection", lambda: connection)
    monkeypatch.setattr(service, "fetch_one", lambda _: row.copy())
    monkeypatch.setattr(service, "_quyen_cua_vai_tro", lambda *_: ["inventory.view"])
    return row, connection


def test_login_me_logout(client, account):
    response = client.post("/api/v1/auth/login", json={"email": " TEST@Example.com ", "password": "secret123"})
    assert response.status_code == 200
    user = response.json["data"]
    assert "MatKhauHash" not in user
    assert user["Quyens"] == ["inventory.view"]
    account[1].cursor.return_value.execute.assert_called_with(
        "SELECT t.*, v.TenVaiTro FROM dbo.TaiKhoan t "
        "JOIN dbo.VaiTro v ON v.VaiTroID = t.VaiTroID WHERE LOWER(t.Email) = ?",
        ("test@example.com",))
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.get("/dashboard").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("payload", [None, [], [1], "text", 2, {},
                                        {"email": 12, "password": "test123"},
                                        {"email": "test@example.com", "password": []},
                                        {"email": " ", "password": "test123"}])
def test_bad_login_input(client, monkeypatch, payload):
    db = MagicMock(side_effect=AssertionError("Invalid input must not query database"))
    monkeypatch.setattr(service, "get_connection", db)
    assert client.post("/api/v1/auth/login", json=payload).status_code == 400
    db.assert_not_called()


def test_wrong_password_does_not_start_session(client, account):
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "wrong"})
    assert response.status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("stored", ["", "plaintext", "unknown$salt$hash", None, "scrypt:invalid$salt$hash"])
def test_invalid_stored_hash_returns_401(client, account, stored):
    account[0]["MatKhauHash"] = stored
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "secret123"})
    assert response.status_code == 401


def test_locked_account_is_rejected(client, account):
    account[0]["TrangThai"] = "KHOA"
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "secret123"})
    assert response.status_code == 401


def test_me_clears_session_for_locked_account(client, account):
    assert client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "secret123"}).status_code == 200
    account[0]["TrangThai"] = "KHOA"
    assert client.get("/api/v1/auth/me").status_code == 404
    assert client.get("/api/v1/auth/me").status_code == 401


def test_database_error_is_json_without_connection_details(client, monkeypatch):
    def broken():
        raise pyodbc.OperationalError("Connection failed: sensitive connection details")
    monkeypatch.setattr(service, "get_connection", broken)
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "secret123"})
    assert response.status_code == 503
    assert response.is_json
    assert response.json == {"success": False, "message": "Co so du lieu chua san sang"}
    assert "sensitive" not in response.get_data(as_text=True)
