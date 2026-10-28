"""Kiem thu Sprint 1: auth (11 API) + menu (10 API). Chay: py -3.12 -m pytest tests/ -v"""

import pytest

from app import create_app
from tests import du_lieu_test as dl


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def login(client, email=dl.ADMIN_EMAIL, password=dl.ADMIN_MK):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.get_json()
    return r.get_json()["data"]


# ---------- Auth ----------
def test_login_sai_bi_401(client):
    r = client.post("/api/v1/auth/login", json={"email": dl.ADMIN_EMAIL, "password": "sai"})
    assert r.status_code == 401


def test_login_me_logout(client):
    user = login(client)
    assert "account.view" in user["Quyens"]
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.get_json()["data"]["Email"] == dl.ADMIN_EMAIL
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_crud_tai_khoan_va_khoa(client):
    login(client)
    r = client.post("/api/v1/accounts", json={
        "ho_ten": "Test Pytest", "email": "pytest@caphe.local",
        "mat_khau": "test123", "vai_tro_id": 3,
    })
    assert r.status_code == 201, r.get_json()
    nid = r.get_json()["data"]["TaiKhoanID"]

    r = client.get(f"/api/v1/accounts/{nid}")
    assert r.status_code == 200
    r = client.put(f"/api/v1/accounts/{nid}", json={"ho_ten": "Test Updated"})
    assert r.get_json()["data"]["HoTen"] == "Test Updated"

    # Khoa -> khong login duoc
    r = client.patch(f"/api/v1/accounts/{nid}/status", json={"trang_thai": "KHOA"})
    assert r.get_json()["data"]["TrangThai"] == "KHOA"
    r = client.post("/api/v1/auth/login", json={"email": "pytest@caphe.local", "password": "test123"})
    assert r.status_code == 401
    login(client)  # login lai admin (session cu van giu)

    # Khong tu khoa chinh minh
    me = client.get("/api/v1/auth/me").get_json()["data"]
    r = client.patch(f"/api/v1/accounts/{me['TaiKhoanID']}/status", json={"trang_thai": "KHOA"})
    assert r.status_code == 400

    # Don dep
    client.patch(f"/api/v1/accounts/{nid}/status", json={"trang_thai": "HOAT_DONG"})
    from database.connection import get_connection
    with get_connection() as conn:
        conn.cursor().execute("DELETE FROM TaiKhoan WHERE TaiKhoanID = ?", (nid,))
        conn.commit()


def test_vai_tro_quyen_va_phan_quyen(client):
    login(client)
    assert client.get("/api/v1/roles").status_code == 200
    assert len(client.get("/api/v1/permissions").get_json()["data"]) >= 7
    r = client.put("/api/v1/roles/3/permissions", json={"quyen_ids": [6]})
    assert r.status_code == 200

    # Nhan vien bi chan API can quyen cao
    staff = create_staff_client()
    r = staff.get("/api/v1/accounts")
    assert r.status_code == 403
    r = staff.post("/api/v1/menu", json={"ten_mon": "X", "danh_muc_id": dl.DANH_MUC_ID, "gia_ban": 10})
    assert r.status_code == 403


def create_staff_client():
    from app import create_app as _ca
    app = _ca()
    app.config.update(TESTING=True)
    c = app.test_client()
    c.post("/api/v1/auth/login", json={"email": dl.NV_EMAIL, "password": dl.NV_MK})
    return c


# ---------- Menu ----------
def test_crud_danh_muc(client):
    login(client)
    r = client.post("/api/v1/categories", json={"ten_danh_muc": "DM Pytest"})
    assert r.status_code == 201, r.get_json()
    cid = r.get_json()["data"]["DanhMucID"]
    r = client.put(f"/api/v1/categories/{cid}", json={"ten_danh_muc": "DM Pytest 2"})
    assert r.get_json()["data"]["TenDanhMuc"] == "DM Pytest 2"
    # Xoa duoc vi chua co mon
    assert client.delete(f"/api/v1/categories/{cid}").status_code == 200
    # Khong xoa danh muc dang co mon
    r = client.delete(f"/api/v1/categories/{dl.DANH_MUC_ID}")
    assert r.status_code == 400


def test_crud_mon_va_tim_kiem(client):
    login(client)
    # Gia am bi chan
    r = client.post("/api/v1/menu", json={"ten_mon": "Loi", "danh_muc_id": dl.DANH_MUC_ID, "gia_ban": -1})
    assert r.status_code == 400
    r = client.post("/api/v1/menu", json={
        "ten_mon": "Mon Pytest", "danh_muc_id": dl.DANH_MUC_ID, "gia_ban": 45000})
    assert r.status_code == 201, r.get_json()
    mid = r.get_json()["data"]["MonID"]

    assert client.get(f"/api/v1/menu/{mid}").status_code == 200
    r = client.put(f"/api/v1/menu/{mid}", json={"gia_ban": 50000})
    assert float(r.get_json()["data"]["GiaBan"]) == 50000
    assert client.get("/api/v1/menu/search?q=Mon Pytest").get_json()["data"]["total"] >= 1
    r = client.patch(f"/api/v1/menu/{mid}/status", json={"dang_ban": False})
    assert r.get_json()["data"]["TrangThai"] is False

    # Nhan vien doc duoc menu
    staff = create_staff_client()
    assert staff.get("/api/v1/menu").status_code == 200

    # Don dep
    from database.connection import get_connection
    with get_connection() as conn:
        conn.cursor().execute("DELETE FROM Mon WHERE MonID = ?", (mid,))
        conn.commit()


def test_giao_dien_pages(client):
    assert client.get("/login").status_code == 200
    login(client)
    assert client.get("/dashboard").status_code == 200
    assert client.get("/accounts").status_code == 200
    assert client.get("/menu").status_code == 200
