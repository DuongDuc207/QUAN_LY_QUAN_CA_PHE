"""Kiem thu Sprint 3 - nha cung cap va nhap hang (API 54-63, module suppliers).

Nguyen lieu tao truc tiep bang SQL (khong goi API kho). Ten du lieu test luon bat dau "Pytest"
nen conftest tu don sau khi chay. Vai tro / tai khoan phu tao rieng trong fixture va xoa o cuoi.

Chay: py -3.12 -m pytest tests/test_sprint3_nhap_hang.py -q
"""

import threading
import uuid
from contextlib import closing
from decimal import Decimal

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from database.connection import get_connection
from tests import du_lieu_test as dl

API = "/api/v1"
PN = f"{API}/purchase-receipts"
NCC = f"{API}/suppliers"

QL_EMAIL, QL_MK = "pytest-quanly-nhap@test.local", "quanly123"
HAN_CHE_EMAIL, HAN_CHE_MK = "pytest-vaitro-nhap@test.local", "hanche123"
VAI_TRO_PHU = "Pytest Vai Tro Nhap"

_APP = create_app()
_APP.config.update(TESTING=True)


# ---------- SQL truc tiep (dung cho dung du lieu test) ----------
def _chay(sql, *params):
    with closing(get_connection()) as conn:
        conn.cursor().execute(sql, params)
        conn.commit()


def _mot(sql, *params):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()


def _nhieu(sql, *params):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()


def _hau_to():
    return uuid.uuid4().hex[:8]


def tao_nl(goi_y="a", ton="0", dang_dung=True):
    ten = f"Pytest NL {goi_y} {_hau_to()}"
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dbo.NguyenLieu (TenNguyenLieu, DonViTinh, SoLuongTon, TrangThai) "
            "OUTPUT INSERTED.NguyenLieuID VALUES (?, N'kg', ?, ?)",
            (ten, Decimal(ton), 1 if dang_dung else 0),
        )
        nl_id = cur.fetchval()
        conn.commit()
    return nl_id


def tao_ncc_sql(goi_y="a", dang_hop_tac=True):
    ten = f"Pytest NCC {goi_y} {_hau_to()}"
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dbo.NhaCungCap (TenNhaCungCap, TrangThai) OUTPUT INSERTED.NhaCungCapID VALUES (?, ?)",
            (ten, 1 if dang_hop_tac else 0),
        )
        ncc_id = cur.fetchval()
        conn.commit()
    return ncc_id


def ton(nl_id):
    return Decimal(_mot("SELECT SoLuongTon FROM dbo.NguyenLieu WHERE NguyenLieuID = ?", nl_id)[0])


def dat_ton(nl_id, so):
    """Mo phong hang da dung / kiem ke ngoai le: chi dung de dung tinh huong test."""
    _chay("UPDATE dbo.NguyenLieu SET SoLuongTon = ? WHERE NguyenLieuID = ?", Decimal(so), nl_id)


def lich_su(phieu_id):
    return _nhieu(
        "SELECT NguyenLieuID, TaiKhoanID, LoaiGiaoDich, SoLuongThayDoi, SoLuongTruoc, SoLuongSau, LyDo, "
        "PhieuNhapID FROM dbo.LichSuKho WHERE PhieuNhapID = ? ORDER BY LichSuKhoID",
        phieu_id,
    )


def so_lich_su_nl(nl_id):
    return _mot("SELECT COUNT(*) FROM dbo.LichSuKho WHERE NguyenLieuID = ?", nl_id)[0]


def trang_thai_phieu(phieu_id):
    return _mot("SELECT TrangThai FROM dbo.PhieuNhap WHERE PhieuNhapID = ?", phieu_id)[0]


def hom_nay_csdl():
    return _mot("SELECT CAST(SYSDATETIME() AS DATE)")[0]


# ---------- Client ----------
def dang_nhap(email, mk):
    c = _APP.test_client()
    r = c.post(f"{API}/auth/login", json={"email": email, "password": mk})
    assert r.status_code == 200, r.get_json()
    return c


@pytest.fixture(scope="module", autouse=True)
def tai_khoan_phu():
    """Quan ly (vai tro 2) + 1 vai tro tam co supplier.view/manage nhung KHONG co purchase.confirm."""
    _don_tai_khoan_phu()
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dbo.TaiKhoan (VaiTroID, HoTen, Email, MatKhauHash, TrangThai, NgayTao) "
            "VALUES (2, N'Pytest Quan Ly Nhap', ?, ?, 'HOAT_DONG', SYSDATETIME())",
            (QL_EMAIL, generate_password_hash(QL_MK)),
        )
        cur.execute(
            "INSERT INTO dbo.VaiTro (TenVaiTro, MoTa, NgayTao) OUTPUT INSERTED.VaiTroID "
            "VALUES (?, N'Vai tro tam cho kiem thu', SYSDATETIME())",
            (VAI_TRO_PHU,),
        )
        vai_tro_id = cur.fetchval()
        cur.execute(
            "INSERT INTO dbo.VaiTroQuyen (VaiTroID, QuyenID) "
            "SELECT ?, QuyenID FROM dbo.Quyen WHERE TenQuyen IN ('supplier.view', 'supplier.manage')",
            (vai_tro_id,),
        )
        cur.execute(
            "INSERT INTO dbo.TaiKhoan (VaiTroID, HoTen, Email, MatKhauHash, TrangThai, NgayTao) "
            "VALUES (?, N'Pytest Han Che Nhap', ?, ?, 'HOAT_DONG', SYSDATETIME())",
            (vai_tro_id, HAN_CHE_EMAIL, generate_password_hash(HAN_CHE_MK)),
        )
        conn.commit()
    try:
        yield
    finally:
        _don_tai_khoan_phu()


