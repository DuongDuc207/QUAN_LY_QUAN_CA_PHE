"""Kiem thu giao dien: phan quyen hien thi, khong lo ma he thong va do phu API.

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
TRANG_SPRINT3 = ["/inventory", "/recipes", "/suppliers", "/purchases"]
TRANG_SPRINT4 = ["/promotions", "/reports", "/employees", "/schedules"]


@pytest.mark.parametrize("duong_dan", ["/dashboard", "/accounts", "/menu", "/roles", "/pos", "/orders"]
                         + TRANG_SPRINT3 + TRANG_SPRINT4)
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


@pytest.mark.parametrize("duong_dan", ["/accounts", "/menu", "/pos", "/orders"] + TRANG_SPRINT3
                         + [p for p in TRANG_SPRINT4 if p != "/reports"])  # bao cao khong co hop thoai
def test_hop_thoai_mac_dinh_an(client, duong_dan):
    login(client)
    html = client.get(duong_dan).get_data(as_text=True)
    lop = re.findall(r'<div class="([^"]*)"', html)
    modals = [c for c in lop if "modal" in c.split()]
    assert modals
    for cls in modals:
        assert "hidden" in cls.split(), f"Hop thoai khong an san: {cls}"


def test_khong_dung_hop_thoai_mac_dinh_cua_trinh_duyet():
    """confirm()/alert() cua trinh duyet khong doi ten nut duoc va trong xau.
    Moi cho xac nhan phai di qua xacNhan() trong main.js (tra ve Promise)."""
    for p in (FRONTEND / "static" / "js").glob("*.js"):
        if p.name == "main.js":
            continue  # noi dinh nghia xacNhan
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"(?<![\w.])confirm\s*\(", text), f"{p.name} con dung confirm() goc"
        assert not re.search(r"(?<![\w.])alert\s*\(", text), f"{p.name} con dung alert() goc"
    for p in (FRONTEND / "templates").rglob("*.html"):
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"(?<![\w.])confirm\s*\(", text), f"{p.name} con dung confirm() goc"
        assert not re.search(r"(?<![\w.])alert\s*\(", text), f"{p.name} con dung alert() goc"


def test_xacNhan_tra_ve_promise_va_cho_await():
    """xacNhan phai bat dong bo (tra Promise) va moi cho goi phai await, neu khong
    dieu kien luon dung va thao tac nguy hiem chay khong can hoi."""
    main_js = (FRONTEND / "static" / "js" / "main.js").read_text(encoding="utf-8")
    assert "new Promise" in main_js and "function xacNhan" in main_js
    for p in list((FRONTEND / "static" / "js").glob("*.js")) + list((FRONTEND / "templates").rglob("*.html")):
        if p.name == "main.js":
            continue
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r"xacNhan\s*\(", text):
            truoc = text[max(0, m.start() - 12):m.start()]
            assert "await " in truoc, f"{p.name}: goi xacNhan ma thieu await"


# ---------- Sprint 2: trang ban hang / don hang ----------
def test_nhan_vien_thay_ban_hang_va_don_hang(client):
    login(client, dl.NV_EMAIL, dl.NV_MK)
    html = client.get("/dashboard").get_data(as_text=True)
    nav = re.search(r"<nav class=\"nav\">(.*?)</nav>", html, re.S).group(1)
    assert "Bán hàng" in nav and "Đơn hàng" in nav
    assert client.get("/pos").status_code == 200
    assert client.get("/orders").status_code == 200


def test_chua_dang_nhap_khong_vao_ban_hang(client):
    for p in ("/pos", "/orders"):
        r = client.get(p)
        assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_nhan_vien_xem_kho_nhung_khong_vao_nhap_hang(client):
    """Nhan vien co inventory.view (xem ton kho, cong thuc) nhung khong co supplier.view."""
    login(client, dl.NV_EMAIL, dl.NV_MK)
    html = client.get("/dashboard").get_data(as_text=True)
    nav = re.search(r"<nav class=\"nav\">(.*?)</nav>", html, re.S).group(1)
    assert "Nguyên liệu và tồn kho" in nav
    assert "Nhập hàng" not in nav and "Nhà cung cấp" not in nav
    for p in ("/inventory", "/recipes"):
        assert client.get(p).status_code == 200, p
    for p in ("/suppliers", "/purchases"):
        assert client.get(p).status_code in (302, 403), p


def test_quan_tri_thay_trang_kho_va_the_kho(client):
    login(client)
    html = client.get("/dashboard").get_data(as_text=True)
    nav = re.search(r"<nav class=\"nav\">(.*?)</nav>", html, re.S).group(1)
    for muc in ("Nguyên liệu và tồn kho", "Công thức pha chế", "Nhập hàng", "Nhà cung cấp"):
        assert muc in nav
    assert 'id="tile-kho"' in html
    for p in TRANG_SPRINT3:
        assert client.get(p).status_code == 200, p


def test_ma_trang_thai_chi_nam_trong_main_js():
    """Template va JS cua trang khong viet ma he thong (HOAT_DONG, NHAP...) - de doi nhan 1 noi."""
    ma = ["HOAT_DONG", "KHOA", "CHO_PHA_CHE", "DANG_PHA_CHE", "HOAN_THANH", "DA_HUY",
          "THANH_CONG", "CHO_XAC_NHAN", "CHUA_THANH_TOAN", "HOAN_MOT_PHAN", "DA_HOAN_TIEN",
          # Sprint 3: kho va phieu nhap
          "NHAP", "DA_NHAN", "DU", "SAP_HET", "HET",
          "NHAP_HANG", "HUY_NHAP", "XUAT_KHO", "TIEU_HAO", "DIEU_CHINH",
          # Sprint 4: khuyen mai, nhan vien, lich lam
          "DANG_DIEN_RA", "SAP_DIEN_RA", "HET_LUOT", "DA_KET_THUC", "DA_TAT", "PHAN_TRAM", "SO_TIEN",
          "DANG_LAM", "TAM_NGHI", "NGHI_VIEC", "DA_XEP", "DA_LAM", "VANG"]
    for p in (FRONTEND / "templates").rglob("*.html"):
        if p.name == "print.html":
            continue  # trang in co bang nhan rieng (Jinja), da kiem o test_sprint2
        text = p.read_text(encoding="utf-8")
        lo = [m for m in ma if re.search(rf"['\"`]{m}['\"`]", text)]
        assert not lo, f"{p.name} viet thang ma he thong: {lo}"
    for p in (FRONTEND / "static" / "js").glob("*.js"):
        if p.name == "main.js":
            continue  # noi duy nhat duoc giu bang ma -> nhan
        js = p.read_text(encoding="utf-8")
        lo = [m for m in ma if re.search(rf"['\"`]{m}['\"`]", js)]
        assert not lo, f"{p.name} viet thang ma he thong: {lo}"


# ---------- Do phu API (Sprint 1: 21, Sprint 2: 17, Sprint 3: 25, Sprint 4: 27) ----------
SO_API = 90


def test_giao_dien_dung_du_api():
    app = create_app()
    api = set()
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if "/api/v1" in path:
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                api.add((method, path.replace("/api/v1", "")))
    assert len(api) == SO_API, f"Backend co {len(api)} API, mong doi {SO_API}"

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

# ---------- Sprint 4: khuyen mai, bao cao, nhan vien, lich lam ----------
def test_quan_tri_thay_trang_sprint4(client):
    login(client)
    html = client.get("/dashboard").get_data(as_text=True)
    nav = re.search(r"<nav class=\"nav\">(.*?)</nav>", html, re.S).group(1)
    for muc in ("Khuyến mãi", "Báo cáo", "Hồ sơ nhân viên", "Ca làm và lịch làm", "Tài khoản đăng nhập"):
        assert muc in nav, muc
    assert 'id="tile-doanh-thu"' in html
    for p in TRANG_SPRINT4:
        assert client.get(p).status_code == 200, p

def test_nhan_vien_chi_thay_lich_cua_minh(client):
    login(client, dl.NV_EMAIL, dl.NV_MK)
    html = client.get("/dashboard").get_data(as_text=True)
    nav = re.search(r"<nav class=\"nav\">(.*?)</nav>", html, re.S).group(1)
    assert "Lịch làm của tôi" in nav
    for muc in ("Khuyến mãi", "Báo cáo", "Hồ sơ nhân viên"):
        assert muc not in nav, muc
    assert 'id="tile-doanh-thu"' not in html or "report.view" not in html
    assert client.get("/schedules").status_code == 200
    for p in ("/promotions", "/reports", "/employees"):
        assert client.get(p).status_code in (302, 403), p

def test_ban_hang_co_o_nhap_ma_khuyen_mai(client):
    login(client, dl.NV_EMAIL, dl.NV_MK)
    html = client.get("/pos").get_data(as_text=True)
    assert 'id="km-ma"' in html and "Mã khuyến mãi" in html

def test_bien_jinja_dung_trong_scripts_phai_khai_bao_trong_scripts():
    """{% set %} trong block content KHONG thay duoc o block scripts (Jinja tach pham vi block).
    Thieu khai bao -> co quyen van ra false, nut quan ly mat chuc nang."""
    for p in (FRONTEND / "templates").rglob("*.html"):
        s = p.read_text(encoding="utf-8")
        if "{% block scripts %}" not in s:
            continue
        truoc, scripts = s.split("{% block scripts %}", 1)
        bien = set(re.findall(r"{% set (\w+)", truoc))
        khai_bao = set(re.findall(r"{% set (\w+)", scripts))
        thieu = [v for v in bien - khai_bao if re.search(r"{[{%][^}%]*\b" + v + r"\b", scripts)]
        assert not thieu, f"{p.name}: block scripts dung {thieu} nhung chua khai bao lai"

def test_quan_tri_co_quyen_quan_ly_trong_script(client):
    login(client)
    for p in ("/menu", "/suppliers", "/promotions", "/employees", "/schedules"):
        html = client.get(p).get_data(as_text=True)
        assert "const CO_QUAN_LY = true" in html, p
    assert "const DUOC_NGUNG = true" in client.get("/accounts").get_data(as_text=True)
