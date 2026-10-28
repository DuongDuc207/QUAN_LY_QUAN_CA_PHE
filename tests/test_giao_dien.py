"""Kiem thu giao dien: phan quyen hien thi va do phu 21 API cua Sprint 1.

Chay: py -3.12 -m pytest tests/ -v
"""

import pathlib
import re

import pytest

from app import create_app
from tests import du_lieu_test as dl

FRONTEND = pathlib.Path(__file__).resolve().parent.parent / "frontend"

# Thuat ngu ky thuat khong duoc xuat hien trong phan chu ma khach doc.
TU_CAM = ["Sprint", "SQL Server", "Flask", "pyodbc", "dbo.", "/api/v1"]


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


def van_ban_hien_thi(html):
    """Bo <script>, <style> va cac thuoc tinh the -> con lai chu khach doc."""
    html = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", "", html, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", html)


# ---------- Trang phan quyen ----------
def test_trang_phan_quyen_mo_duoc(client):
    login(client)
    assert client.get("/roles").status_code == 200


def test_chua_dang_nhap_bi_dua_ve_trang_dang_nhap(client):
    r = client.get("/roles")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


# ---------- Menu dieu huong an theo quyen ----------
def test_nhan_vien_khong_thay_muc_nhan_su_va_phan_quyen(client):
    login(client, dl.NV_EMAIL, dl.NV_MK)
    html = client.get("/dashboard").get_data(as_text=True)
    nav = re.search(r"<nav class=\"nav\">(.*?)</nav>", html, re.S).group(1)
    assert "Thực đơn" in nav
    assert "Nhân sự" not in nav
    assert "Phân quyền" not in nav


def test_quan_tri_thay_day_du_muc_dieu_huong(client):
    login(client)
    html = client.get("/dashboard").get_data(as_text=True)
    nav = re.search(r"<nav class=\"nav\">(.*?)</nav>", html, re.S).group(1)
    for muc in ("Trang chủ", "Nhân sự", "Thực đơn", "Phân quyền"):
        assert muc in nav


# ---------- Khong lo thuat ngu backend ----------
@pytest.mark.parametrize("duong_dan", ["/dashboard", "/accounts", "/menu", "/roles"])
def test_khong_lo_thuat_ngu_ky_thuat(client, duong_dan):
    login(client)
    text = van_ban_hien_thi(client.get(duong_dan).get_data(as_text=True))
    lo = [t for t in TU_CAM if t in text]
    assert not lo, f"{duong_dan} con lo thuat ngu: {lo}"


def test_trang_dang_nhap_khong_goi_y_tai_khoan_mau(client):
    html = client.get("/login").get_data(as_text=True)
    assert "admin123" not in html
    assert "@caphe.local" not in html


# ---------- Hop thoai mac dinh phai an ----------
def test_class_hidden_thang_moi_luat_display():
    """.hidden phai co !important, neu khong .modal { display: flex } se ghi de
    va moi hop thoai hien cung luc khi vua mo trang."""
    css = (FRONTEND / "static" / "css" / "style.css").read_text(encoding="utf-8")
    assert re.search(r"\.hidden\s*\{\s*display:\s*none\s*!important", css)


@pytest.mark.parametrize("duong_dan", ["/accounts", "/menu"])
def test_hop_thoai_mac_dinh_an(client, duong_dan):
    login(client)
    html = client.get(duong_dan).get_data(as_text=True)
    lop = re.findall(r'<div class="([^"]*)"', html)
    modals = [c for c in lop if "modal" in c.split()]
    assert modals
    for cls in modals:
        assert "hidden" in cls.split(), f"Hop thoai khong an san: {cls}"


# ---------- Do phu 21 API ----------
def test_giao_dien_dung_du_21_api():
    app = create_app()
    api = set()
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if "/api/v1" in path:
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                api.add((method, path.replace("/api/v1", "")))
    assert len(api) == 21, f"Backend co {len(api)} API, mong doi 21"

    source = ""
    for p in FRONTEND.rglob("*"):
        if p.suffix in (".html", ".js"):
            source += p.read_text(encoding="utf-8")

    # /auth/me la API nen (xac thuc phien), khong can nut rieng tren giao dien.
    chua_dung = []
    for method, rule in sorted(api):
        if rule == "/auth/me":
            continue
        # Doi tham so duong dan thanh mau bat ky de khop voi `${id}` trong JS.
        mau = re.escape(rule).replace(r"<int:", "<").replace("\\<", "<")
        mau = re.sub(r"<[^>]+>", r"[^\"'`]+", mau)
        if not re.search(mau, source):
            chua_dung.append(f"{method} {rule}")
    assert not chua_dung, f"Giao dien chua dung: {chua_dung}"