def _don_tai_khoan_phu():
    """Tai khoan han che khong so huu dong nao (chi bi tu choi hoac huy phieu NHAP) nen xoa duoc."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM dbo.TaiKhoan WHERE Email = ?", (HAN_CHE_EMAIL,))
        cur.execute(
            "DELETE FROM dbo.VaiTroQuyen WHERE VaiTroID IN (SELECT VaiTroID FROM dbo.VaiTro WHERE TenVaiTro = ?)",
            (VAI_TRO_PHU,),
        )
        cur.execute("DELETE FROM dbo.VaiTro WHERE TenVaiTro = ?", (VAI_TRO_PHU,))
        conn.commit()


@pytest.fixture(scope="module")
def admin():
    return dang_nhap(dl.ADMIN_EMAIL, dl.ADMIN_MK)


@pytest.fixture(scope="module")
def quan_ly():
    return dang_nhap(QL_EMAIL, QL_MK)


@pytest.fixture(scope="module")
def nhan_vien():
    return dang_nhap(dl.NV_EMAIL, dl.NV_MK)


@pytest.fixture(scope="module")
def han_che():
    return dang_nhap(HAN_CHE_EMAIL, HAN_CHE_MK)


# ---------- Helper goi API ----------
def dong(nl_id, so_luong, don_gia):
    return {"nguyen_lieu_id": nl_id, "so_luong": so_luong, "don_gia_nhap": don_gia}


def tao_phieu(c, ncc_id, items, **them):
    r = c.post(PN, json={"nha_cung_cap_id": ncc_id, "items": items, **them})
    assert r.status_code == 201, r.get_json()
    return r.get_json()["data"]


def xac_nhan(c, phieu_id, ma=200):
    r = c.post(f"{PN}/{phieu_id}/confirm")
    assert r.status_code == ma, r.get_json()
    return r.get_json().get("data")


def huy(c, phieu_id, ly_do="Nha cung cap khong giao", ma=200):
    r = c.post(f"{PN}/{phieu_id}/cancel", json={"ly_do": ly_do})
    assert r.status_code == ma, r.get_json()
    return r.get_json().get("data")


def d(x):
    return Decimal(str(x))


# =====================================================================
# 54-57. NHA CUNG CAP
# =====================================================================
def test_tao_nha_cung_cap_thanh_cong(admin):
    ten = f"  Pytest NCC Tao {_hau_to()}  "
    r = admin.post(NCC, json={
        "ten_nha_cung_cap": ten, "so_dien_thoai": "+84 912-345.678",
        "email": "ban-hang@pytest-ncc.vn", "dia_chi": "  12 Le Loi, Q1  ", "trang_thai": False})
    assert r.status_code == 201, r.get_json()
    n = r.get_json()["data"]
    assert n["TenNhaCungCap"] == ten.strip()
    assert n["SoDienThoai"] == "+84 912-345.678"
    assert n["Email"] == "ban-hang@pytest-ncc.vn"
    assert n["DiaChi"] == "12 Le Loi, Q1"
    assert n["TrangThai"] is True  # tao moi luon dang hop tac, bo qua trang_thai client gui
    assert n["SoPhieuNhap"] == 0 and n["TongSoPhieu"] == 0
    assert d(n["TongTienDaNhan"]) == 0 and n["PhieuGanNhat"] == []

    # Chi can ten
    r = admin.post(NCC, json={"ten_nha_cung_cap": f"Pytest NCC Toi Thieu {_hau_to()}"})
    assert r.status_code == 201
    assert r.get_json()["data"]["SoDienThoai"] is None


def test_tao_nha_cung_cap_trung_ten_409(admin):
    ten = f"Pytest NCC Trung {_hau_to()}"
    assert admin.post(NCC, json={"ten_nha_cung_cap": ten}).status_code == 201
    r = admin.post(NCC, json={"ten_nha_cung_cap": f"  {ten}  "})
    assert r.status_code == 409
    assert r.get_json()["message"] == "Nha cung cap da ton tai"
    # Khong phan biet hoa thuong (collation mac dinh cua CSDL)
    assert admin.post(NCC, json={"ten_nha_cung_cap": ten.upper()}).status_code == 409


@pytest.mark.parametrize("body", [
    {},
    {"ten_nha_cung_cap": ""},
    {"ten_nha_cung_cap": "    "},
    {"ten_nha_cung_cap": 123},
    {"ten_nha_cung_cap": None},
    {"ten_nha_cung_cap": "Pytest X", "so_dien_thoai": "1234567"},          # < 8 ky tu
    {"ten_nha_cung_cap": "Pytest X", "so_dien_thoai": "1234567890123456"},  # > 15 ky tu
    {"ten_nha_cung_cap": "Pytest X", "so_dien_thoai": "abc12345678"},
    {"ten_nha_cung_cap": "Pytest X", "so_dien_thoai": 912345678},
    {"ten_nha_cung_cap": "Pytest X", "email": "abc"},
    {"ten_nha_cung_cap": "Pytest X", "email": "a@b"},
    {"ten_nha_cung_cap": "Pytest X", "email": "a b@c.vn"},
    {"ten_nha_cung_cap": "Pytest X", "email": 5},
    {"ten_nha_cung_cap": "Pytest X", "dia_chi": 5},
])
def test_tao_nha_cung_cap_du_lieu_sai_400(admin, body):
    if "ten_nha_cung_cap" in body and isinstance(body["ten_nha_cung_cap"], str) and body["ten_nha_cung_cap"].strip():
        body = {**body, "ten_nha_cung_cap": f"{body['ten_nha_cung_cap']} {_hau_to()}"}
    r = admin.post(NCC, json=body)
    assert r.status_code == 400, r.get_json()
    assert r.get_json()["success"] is False


def test_tao_nha_cung_cap_body_khong_phai_json_400(admin):
    r = admin.post(NCC, data="khong phai json", content_type="text/plain")
    assert r.status_code == 400
    r = admin.post(NCC, json=["Pytest"])
    assert r.status_code == 400


def test_ten_nha_cung_cap_cat_150_ky_tu(admin):
    ten = "Pytest NCC Dai " + _hau_to() + " " + "x" * 200
    r = admin.post(NCC, json={"ten_nha_cung_cap": ten})
    assert r.status_code == 201
    assert r.get_json()["data"]["TenNhaCungCap"] == ten[:150]


def test_danh_sach_nha_cung_cap_loc_va_phan_trang(admin):
    nhan = f"Loc{_hau_to()}"
    ids = [tao_ncc_sql(f"{nhan} {i}") for i in range(3)]
    dung = tao_ncc_sql(f"{nhan} dung", dang_hop_tac=False)
    nl = tao_nl("ds")
    tao_phieu(admin, ids[0], [dong(nl, 1, 10)])
    tao_phieu(admin, ids[0], [dong(nl, 1, 10)])

    r = admin.get(f"{NCC}?q=NCC {nhan}")
    assert r.status_code == 200
    p = r.get_json()["data"]
    assert p["total"] == 4 and p["page"] == 1 and p["per_page"] == 20 and len(p["items"]) == 4
    so_phieu = {i["NhaCungCapID"]: i["SoPhieuNhap"] for i in p["items"]}
    assert so_phieu[ids[0]] == 2 and so_phieu[ids[1]] == 0

    r = admin.get(f"{NCC}?q=NCC {nhan}&status=active")
    assert r.get_json()["data"]["total"] == 3
    r = admin.get(f"{NCC}?q=NCC {nhan}&status=inactive")
    p = r.get_json()["data"]
    assert p["total"] == 1 and p["items"][0]["NhaCungCapID"] == dung

    r = admin.get(f"{NCC}?q=NCC {nhan}&page=2&per_page=3")
    p = r.get_json()["data"]
    assert p["total"] == 4 and p["page"] == 2 and p["per_page"] == 3 and len(p["items"]) == 1

    assert admin.get(f"{NCC}?status=khac").status_code == 400
    # Ky tu dac biet cua LIKE duoc thoat: '%' khong khop tat ca
    assert admin.get(f"{NCC}?q=%25%25%25Pytest").get_json()["data"]["total"] == 0
    # per_page/page rac khong gay loi
    assert admin.get(f"{NCC}?page=abc&per_page=xyz").status_code == 200
    assert admin.get(f"{NCC}?per_page=100000").get_json()["data"]["per_page"] == 100


def test_chi_tiet_nha_cung_cap_tong_hop_phieu(admin):
    ncc = tao_ncc_sql("ct")
    nl = tao_nl("ct")
    tao_phieu(admin, ncc, [dong(nl, 1, 100)])                       # NHAP: khong tinh vao da nhan
    p2 = tao_phieu(admin, ncc, [dong(nl, 2, "100.25")])             # 200.50
    xac_nhan(admin, p2["PhieuNhapID"])
    p3 = tao_phieu(admin, ncc, [dong(nl, 1, 999)])
    huy(admin, p3["PhieuNhapID"])                                    # DA_HUY: khong tinh
    p4 = tao_phieu(admin, ncc, [dong(nl, 1, 555)])
    xac_nhan(admin, p4["PhieuNhapID"])
    huy(admin, p4["PhieuNhapID"])                                    # DA_NHAN roi huy: khong tinh

    r = admin.get(f"{NCC}/{ncc}")
    assert r.status_code == 200
    n = r.get_json()["data"]
    assert n["NhaCungCapID"] == ncc and n["TrangThai"] is True
    assert n["TongSoPhieu"] == 4 and n["SoPhieuNhap"] == 4
    assert d(n["TongTienDaNhan"]) == d("200.50")
    assert [x["PhieuNhapID"] for x in n["PhieuGanNhat"]] == sorted(
        (x["PhieuNhapID"] for x in n["PhieuGanNhat"]), reverse=True)
    assert len(n["PhieuGanNhat"]) == 4

    assert admin.get(f"{NCC}/999999").status_code == 404


def test_chi_tiet_nha_cung_cap_chi_10_phieu_gan_nhat(admin):
    ncc = tao_ncc_sql("muoi")
    nl = tao_nl("muoi")
    ids = [tao_phieu(admin, ncc, [dong(nl, 1, 1)])["PhieuNhapID"] for _ in range(12)]
    n = admin.get(f"{NCC}/{ncc}").get_json()["data"]
    assert n["TongSoPhieu"] == 12
    assert [x["PhieuNhapID"] for x in n["PhieuGanNhat"]] == sorted(ids, reverse=True)[:10]


def test_cap_nhat_nha_cung_cap(admin):
    ncc = tao_ncc_sql("sua")
    khac = tao_ncc_sql("khac")
    ten_khac = _mot("SELECT TenNhaCungCap FROM dbo.NhaCungCap WHERE NhaCungCapID = ?", khac)[0]

    assert admin.put(f"{NCC}/{ncc}", json={}).status_code == 400
    r = admin.put(f"{NCC}/{ncc}", json={})
    assert r.get_json()["message"] == "Khong co gi de cap nhat"
    assert admin.put(f"{NCC}/{ncc}", json={"khong_phai_truong": 1}).status_code == 400

    ten_moi = f"Pytest NCC Moi {_hau_to()}"
    r = admin.put(f"{NCC}/{ncc}", json={
        "ten_nha_cung_cap": ten_moi, "so_dien_thoai": "0912345678", "email": "x@y.vn", "dia_chi": "HN"})
    assert r.status_code == 200, r.get_json()
    n = r.get_json()["data"]
    assert (n["TenNhaCungCap"], n["SoDienThoai"], n["Email"], n["DiaChi"]) == (ten_moi, "0912345678", "x@y.vn", "HN")
    assert n["NgayCapNhat"] is not None

    # Chi doi 1 truong thi cac truong khac giu nguyen; xoa bang null
    r = admin.put(f"{NCC}/{ncc}", json={"so_dien_thoai": None})
    n = r.get_json()["data"]
    assert n["SoDienThoai"] is None and n["Email"] == "x@y.vn" and n["TenNhaCungCap"] == ten_moi

    # trang_thai nam o API nay (ngung / mo lai hop tac)
    r = admin.put(f"{NCC}/{ncc}", json={"trang_thai": False})
    assert r.status_code == 200 and r.get_json()["data"]["TrangThai"] is False
    assert admin.get(f"{NCC}?q={ten_moi}&status=inactive").get_json()["data"]["total"] == 1
    r = admin.put(f"{NCC}/{ncc}", json={"trang_thai": True})
    assert r.get_json()["data"]["TrangThai"] is True

    # Du lieu sai / trung ten / khong ton tai
    assert admin.put(f"{NCC}/{ncc}", json={"trang_thai": "yes"}).status_code == 400
    assert admin.put(f"{NCC}/{ncc}", json={"trang_thai": 1}).status_code == 400
    assert admin.put(f"{NCC}/{ncc}", json={"ten_nha_cung_cap": "  "}).status_code == 400
    assert admin.put(f"{NCC}/{ncc}", json={"email": "sai"}).status_code == 400
    assert admin.put(f"{NCC}/{ncc}", json={"so_dien_thoai": "12"}).status_code == 400
    r = admin.put(f"{NCC}/{ncc}", json={"ten_nha_cung_cap": ten_khac})
    assert r.status_code == 409 and r.get_json()["message"] == "Nha cung cap da ton tai"
    assert admin.put(f"{NCC}/999999", json={"dia_chi": "x"}).status_code == 404
    # Doi lai chinh ten minh thi khong bi coi la trung
    assert admin.put(f"{NCC}/{ncc}", json={"ten_nha_cung_cap": ten_moi}).status_code == 200


# =====================================================================
# 59. TAO PHIEU NHAP - tinh tien o backend
# =====================================================================
def test_tao_phieu_backend_tinh_tien_va_bo_qua_so_client(admin):
    ncc, nl1, nl2 = tao_ncc_sql("tien"), tao_nl("t1", "5"), tao_nl("t2", "7")
    r = admin.post(PN, json={
        "nha_cung_cap_id": ncc, "ghi_chu": "  Giao buoi sang  ",
        "tong_tien": 1, "TongTien": 1, "trang_thai": "DA_NHAN", "ma_phieu_nhap": "PN-GIA",
        "items": [
            {"nguyen_lieu_id": nl1, "so_luong": "2.5", "don_gia_nhap": "10000.50", "thanh_tien": 1, "ThanhTien": 1},
            {"nguyen_lieu_id": nl2, "so_luong": 3, "don_gia_nhap": 4000, "thanh_tien": 0.01},
        ]})
    assert r.status_code == 201, r.get_json()
    p = r.get_json()["data"]
    assert p["TrangThai"] == "NHAP"
    assert p["GhiChu"] == "Giao buoi sang"
    assert p["MaPhieuNhap"].startswith("PN") and "TMP" not in p["MaPhieuNhap"]
    assert p["MaPhieuNhap"].endswith(f"-{p['PhieuNhapID']:05d}") and len(p["MaPhieuNhap"]) == 2 + 6 + 1 + 5
    assert d(p["TongTien"]) == d("25001.25") + d("12000.00")
    ct = {c["NguyenLieuID"]: c for c in p["ChiTiet"]}
    assert d(ct[nl1]["ThanhTien"]) == d("25001.25") and d(ct[nl1]["SoLuong"]) == d("2.5")
    assert d(ct[nl2]["ThanhTien"]) == d("12000.00")
    assert p["NguoiXacNhan"] is None and p["NgayXacNhan"] is None and p["DuocSua"] is True
    assert p["NguoiLap"] == "Pytest Quan Tri" and p["TenNhaCungCap"]
    # Tao phieu KHONG dong vao ton kho
    assert ton(nl1) == 5 and ton(nl2) == 7
    assert so_lich_su_nl(nl1) == 0 and so_lich_su_nl(nl2) == 0


def test_lam_tron_half_up_hai_so_le(admin):
    ncc = tao_ncc_sql("tron")
    nl = [tao_nl(f"r{i}") for i in range(4)]
    p = tao_phieu(admin, ncc, [
        dong(nl[0], "0.5", "0.01"),            # 0.005 -> 0.01 (HALF_UP; banker's se ra 0.00)
        dong(nl[1], 2, "0.125"),               # don gia 0.125 -> 0.13, thanh tien 0.26
        dong(nl[2], "2.5", "19999.99"),        # 49999.975 -> 49999.98
        dong(nl[3], "0.333", "10.005"),        # don gia 10.01 -> 3.33333 -> 3.33
    ])
    ct = {c["NguyenLieuID"]: c for c in p["ChiTiet"]}
    assert d(ct[nl[0]]["ThanhTien"]) == d("0.01")
    assert d(ct[nl[1]]["DonGiaNhap"]) == d("0.13") and d(ct[nl[1]]["ThanhTien"]) == d("0.26")
    assert d(ct[nl[2]]["ThanhTien"]) == d("49999.98")
    assert d(ct[nl[3]]["DonGiaNhap"]) == d("10.01") and d(ct[nl[3]]["ThanhTien"]) == d("3.33")
    assert d(p["TongTien"]) == d("0.01") + d("0.26") + d("49999.98") + d("3.33")


def test_so_luong_ba_so_le_va_don_gia_bang_0(admin):
    ncc, nl = tao_ncc_sql("le"), tao_nl("le")
    p = tao_phieu(admin, ncc, [dong(nl, "0.0014", 0)])  # 0.0014 -> 0.001
    c = p["ChiTiet"][0]
    assert d(c["SoLuong"]) == d("0.001") and d(c["ThanhTien"]) == 0 and d(p["TongTien"]) == 0
    xac_nhan(admin, p["PhieuNhapID"])
    assert ton(nl) == d("0.001")


def test_gia_tri_toi_da_hop_le(admin):
    ncc, nl = tao_ncc_sql("max"), tao_nl("max")
    p = tao_phieu(admin, ncc, [dong(nl, 1000000, 1000000000)])
    assert d(p["TongTien"]) == d("1000000000000000.00")


@pytest.mark.parametrize("sai", [
    {"so_luong": 0}, {"so_luong": -1}, {"so_luong": "abc"}, {"so_luong": True}, {"so_luong": None},
    {"so_luong": ""}, {"so_luong": "NaN"}, {"so_luong": "Infinity"}, {"so_luong": 1000000.001},
    {"so_luong": "0.0004"},                                  # lam tron ve 0.000
    {"don_gia_nhap": -1}, {"don_gia_nhap": "abc"}, {"don_gia_nhap": True}, {"don_gia_nhap": None},
    {"don_gia_nhap": "NaN"}, {"don_gia_nhap": "Infinity"}, {"don_gia_nhap": 1000000000.01},
    {"nguyen_lieu_id": "abc"}, {"nguyen_lieu_id": 0}, {"nguyen_lieu_id": None}, {"nguyen_lieu_id": True},
])
def test_tao_phieu_dong_sai_400(admin, sai):
    ncc, nl = tao_ncc_sql("sai"), tao_nl("sai")
    dong_dung = dong(nl, 1, 1000)
    r = admin.post(PN, json={"nha_cung_cap_id": ncc, "items": [{**dong_dung, **sai}]})
    assert r.status_code == 400, (sai, r.get_json())
    assert _mot("SELECT COUNT(*) FROM dbo.PhieuNhap WHERE NhaCungCapID = ?", ncc)[0] == 0


@pytest.mark.parametrize("items", [None, [], {}, "abc", 5, [1], ["x"], [None]])
def test_tao_phieu_items_sai_400(admin, items):
    r = admin.post(PN, json={"nha_cung_cap_id": tao_ncc_sql("it"), "items": items})
    assert r.status_code == 400, r.get_json()


def test_tao_phieu_thieu_items_va_body_sai(admin):
    ncc = tao_ncc_sql("body")
    assert admin.post(PN, json={"nha_cung_cap_id": ncc}).status_code == 400
    assert admin.post(PN, data="rac", content_type="text/plain").status_code == 400
    assert admin.post(PN, json=[1, 2]).status_code == 400


@pytest.mark.parametrize("ncc_id, ma", [(None, 400), ("abc", 400), (0, 400), (-3, 400), (True, 400),
                                         (1.5, 400), (999999, 404)])
def test_tao_phieu_nha_cung_cap_sai(admin, ncc_id, ma):
    nl = tao_nl("nccsai")
    r = admin.post(PN, json={"nha_cung_cap_id": ncc_id, "items": [dong(nl, 1, 1)]})
    assert r.status_code == ma, r.get_json()


def test_tao_phieu_nguyen_lieu_khong_ton_tai_404(admin):
    ncc = tao_ncc_sql("nl404")
    r = admin.post(PN, json={"nha_cung_cap_id": ncc, "items": [dong(999999, 1, 1)]})
    assert r.status_code == 404
    assert _mot("SELECT COUNT(*) FROM dbo.PhieuNhap WHERE NhaCungCapID = ?", ncc)[0] == 0


def test_tao_phieu_nguyen_lieu_trung_dong_400(admin):
    ncc, nl = tao_ncc_sql("trung"), tao_nl("trung")
    r = admin.post(PN, json={"nha_cung_cap_id": ncc, "items": [dong(nl, 1, 10), dong(nl, 2, 20)]})
    assert r.status_code == 400
    assert "trung" in r.get_json()["message"]
    # Id dang chuoi van bi coi la trung
    r = admin.post(PN, json={"nha_cung_cap_id": ncc, "items": [dong(nl, 1, 10), dong(str(nl), 2, 20)]})
    assert r.status_code == 400
    assert _mot("SELECT COUNT(*) FROM dbo.PhieuNhap WHERE NhaCungCapID = ?", ncc)[0] == 0


def test_tao_phieu_nha_cung_cap_ngung_hop_tac_bi_tu_choi(admin):
    ncc, nl = tao_ncc_sql("ngung", dang_hop_tac=False), tao_nl("ngung")
    r = admin.post(PN, json={"nha_cung_cap_id": ncc, "items": [dong(nl, 1, 10)]})
    assert r.status_code == 400
    assert "ngung hop tac" in r.get_json()["message"]


def test_tao_phieu_nguyen_lieu_ngung_dung_bi_tu_choi(admin):
    ncc, ok_nl, ngung = tao_ncc_sql("nlng"), tao_nl("ok"), tao_nl("ngung", dang_dung=False)
    r = admin.post(PN, json={"nha_cung_cap_id": ncc, "items": [dong(ok_nl, 1, 10), dong(ngung, 1, 10)]})
    assert r.status_code == 400
    assert "ngung su dung" in r.get_json()["message"]
    assert _mot("SELECT COUNT(*) FROM dbo.PhieuNhap WHERE NhaCungCapID = ?", ncc)[0] == 0


def test_tao_phieu_toi_da_100_dong(admin):
    ncc = tao_ncc_sql("100")
    nls = [tao_nl(f"n{i}") for i in range(100)]
    p = tao_phieu(admin, ncc, [dong(n, 1, 1) for n in nls])
    assert len(p["ChiTiet"]) == 100 and d(p["TongTien"]) == 100
    # 101 dong -> 400 (id gia cung bi chan truoc khi cham CSDL)
    r = admin.post(PN, json={"nha_cung_cap_id": ncc, "items": [dong(i, 1, 1) for i in range(1, 102)]})
    assert r.status_code == 400 and "100" in r.get_json()["message"]


def test_tao_phieu_tong_tien_vuot_gioi_han_400(admin):
    ncc = tao_ncc_sql("tong")
    # 10 dong x 1e15 = 1e16 > DECIMAL(18,2); bi chan truoc khi cham CSDL
    items = [dong(i, 1000000, 1000000000) for i in range(1, 11)]
    r = admin.post(PN, json={"nha_cung_cap_id": ncc, "items": items})
    assert r.status_code == 400


def test_ghi_chu_phieu_cat_500_ky_tu(admin):
    ncc, nl = tao_ncc_sql("gc"), tao_nl("gc")
    p = tao_phieu(admin, ncc, [dong(nl, 1, 1)], ghi_chu="g" * 700)
    assert p["GhiChu"] == "g" * 500
    r = admin.post(PN, json={"nha_cung_cap_id": ncc, "items": [dong(nl, 1, 1)], "ghi_chu": 5})
    assert r.status_code == 400


# =====================================================================
# 58, 60. DANH SACH, CHI TIET PHIEU NHAP
# =====================================================================
def test_chi_tiet_phieu_nhap(admin):
    ncc, nl = tao_ncc_sql("ctp"), tao_nl("ctp")
    p = tao_phieu(admin, ncc, [dong(nl, 4, 2500)])
    r = admin.get(f"{PN}/{p['PhieuNhapID']}")
    assert r.status_code == 200
    g = r.get_json()["data"]
    assert g["PhieuNhapID"] == p["PhieuNhapID"] and g["TrangThai"] == "NHAP" and g["DuocSua"] is True
    assert g["NguoiLap"] == "Pytest Quan Tri" and g["NguoiXacNhan"] is None
    c = g["ChiTiet"][0]
    assert c["TenNguyenLieu"].startswith("Pytest NL") and c["DonViTinh"] == "kg"
    assert d(c["SoLuong"]) == 4 and d(c["DonGiaNhap"]) == 2500 and d(c["ThanhTien"]) == 10000
    assert admin.get(f"{PN}/999999").status_code == 404


def test_chi_tiet_phieu_sau_xac_nhan_khong_con_duoc_sua(admin, quan_ly):
    ncc, nl = tao_ncc_sql("ctx"), tao_nl("ctx")
    p = tao_phieu(admin, ncc, [dong(nl, 1, 10)])
    xac_nhan(quan_ly, p["PhieuNhapID"])
    g = admin.get(f"{PN}/{p['PhieuNhapID']}").get_json()["data"]
    assert g["TrangThai"] == "DA_NHAN" and g["DuocSua"] is False
    assert g["NguoiXacNhan"] == "Pytest Quan Ly Nhap" and g["NgayXacNhan"]
    assert g["NguoiLap"] == "Pytest Quan Tri"


def test_danh_sach_phieu_nhap_loc_va_phan_trang(admin, quan_ly):
    ncc_a, ncc_b = tao_ncc_sql("la"), tao_ncc_sql("lb")
    nl = tao_nl("ds")
    p1 = tao_phieu(admin, ncc_a, [dong(nl, 1, 10), dong(tao_nl("ds2"), 1, 10)])
    p2 = tao_phieu(admin, ncc_a, [dong(nl, 1, 10)])
    p3 = tao_phieu(admin, ncc_a, [dong(nl, 1, 10)])
    xac_nhan(admin, p2["PhieuNhapID"])
    huy(admin, p3["PhieuNhapID"])
    pb = tao_phieu(admin, ncc_b, [dong(nl, 1, 10)])

    r = admin.get(f"{PN}?nha_cung_cap_id={ncc_a}")
    assert r.status_code == 200
    p = r.get_json()["data"]
    assert p["total"] == 3 and p["page"] == 1 and p["per_page"] == 20
    ids = [i["PhieuNhapID"] for i in p["items"]]
    assert ids == sorted(ids, reverse=True)  # moi nhat truoc
    dau = next(i for i in p["items"] if i["PhieuNhapID"] == p1["PhieuNhapID"])
    assert dau["SoDong"] == 2 and dau["TenNhaCungCap"].startswith("Pytest NCC")
    assert dau["NguoiLap"] == "Pytest Quan Tri" and "TongTien" in dau and "MaPhieuNhap" in dau

    for tt, mong_doi in (("NHAP", 1), ("DA_NHAN", 1), ("DA_HUY", 1), ("da_nhan", 1)):
        r = admin.get(f"{PN}?nha_cung_cap_id={ncc_a}&status={tt}")
        assert r.get_json()["data"]["total"] == mong_doi, tt

    r = admin.get(f"{PN}?q={p1['MaPhieuNhap']}")
    assert [i["PhieuNhapID"] for i in r.get_json()["data"]["items"]] == [p1["PhieuNhapID"]]
    r = admin.get(f"{PN}?nha_cung_cap_id={ncc_b}")
    assert [i["PhieuNhapID"] for i in r.get_json()["data"]["items"]] == [pb["PhieuNhapID"]]

    r = admin.get(f"{PN}?nha_cung_cap_id={ncc_a}&page=2&per_page=2")
    p = r.get_json()["data"]
    assert p["total"] == 3 and p["page"] == 2 and p["per_page"] == 2 and len(p["items"]) == 1


def test_danh_sach_phieu_nhap_loc_theo_ngay(admin):
    ncc, nl = tao_ncc_sql("ngay"), tao_nl("ngay")
    tao_phieu(admin, ncc, [dong(nl, 1, 1)])
    hom_nay = hom_nay_csdl()
    h = hom_nay.isoformat()
    mai = (hom_nay.fromordinal(hom_nay.toordinal() + 1)).isoformat()
    qua = (hom_nay.fromordinal(hom_nay.toordinal() - 1)).isoformat()

    def tong(query):
        r = admin.get(f"{PN}?nha_cung_cap_id={ncc}&{query}")
        assert r.status_code == 200, r.get_json()
        return r.get_json()["data"]["total"]

    assert tong(f"tu_ngay={h}&den_ngay={h}") == 1   # den_ngay bao gom ca ngay do
    assert tong(f"tu_ngay={h}") == 1
    assert tong(f"den_ngay={h}") == 1
    assert tong(f"tu_ngay={mai}") == 0
    assert tong(f"den_ngay={qua}") == 0
    assert tong(f"tu_ngay={qua}&den_ngay={mai}") == 1


@pytest.mark.parametrize("query", [
    "status=XYZ", "nha_cung_cap_id=abc", "nha_cung_cap_id=0", "tu_ngay=2025-13-45", "den_ngay=hom-nay",
    "tu_ngay=01/02/2025",
])
def test_danh_sach_phieu_nhap_tham_so_sai_400(admin, query):
    assert admin.get(f"{PN}?{query}").status_code == 400


# =====================================================================
# 61. SUA PHIEU NHAP
# =====================================================================
def test_sua_phieu_nhap_thay_items_tinh_lai_tien(admin):
    ncc1, ncc2 = tao_ncc_sql("s1"), tao_ncc_sql("s2")
    nl1, nl2, nl3 = tao_nl("s1", "3"), tao_nl("s2"), tao_nl("s3")
    p = tao_phieu(admin, ncc1, [dong(nl1, 1, 1000), dong(nl2, 2, 500)], ghi_chu="Ban dau")
    pid = p["PhieuNhapID"]
    assert d(p["TongTien"]) == 2000

    # Chi doi ghi chu: items va tien giu nguyen
    r = admin.put(f"{PN}/{pid}", json={"ghi_chu": "  Da doi  "})
    assert r.status_code == 200, r.get_json()
    g = r.get_json()["data"]
    assert g["GhiChu"] == "Da doi" and len(g["ChiTiet"]) == 2 and d(g["TongTien"]) == 2000
    assert g["NhaCungCapID"] == ncc1

    # Xoa ghi chu bang null
    assert admin.put(f"{PN}/{pid}", json={"ghi_chu": None}).get_json()["data"]["GhiChu"] is None

    # Thay ca danh sach + doi nha cung cap, bo qua so tien client gui
    r = admin.put(f"{PN}/{pid}", json={
        "nha_cung_cap_id": ncc2, "tong_tien": 1,
        "items": [dong(nl3, "2.5", "8000.10"), {**dong(nl1, 1, 100), "thanh_tien": 1}]})
    assert r.status_code == 200, r.get_json()
    g = r.get_json()["data"]
    assert g["NhaCungCapID"] == ncc2 and g["NgayCapNhat"] is not None
    assert {c["NguyenLieuID"] for c in g["ChiTiet"]} == {nl1, nl3}
    assert d(g["TongTien"]) == d("20000.25") + 100
    assert g["TrangThai"] == "NHAP" and g["MaPhieuNhap"] == p["MaPhieuNhap"]
    assert ton(nl1) == 3 and so_lich_su_nl(nl1) == 0  # sua phieu khong dong vao kho
    assert _mot("SELECT COUNT(*) FROM dbo.ChiTietPhieuNhap WHERE PhieuNhapID = ?", pid)[0] == 2


def test_sua_phieu_nhap_du_lieu_sai(admin):
    ncc, ncc_ngung = tao_ncc_sql("sd"), tao_ncc_sql("sdn", dang_hop_tac=False)
    nl, nl_ngung = tao_nl("sd"), tao_nl("sdn", dang_dung=False)
    p = tao_phieu(admin, ncc, [dong(nl, 1, 1000)])
    pid = p["PhieuNhapID"]
    url = f"{PN}/{pid}"

    r = admin.put(url, json={})
    assert r.status_code == 400 and r.get_json()["message"] == "Khong co gi de cap nhat"
    assert admin.put(url, json={"khong_phai_truong": 1}).status_code == 400
    assert admin.put(url, json={"items": []}).status_code == 400
    assert admin.put(url, json={"items": "abc"}).status_code == 400
    assert admin.put(url, json={"items": [dong(nl, 1, 1), dong(nl, 2, 2)]}).status_code == 400
    assert admin.put(url, json={"items": [dong(nl, 0, 1)]}).status_code == 400
    assert admin.put(url, json={"items": [dong(nl, 1, -1)]}).status_code == 400
    assert admin.put(url, json={"items": [dong(nl_ngung, 1, 1)]}).status_code == 400
    assert admin.put(url, json={"items": [dong(999999, 1, 1)]}).status_code == 404
    assert admin.put(url, json={"nha_cung_cap_id": "abc"}).status_code == 400
    assert admin.put(url, json={"nha_cung_cap_id": ncc_ngung}).status_code == 400
    assert admin.put(url, json={"nha_cung_cap_id": 999999}).status_code == 404
    assert admin.put(url, json={"ghi_chu": 5}).status_code == 400
    assert admin.put(f"{PN}/999999", json={"ghi_chu": "x"}).status_code == 404
    assert admin.put(url, data="rac", content_type="text/plain").status_code == 400

    # Moi lan sai deu giu nguyen phieu cu
    g = admin.get(url).get_json()["data"]
    assert g["NhaCungCapID"] == ncc and len(g["ChiTiet"]) == 1 and d(g["TongTien"]) == 1000


def test_sua_phieu_nhap_nha_cung_cap_hien_tai_da_ngung_van_sua_duoc_ghi_chu(admin):
    """Chi can kiem tra nha cung cap khi DOI sang nha cung cap khac."""
    ncc, nl = tao_ncc_sql("ngsau"), tao_nl("ngsau")
    p = tao_phieu(admin, ncc, [dong(nl, 1, 1)])
    _chay("UPDATE dbo.NhaCungCap SET TrangThai = 0 WHERE NhaCungCapID = ?", ncc)
    r = admin.put(f"{PN}/{p['PhieuNhapID']}", json={"ghi_chu": "van sua duoc"})
    assert r.status_code == 200


def test_sua_phieu_sau_xac_nhan_hoac_huy_409(admin):
    ncc, nl = tao_ncc_sql("s409"), tao_nl("s409")
    da_nhan = tao_phieu(admin, ncc, [dong(nl, 2, 100)])
    xac_nhan(admin, da_nhan["PhieuNhapID"])
    da_huy = tao_phieu(admin, ncc, [dong(nl, 2, 100)])
    huy(admin, da_huy["PhieuNhapID"])

    for p in (da_nhan, da_huy):
        for body in ({"ghi_chu": "x"}, {"items": [dong(nl, 9, 9)]}, {"nha_cung_cap_id": ncc}):
            r = admin.put(f"{PN}/{p['PhieuNhapID']}", json=body)
            assert r.status_code == 409, r.get_json()
            assert r.get_json()["message"] == "Phieu da xac nhan hoac da huy, khong the sua"
    g = admin.get(f"{PN}/{da_nhan['PhieuNhapID']}").get_json()["data"]
    assert d(g["TongTien"]) == 200 and g["GhiChu"] is None
    assert ton(nl) == 2


# =====================================================================
# 62. XAC NHAN PHIEU - cong ton dung 1 lan
# =====================================================================
def test_xac_nhan_cong_ton_va_ghi_so_cai(admin, quan_ly):
    ncc = tao_ncc_sql("xn")
    nl1, nl2 = tao_nl("x1", "5"), tao_nl("x2", "0.250")
    p = tao_phieu(admin, ncc, [dong(nl1, "2.5", 100), dong(nl2, 10, 50)])
    pid = p["PhieuNhapID"]

    g = xac_nhan(quan_ly, pid)
    assert g["TrangThai"] == "DA_NHAN" and g["DuocSua"] is False
    assert g["NgayXacNhan"] and g["NguoiXacNhan"] == "Pytest Quan Ly Nhap" and g["NguoiLap"] == "Pytest Quan Tri"
    assert ton(nl1) == d("7.5") and ton(nl2) == d("10.25")

    ls = lich_su(pid)
    assert len(ls) == 2
    theo_nl = {row.NguyenLieuID: row for row in ls}
    r1, r2 = theo_nl[nl1], theo_nl[nl2]
    assert (r1.LoaiGiaoDich, r1.PhieuNhapID) == ("NHAP_HANG", pid)
    assert (Decimal(r1.SoLuongThayDoi), Decimal(r1.SoLuongTruoc), Decimal(r1.SoLuongSau)) == (
        d("2.5"), d("5"), d("7.5"))
    assert (Decimal(r2.SoLuongThayDoi), Decimal(r2.SoLuongTruoc), Decimal(r2.SoLuongSau)) == (
        d("10"), d("0.25"), d("10.25"))
    assert r1.LyDo == f"Nhap hang theo phieu {p['MaPhieuNhap']}"
    tk = _mot("SELECT TaiKhoanXacNhanID FROM dbo.PhieuNhap WHERE PhieuNhapID = ?", pid)[0]
    assert tk == r1.TaiKhoanID == r2.TaiKhoanID
    # Ghi theo thu tu NguyenLieuID tang dan
    assert [row.NguyenLieuID for row in ls] == sorted(row.NguyenLieuID for row in ls)


def test_xac_nhan_hai_lan_chi_cong_mot_lan(admin):
    ncc, nl = tao_ncc_sql("2l"), tao_nl("2l", "1")
    p = tao_phieu(admin, ncc, [dong(nl, 4, 10)])
    xac_nhan(admin, p["PhieuNhapID"])
    r = admin.post(f"{PN}/{p['PhieuNhapID']}/confirm")
    assert r.status_code == 409, r.get_json()
    assert ton(nl) == 5 and len(lich_su(p["PhieuNhapID"])) == 1
    assert admin.post(f"{PN}/{p['PhieuNhapID']}/confirm").status_code == 409
    assert ton(nl) == 5


def test_xac_nhan_nhieu_phieu_cung_nguyen_lieu_cong_don(admin):
    ncc, nl = tao_ncc_sql("cd"), tao_nl("cd", "0")
    a = tao_phieu(admin, ncc, [dong(nl, 3, 10)])
    b = tao_phieu(admin, ncc, [dong(nl, 4, 10)])
    xac_nhan(admin, b["PhieuNhapID"])
    xac_nhan(admin, a["PhieuNhapID"])
    assert ton(nl) == 7
    sau_a = lich_su(a["PhieuNhapID"])[0]
    assert (Decimal(sau_a.SoLuongTruoc), Decimal(sau_a.SoLuongSau)) == (4, 7)


def test_xac_nhan_phieu_khong_ton_tai_hoac_da_huy(admin):
    ncc, nl = tao_ncc_sql("xh"), tao_nl("xh", "2")
    assert admin.post(f"{PN}/999999/confirm").status_code == 404
    p = tao_phieu(admin, ncc, [dong(nl, 5, 10)])
    huy(admin, p["PhieuNhapID"])
    r = admin.post(f"{PN}/{p['PhieuNhapID']}/confirm")
    assert r.status_code == 409
    assert ton(nl) == 2 and lich_su(p["PhieuNhapID"]) == []


def test_xac_nhan_nguyen_lieu_ngung_dung_giua_chung_409_khong_doi_ton(admin):
    ncc = tao_ncc_sql("ngn")
    a, b = tao_nl("a", "10"), tao_nl("b", "20")  # a co id nho hon: se duoc cong truoc
    assert a < b
    p = tao_phieu(admin, ncc, [dong(a, 1, 10), dong(b, 2, 10)])
    _chay("UPDATE dbo.NguyenLieu SET TrangThai = 0 WHERE NguyenLieuID = ?", b)
    r = admin.post(f"{PN}/{p['PhieuNhapID']}/confirm")
    assert r.status_code == 409, r.get_json()
    assert "ngung su dung" in r.get_json()["message"]
    # Toan bo hoac khong: dong a cung khong duoc cong
    assert ton(a) == 10 and ton(b) == 20
    assert lich_su(p["PhieuNhapID"]) == [] and trang_thai_phieu(p["PhieuNhapID"]) == "NHAP"
    # Bat lai thi xac nhan duoc
    _chay("UPDATE dbo.NguyenLieu SET TrangThai = 1 WHERE NguyenLieuID = ?", b)
    xac_nhan(admin, p["PhieuNhapID"])
    assert ton(a) == 11 and ton(b) == 22


def test_xac_nhan_van_duoc_khi_nha_cung_cap_da_ngung_hop_tac(admin):
    """Hang da ve thi van phai ghi nhan duoc du nha cung cap vua bi ngung."""
    ncc, nl = tao_ncc_sql("nccng"), tao_nl("nccng")
    p = tao_phieu(admin, ncc, [dong(nl, 3, 10)])
    _chay("UPDATE dbo.NhaCungCap SET TrangThai = 0 WHERE NhaCungCapID = ?", ncc)
    xac_nhan(admin, p["PhieuNhapID"])
    assert ton(nl) == 3


def _song_song(viec, tai_khoan):
    """Chay viec(client) dong thoi tren moi tai khoan (moi luong 1 client rieng). Tra ve list status."""
    n = len(tai_khoan)
    rao = threading.Barrier(n)
    ket_qua, loi = [None] * n, []

    def chay(i):
        try:
            c = dang_nhap(*tai_khoan[i])
            rao.wait(timeout=30)
            ket_qua[i] = viec(c).status_code
        except BaseException as e:  # noqa: BLE001 - day loi ve luong chinh
            loi.append(repr(e))
            rao.abort()

    luong = [threading.Thread(target=chay, args=(i,)) for i in range(n)]
    for t in luong:
        t.start()
    for t in luong:
        t.join(timeout=60)
    assert not loi, loi
    return ket_qua


@pytest.mark.parametrize("vong", range(3))
def test_xac_nhan_song_song_chi_mot_luong_thanh_cong(admin, vong):
    ncc, nl1, nl2 = tao_ncc_sql("ss"), tao_nl("ss1", "1"), tao_nl("ss2", "0")
    p = tao_phieu(admin, ncc, [dong(nl1, 5, 10), dong(nl2, "2.5", 10)])
    pid = p["PhieuNhapID"]
    tk = [(dl.ADMIN_EMAIL, dl.ADMIN_MK), (QL_EMAIL, QL_MK), (dl.ADMIN_EMAIL, dl.ADMIN_MK)]
    ma = _song_song(lambda c: c.post(f"{PN}/{pid}/confirm"), tk)
    assert sorted(ma) == [200, 409, 409], ma
    assert ton(nl1) == 6 and ton(nl2) == d("2.5")  # chi tang 1 lan
    assert len(lich_su(pid)) == 2 and trang_thai_phieu(pid) == "DA_NHAN"


def test_huy_song_song_phieu_da_nhan_chi_tru_mot_lan(admin):
    ncc, nl = tao_ncc_sql("hss"), tao_nl("hss", "10")
    p = tao_phieu(admin, ncc, [dong(nl, 4, 10)])
    pid = p["PhieuNhapID"]
    xac_nhan(admin, pid)
    assert ton(nl) == 14
    tk = [(dl.ADMIN_EMAIL, dl.ADMIN_MK), (QL_EMAIL, QL_MK)]
    ma = _song_song(lambda c: c.post(f"{PN}/{pid}/cancel", json={"ly_do": "Huy dong thoi"}), tk)
    assert sorted(ma) == [200, 409], ma
    assert ton(nl) == 10 and trang_thai_phieu(pid) == "DA_HUY"
    assert [r.LoaiGiaoDich for r in lich_su(pid)] == ["NHAP_HANG", "HUY_NHAP"]


def test_xac_nhan_va_sua_song_song_khong_lech_tien(admin):
    """Sua phieu va xac nhan cung luc: ton cong dung theo dong luc xac nhan, khong bao gio lech."""
    ncc, nl = tao_ncc_sql("sx"), tao_nl("sx", "0")
    p = tao_phieu(admin, ncc, [dong(nl, 1, 10)])
    pid = p["PhieuNhapID"]
    tk = [(dl.ADMIN_EMAIL, dl.ADMIN_MK), (QL_EMAIL, QL_MK)]
    rao = threading.Barrier(2)
    ket_qua, loi = {}, []

    def sua():
        try:
            c = dang_nhap(*tk[0])
            rao.wait(timeout=30)
            ket_qua["sua"] = c.put(f"{PN}/{pid}", json={"items": [dong(nl, 9, 10)]}).status_code
        except BaseException as e:  # noqa: BLE001
            loi.append(repr(e))
            rao.abort()

    def nhan():
        try:
            c = dang_nhap(*tk[1])
            rao.wait(timeout=30)
            ket_qua["nhan"] = c.post(f"{PN}/{pid}/confirm").status_code
        except BaseException as e:  # noqa: BLE001
            loi.append(repr(e))
            rao.abort()

    luong = [threading.Thread(target=sua), threading.Thread(target=nhan)]
    for t in luong:
        t.start()
    for t in luong:
        t.join(timeout=60)
    assert not loi, loi
    assert ket_qua["nhan"] == 200 and ket_qua["sua"] in (200, 409)
    so_cong = ton(nl)
    chi_tiet = _mot("SELECT SoLuong FROM dbo.ChiTietPhieuNhap WHERE PhieuNhapID = ?", pid)[0]
    assert so_cong == Decimal(chi_tiet)  # ton cong dung bang dong cuoi cung cua phieu


# =====================================================================
# 63. HUY PHIEU
# =====================================================================
def test_huy_phieu_nhap_khong_dong_ton(admin):
    ncc, nl = tao_ncc_sql("hn"), tao_nl("hn", "8")
    p = tao_phieu(admin, ncc, [dong(nl, 5, 10)])
    pid = p["PhieuNhapID"]

    # Ly do bat buoc
    for body in ({}, {"ly_do": ""}, {"ly_do": "   "}, {"ly_do": None}, {"ly_do": 5}):
        r = admin.post(f"{PN}/{pid}/cancel", json=body)
        assert r.status_code == 400, body
    assert admin.post(f"{PN}/{pid}/cancel", data="rac", content_type="text/plain").status_code == 400
    assert trang_thai_phieu(pid) == "NHAP"

    g = huy(admin, pid, "  Nha cung cap het hang  ")
    assert g["TrangThai"] == "DA_HUY" and g["LyDoHuy"] == "Nha cung cap het hang" and g["DuocSua"] is False
    assert ton(nl) == 8 and lich_su(pid) == []
    # Du lieu phieu van con (QD08)
    assert _mot("SELECT COUNT(*) FROM dbo.ChiTietPhieuNhap WHERE PhieuNhapID = ?", pid)[0] == 1
    assert admin.get(f"{PN}/{pid}").get_json()["data"]["TrangThai"] == "DA_HUY"


def test_huy_phieu_da_huy_409_va_phieu_khong_ton_tai_404(admin):
    ncc, nl = tao_ncc_sql("hh"), tao_nl("hh")
    p = tao_phieu(admin, ncc, [dong(nl, 1, 1)])
    huy(admin, p["PhieuNhapID"])
    r = admin.post(f"{PN}/{p['PhieuNhapID']}/cancel", json={"ly_do": "lai"})
    assert r.status_code == 409
    assert admin.post(f"{PN}/999999/cancel", json={"ly_do": "x"}).status_code == 404


def test_huy_phieu_da_nhan_tru_lai_ton(admin, quan_ly):
    ncc = tao_ncc_sql("hdn")
    a, b = tao_nl("a", "5"), tao_nl("b", "0")
    p = tao_phieu(admin, ncc, [dong(a, "2.5", 10), dong(b, 4, 10)])
    pid = p["PhieuNhapID"]
    xac_nhan(admin, pid)
    assert ton(a) == d("7.5") and ton(b) == 4

    g = huy(quan_ly, pid, "Giao nham hang")
    assert g["TrangThai"] == "DA_HUY" and g["LyDoHuy"] == "Giao nham hang"
    assert ton(a) == 5 and ton(b) == 0

    ls = lich_su(pid)
    assert [r.LoaiGiaoDich for r in ls] == ["NHAP_HANG", "NHAP_HANG", "HUY_NHAP", "HUY_NHAP"]
    huy_a = next(r for r in ls if r.LoaiGiaoDich == "HUY_NHAP" and r.NguyenLieuID == a)
    assert (Decimal(huy_a.SoLuongThayDoi), Decimal(huy_a.SoLuongTruoc), Decimal(huy_a.SoLuongSau)) == (
        d("-2.5"), d("7.5"), d("5"))
    assert huy_a.PhieuNhapID == pid and "Giao nham hang" in huy_a.LyDo
    # Huy xong khong xac nhan lai duoc va khong huy lan hai
    assert admin.post(f"{PN}/{pid}/confirm").status_code == 409
    assert admin.post(f"{PN}/{pid}/cancel", json={"ly_do": "lai"}).status_code == 409
    assert ton(a) == 5 and ton(b) == 0


def test_huy_phieu_da_nhan_khi_hang_da_dung_409_rollback_het(admin):
    ncc = tao_ncc_sql("hdd")
    a, b = tao_nl("a", "0"), tao_nl("b", "0")
    assert a < b
    p = tao_phieu(admin, ncc, [dong(a, 5, 10), dong(b, 6, 10)])
    pid = p["PhieuNhapID"]
    xac_nhan(admin, pid)
    assert ton(a) == 5 and ton(b) == 6
    so_dong_truoc = len(lich_su(pid))

    dat_ton(b, "2")  # hang b da dung bot (con 2 < 6 can tru lai)
    r = admin.post(f"{PN}/{pid}/cancel", json={"ly_do": "Huy sau khi dung"})
    assert r.status_code == 409, r.get_json()
    assert "Ton kho khong du" in r.get_json()["message"]
    # a duoc xu ly truoc nhung phai rollback: ton khong doi, khong them so cai, phieu van DA_NHAN
    assert ton(a) == 5 and ton(b) == 2
    assert len(lich_su(pid)) == so_dong_truoc
    assert trang_thai_phieu(pid) == "DA_NHAN"
    assert _mot("SELECT LyDoHuy FROM dbo.PhieuNhap WHERE PhieuNhapID = ?", pid)[0] is None

    dat_ton(b, "6")  # kho du lai thi huy duoc
    huy(admin, pid, "Huy lai")
    assert ton(a) == 0 and ton(b) == 0


# =====================================================================
# PHAN QUYEN
# =====================================================================
DANH_SACH_API = [
    ("get", "/suppliers", None),
    ("post", "/suppliers", {"ten_nha_cung_cap": "Pytest Khong Duoc Tao"}),
    ("get", "/suppliers/1", None),
    ("put", "/suppliers/1", {"dia_chi": "x"}),
    ("get", "/purchase-receipts", None),
    ("post", "/purchase-receipts", {"nha_cung_cap_id": 1, "items": []}),
    ("get", "/purchase-receipts/1", None),
    ("put", "/purchase-receipts/1", {"ghi_chu": "x"}),
    ("post", "/purchase-receipts/1/confirm", None),
    ("post", "/purchase-receipts/1/cancel", {"ly_do": "x"}),
]


@pytest.mark.parametrize("method, duong, body", DANH_SACH_API)
def test_chua_dang_nhap_401(method, duong, body):
    c = _APP.test_client()
    r = getattr(c, method)(f"{API}{duong}", **({"json": body} if body is not None else {}))
    assert r.status_code == 401, (duong, r.get_json())
    assert r.get_json()["success"] is False


@pytest.mark.parametrize("method, duong, body", DANH_SACH_API)
def test_nhan_vien_bi_chan_403_toan_bo_nhom_nha_cung_cap_va_phieu_nhap(nhan_vien, method, duong, body):
    r = getattr(nhan_vien, method)(f"{API}{duong}", **({"json": body} if body is not None else {}))
    assert r.status_code == 403, (duong, r.get_json())


def test_nhan_vien_bi_chan_khong_lam_thay_doi_du_lieu(admin, nhan_vien):
    ncc, nl = tao_ncc_sql("nv"), tao_nl("nv", "3")
    p = tao_phieu(admin, ncc, [dong(nl, 2, 10)])
    pid = p["PhieuNhapID"]
    ten = f"Pytest NCC Nv {_hau_to()}"
    assert nhan_vien.post(NCC, json={"ten_nha_cung_cap": ten}).status_code == 403
    assert _mot("SELECT COUNT(*) FROM dbo.NhaCungCap WHERE TenNhaCungCap = ?", ten)[0] == 0
    assert nhan_vien.post(PN, json={"nha_cung_cap_id": ncc, "items": [dong(nl, 1, 1)]}).status_code == 403
    assert nhan_vien.put(f"{PN}/{pid}", json={"ghi_chu": "hack"}).status_code == 403
    assert nhan_vien.post(f"{PN}/{pid}/confirm").status_code == 403
    assert nhan_vien.post(f"{PN}/{pid}/cancel", json={"ly_do": "x"}).status_code == 403
    assert trang_thai_phieu(pid) == "NHAP" and ton(nl) == 3
    assert _mot("SELECT COUNT(*) FROM dbo.PhieuNhap WHERE NhaCungCapID = ?", ncc)[0] == 1
    assert _mot("SELECT GhiChu FROM dbo.PhieuNhap WHERE PhieuNhapID = ?", pid)[0] is None


def test_quan_ly_lam_het_quy_trinh(quan_ly):
    r = quan_ly.post(NCC, json={"ten_nha_cung_cap": f"Pytest NCC Ql {_hau_to()}"})
    assert r.status_code == 201
    ncc = r.get_json()["data"]["NhaCungCapID"]
    assert quan_ly.get(NCC).status_code == 200 and quan_ly.get(f"{NCC}/{ncc}").status_code == 200
    assert quan_ly.put(f"{NCC}/{ncc}", json={"dia_chi": "HCM"}).status_code == 200
    nl = tao_nl("ql", "1")
    p = tao_phieu(quan_ly, ncc, [dong(nl, 2, 100)])
    assert p["NguoiLap"] == "Pytest Quan Ly Nhap"
    assert quan_ly.get(PN).status_code == 200 and quan_ly.get(f"{PN}/{p['PhieuNhapID']}").status_code == 200
    assert quan_ly.put(f"{PN}/{p['PhieuNhapID']}", json={"ghi_chu": "ok"}).status_code == 200
    xac_nhan(quan_ly, p["PhieuNhapID"])
    assert ton(nl) == 3
    huy(quan_ly, p["PhieuNhapID"])
    assert ton(nl) == 1


def test_vai_tro_khong_co_purchase_confirm(admin, han_che):
    """Co supplier.view + supplier.manage nhung thieu purchase.confirm."""
    ncc, nl = tao_ncc_sql("hc"), tao_nl("hc", "1")
    # Xem va quan ly nha cung cap / lap, sua phieu thi duoc
    assert han_che.get(NCC).status_code == 200
    assert han_che.get(PN).status_code == 200
    assert han_che.put(f"{NCC}/{ncc}", json={"dia_chi": "x"}).status_code == 200
    # Xac nhan can purchase.confirm -> 403, khong cong ton
    p = tao_phieu(admin, ncc, [dong(nl, 3, 10)])
    pid = p["PhieuNhapID"]
    assert han_che.put(f"{PN}/{pid}", json={"ghi_chu": "sua boi vai tro tam"}).status_code == 200
    assert han_che.post(f"{PN}/{pid}/confirm").status_code == 403
    assert trang_thai_phieu(pid) == "NHAP" and ton(nl) == 1 and lich_su(pid) == []

    # Phieu da nhan: huy can purchase.confirm -> 403 va khong tru ton
    xac_nhan(admin, pid)
    assert ton(nl) == 4
    r = han_che.post(f"{PN}/{pid}/cancel", json={"ly_do": "Thu huy"})
    assert r.status_code == 403, r.get_json()
    assert trang_thai_phieu(pid) == "DA_NHAN" and ton(nl) == 4 and len(lich_su(pid)) == 1

    # Phieu NHAP thi chi can supplier.manage
    p2 = tao_phieu(admin, ncc, [dong(nl, 1, 10)])
    huy(han_che, p2["PhieuNhapID"], "Huy phieu nhap")
    assert trang_thai_phieu(p2["PhieuNhapID"]) == "DA_HUY" and ton(nl) == 4

    # Nguoi co quyen thi huy duoc
    huy(admin, pid, "Admin huy")
    assert ton(nl) == 1


def test_phan_quyen_theo_nguoi_dung_co_quyen_view_nhung_khong_manage():
    """Vai tro tam #2 chi co supplier.view: xem duoc, moi thao tac ghi bi 403."""
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dbo.VaiTro (TenVaiTro, MoTa, NgayTao) OUTPUT INSERTED.VaiTroID "
            "VALUES (N'Pytest Chi Xem Nhap', N'Vai tro tam', SYSDATETIME())"
        )
        vt = cur.fetchval()
        cur.execute(
            "INSERT INTO dbo.VaiTroQuyen (VaiTroID, QuyenID) SELECT ?, QuyenID FROM dbo.Quyen "
            "WHERE TenQuyen = 'supplier.view'", (vt,))
        cur.execute(
            "INSERT INTO dbo.TaiKhoan (VaiTroID, HoTen, Email, MatKhauHash, TrangThai, NgayTao) "
            "VALUES (?, N'Pytest Chi Xem', 'pytest-chixem-nhap@test.local', ?, 'HOAT_DONG', SYSDATETIME())",
            (vt, generate_password_hash("chixem123")),
        )
        conn.commit()
    try:
        c = dang_nhap("pytest-chixem-nhap@test.local", "chixem123")
        assert c.get(NCC).status_code == 200 and c.get(PN).status_code == 200
        assert c.get(f"{NCC}/999999").status_code == 404  # co quyen xem nen toi duoc buoc tim kiem
        assert c.post(NCC, json={"ten_nha_cung_cap": "Pytest Chi Xem"}).status_code == 403
        assert c.put(f"{NCC}/1", json={"dia_chi": "x"}).status_code == 403
        assert c.post(PN, json={"nha_cung_cap_id": 1, "items": []}).status_code == 403
        assert c.put(f"{PN}/1", json={"ghi_chu": "x"}).status_code == 403
        assert c.post(f"{PN}/1/confirm").status_code == 403
        assert c.post(f"{PN}/1/cancel", json={"ly_do": "x"}).status_code == 403
    finally:
        with closing(get_connection()) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM dbo.TaiKhoan WHERE Email = 'pytest-chixem-nhap@test.local'")
            cur.execute(
                "DELETE FROM dbo.VaiTroQuyen WHERE VaiTroID IN "
                "(SELECT VaiTroID FROM dbo.VaiTro WHERE TenVaiTro = N'Pytest Chi Xem Nhap')")
            cur.execute("DELETE FROM dbo.VaiTro WHERE TenVaiTro = N'Pytest Chi Xem Nhap'")
            conn.commit()
