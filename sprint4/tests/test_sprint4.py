"""Kiem thu Sprint 4: promotions (64-70), reports (71-79), employees/shifts/workSchedules (80-90).

Ma khuyen mai test bat dau "PYTEST", ten nhan vien / ca bat dau "Pytest" -> conftest tu don.

Chay: py -3.12 -m pytest tests/test_sprint4.py -q
"""

import datetime
import uuid
from contextlib import closing
from decimal import Decimal

import pytest

from app import create_app
from database.connection import get_connection
from tests import du_lieu_test as dl

API = "/api/v1"
_APP = create_app()
_APP.config.update(TESTING=True)


@pytest.fixture()
def client():
    with _APP.test_client() as c:
        yield c


def login(client, email=dl.ADMIN_EMAIL, password=dl.ADMIN_MK):
    r = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.get_json()


@pytest.fixture()
def admin(client):
    login(client)
    return client


@pytest.fixture()
def nv():
    c = _APP.test_client()
    login(c, dl.NV_EMAIL, dl.NV_MK)
    return c


def _ma():
    return "PYTEST" + uuid.uuid4().hex[:8].upper()


def _chay(sql, *params):
    with closing(get_connection()) as conn:
        conn.cursor().execute(sql, params)
        conn.commit()


def _gio(delta_ngay=0):
    return (datetime.datetime.now() + datetime.timedelta(days=delta_ngay)).strftime("%Y-%m-%dT%H:%M")


def tao_km(c, **kw):
    body = {
        "ma_khuyen_mai": _ma(), "ten_khuyen_mai": "Pytest giam gia", "loai_giam_gia": "PHAN_TRAM",
        "gia_tri_giam": 10, "ngay_bat_dau": _gio(-1), "ngay_ket_thuc": _gio(7),
    }
    body.update(kw)
    r = c.post(f"{API}/promotions", json=body)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["data"]


def tao_don(c, items=None, **kw):
    items = items or [{"mon_id": dl.MON_ID, "so_luong": 2}, {"mon_id": dl.MON2_ID, "so_luong": 1}]  # 45.000
    r = c.post(f"{API}/orders", json={"items": items, **kw})
    return r


def thu_tien(c, don):
    r = c.post(f"{API}/payments", json={"don_hang_id": don["DonHangID"], "phuong_thuc": "TIEN_MAT",
                                        "so_tien": float(don["ThanhTien"])})
    assert r.status_code == 201, r.get_json()
    r = c.post(f"{API}/payments/{r.get_json()['data']['ThanhToanID']}/confirm", json={})
    assert r.status_code == 200, r.get_json()
    return r.get_json()["data"]


# =====================================================================
# Khuyen mai
# =====================================================================
def test_tao_xem_sua_bat_tat_khuyen_mai(admin):
    km = tao_km(admin, ma_khuyen_mai="  " + _ma().lower() + " ")
    assert km["MaKhuyenMai"].startswith("PYTEST") and km["MaKhuyenMai"] == km["MaKhuyenMai"].upper()
    assert km["TinhTrang"] == "DANG_DIEN_RA" and km["SoLuotDaDung"] == 0
    km_id = km["KhuyenMaiID"]

    r = admin.get(f"{API}/promotions/{km_id}")
    assert r.status_code == 200 and r.get_json()["data"]["TenKhuyenMai"] == "Pytest giam gia"

    r = admin.put(f"{API}/promotions/{km_id}", json={"ten_khuyen_mai": "Pytest doi ten", "giam_toi_da": 5000})
    assert r.status_code == 200, r.get_json()
    d = r.get_json()["data"]
    assert d["TenKhuyenMai"] == "Pytest doi ten" and float(d["GiamToiDa"]) == 5000
    assert float(d["GiaTriGiam"]) == 10  # truong khong gui giu nguyen

    r = admin.patch(f"{API}/promotions/{km_id}/status", json={"trang_thai": False})
    assert r.status_code == 200 and r.get_json()["data"]["TinhTrang"] == "DA_TAT"
    r = admin.get(f"{API}/promotions?status=DA_TAT&q={km['MaKhuyenMai']}")
    assert [x["KhuyenMaiID"] for x in r.get_json()["data"]["items"]] == [km_id]
    assert admin.patch(f"{API}/promotions/{km_id}/status", json={"trang_thai": "off"}).status_code == 400
    assert admin.get(f"{API}/promotions/999999999").status_code == 404


@pytest.mark.parametrize("sai, loi", [
    ({"ma_khuyen_mai": "a b"}, "ma khuyen mai"),
    ({"ten_khuyen_mai": "  "}, "ten khuyen mai"),
    ({"loai_giam_gia": "TANG_QUA"}, "loai giam gia"),
    ({"gia_tri_giam": 0}, "gia tri giam"),
    ({"gia_tri_giam": 101}, "phan tram"),
    ({"ngay_ket_thuc": _gio(-2)}, "ngay ket thuc"),
    ({"ngay_bat_dau": "hom qua"}, "thoi gian"),
    ({"so_luong_su_dung": 0}, "so luot"),
    ({"don_hang_toi_thieu": -1}, "toi thieu"),
])
def test_khuyen_mai_du_lieu_sai(admin, sai, loi):
    body = {"ma_khuyen_mai": _ma(), "ten_khuyen_mai": "Pytest", "loai_giam_gia": "PHAN_TRAM",
            "gia_tri_giam": 10, "ngay_bat_dau": _gio(-1), "ngay_ket_thuc": _gio(1), **sai}
    r = admin.post(f"{API}/promotions", json=body)
    assert r.status_code == 400 and loi in r.get_json()["message"].lower()


def test_ma_khuyen_mai_khong_trung(admin):
    km = tao_km(admin)
    r = admin.post(f"{API}/promotions", json={
        "ma_khuyen_mai": km["MaKhuyenMai"], "ten_khuyen_mai": "Pytest", "loai_giam_gia": "SO_TIEN",
        "gia_tri_giam": 1000, "ngay_bat_dau": _gio(-1), "ngay_ket_thuc": _gio(1)})
    assert r.status_code == 409 and "da ton tai" in r.get_json()["message"]


def test_ap_ma_phan_tram_co_tran_vao_don_va_hoa_don(admin):
    km = tao_km(admin, gia_tri_giam=20, giam_toi_da=5000)
    r = tao_don(admin, ma_khuyen_mai=km["MaKhuyenMai"].lower())
    assert r.status_code == 201, r.get_json()
    don = r.get_json()["data"]
    # 45.000 x 20% = 9.000 nhung tran 5.000
    assert float(don["TongTien"]) == 45000 and float(don["GiamGia"]) == 5000
    assert float(don["ThanhTien"]) == 40000 and don["MaKhuyenMai"] == km["MaKhuyenMai"]

    kq = thu_tien(admin, don)
    assert float(kq["HoaDon"]["GiamGia"]) == 5000 and float(kq["HoaDon"]["ThanhTien"]) == 40000

    r = admin.get(f"{API}/promotions/{km['KhuyenMaiID']}/usage")
    u = r.get_json()["data"]
    assert u["SoLuot"] == 1 and float(u["TongGiam"]) == 5000
    assert u["items"][0]["MaDonHang"] == don["MaDonHang"]


def test_so_tien_giam_khong_qua_tong_va_tinh_lai_khi_doi_mon(admin):
    km = tao_km(admin, loai_giam_gia="SO_TIEN", gia_tri_giam=100000)
    don = tao_don(admin, [{"mon_id": dl.MON_ID, "so_luong": 1}], ma_khuyen_mai=km["MaKhuyenMai"]).get_json()["data"]
    assert float(don["GiamGia"]) == 10000 and float(don["ThanhTien"]) == 0

    km2 = tao_km(admin, gia_tri_giam=10)
    r = admin.put(f"{API}/orders/{don['DonHangID']}/items", json={
        "items": [{"chi_tiet_id": don["ChiTiet"][0]["ChiTietDonHangID"], "mon_id": dl.MON_ID, "so_luong": 3}],
        "ma_khuyen_mai": km2["MaKhuyenMai"]})
    assert r.status_code == 200, r.get_json()
    d = r.get_json()["data"]
    assert float(d["TongTien"]) == 30000 and float(d["GiamGia"]) == 3000 and d["MaKhuyenMai"] == km2["MaKhuyenMai"]

    # Them mon (khong gui ma) -> giu ma, tinh lai giam
    r = admin.post(f"{API}/orders/{don['DonHangID']}/items", json={"mon_id": dl.MON2_ID, "so_luong": 1})
    d = r.get_json()["data"]
    assert float(d["TongTien"]) == 55000 and float(d["GiamGia"]) == 5500

    # Gui ma rong -> go ma
    r = admin.put(f"{API}/orders/{don['DonHangID']}/items", json={
        "items": [{"chi_tiet_id": c["ChiTietDonHangID"], "mon_id": c["MonID"], "so_luong": c["SoLuong"]}
                  for c in d["ChiTiet"]], "ma_khuyen_mai": ""})
    d = r.get_json()["data"]
    assert float(d["GiamGia"]) == 0 and float(d["ThanhTien"]) == 55000 and d["MaKhuyenMai"] is None


def test_don_toi_thieu_va_tu_go_khi_duoi_muc(admin):
    km = tao_km(admin, gia_tri_giam=10, don_hang_toi_thieu=40000)
    r = tao_don(admin, [{"mon_id": dl.MON_ID, "so_luong": 1}], ma_khuyen_mai=km["MaKhuyenMai"])
    assert r.status_code == 409 and "toi thieu" in r.get_json()["message"]

    don = tao_don(admin, ma_khuyen_mai=km["MaKhuyenMai"]).get_json()["data"]
    assert float(don["GiamGia"]) == 4500
    xoa = next(c for c in don["ChiTiet"] if c["MonID"] == dl.MON2_ID)
    r = admin.delete(f"{API}/orders/{don['DonHangID']}/items/{xoa['ChiTietDonHangID']}")
    d = r.get_json()["data"]
    assert float(d["TongTien"]) == 20000 and float(d["GiamGia"]) == 0 and d["MaKhuyenMai"] is None


@pytest.mark.parametrize("kw, loi", [
    ({"ngay_bat_dau": _gio(1), "ngay_ket_thuc": _gio(3)}, "chua den"),
    ({"ngay_bat_dau": _gio(-5), "ngay_ket_thuc": _gio(-1)}, "het han"),
])
def test_ma_ngoai_thoi_gian(admin, kw, loi):
    km = tao_km(admin, **kw)
    r = tao_don(admin, ma_khuyen_mai=km["MaKhuyenMai"])
    assert r.status_code == 409 and loi in r.get_json()["message"]


def test_ma_tat_va_ma_khong_ton_tai(admin):
    km = tao_km(admin, trang_thai=False)
    r = tao_don(admin, ma_khuyen_mai=km["MaKhuyenMai"])
    assert r.status_code == 409 and "tam tat" in r.get_json()["message"]
    r = tao_don(admin, ma_khuyen_mai="PYTESTKHONGCO")
    assert r.status_code == 404
    # Loi ma -> khong tao don do dang
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM dbo.DonHang WHERE MaDonHang LIKE 'TMP%'")
        assert cur.fetchval() == 0


def test_het_luot_va_don_huy_tra_lai_luot(admin):
    km = tao_km(admin, so_luong_su_dung=1)
    don = tao_don(admin, ma_khuyen_mai=km["MaKhuyenMai"]).get_json()["data"]
    r = tao_don(admin, ma_khuyen_mai=km["MaKhuyenMai"])
    assert r.status_code == 409 and "het luot" in r.get_json()["message"]
    assert admin.get(f"{API}/promotions/{km['KhuyenMaiID']}").get_json()["data"]["TinhTrang"] == "HET_LUOT"

    # Khong giam so luot duoi so da dung
    r = admin.put(f"{API}/promotions/{km['KhuyenMaiID']}", json={"so_luong_su_dung": 0})
    assert r.status_code == 400

    assert admin.post(f"{API}/orders/{don['DonHangID']}/cancel", json={"ly_do": "Pytest"}).status_code == 200
    r = tao_don(admin, ma_khuyen_mai=km["MaKhuyenMai"])
    assert r.status_code == 201, r.get_json()


def test_khong_doi_ma_khi_da_dung(admin):
    km = tao_km(admin)
    tao_don(admin, ma_khuyen_mai=km["MaKhuyenMai"])
    r = admin.put(f"{API}/promotions/{km['KhuyenMaiID']}", json={"ma_khuyen_mai": _ma()})
    assert r.status_code == 409


def test_kiem_tra_ma_cho_gio_hang_va_don(admin, nv):
    km = tao_km(admin, gia_tri_giam=10)
    # Nhan vien ban hang kiem tra duoc ma; gia client gui bi bo qua.
    r = nv.post(f"{API}/promotions/validate", json={
        "ma_khuyen_mai": km["MaKhuyenMai"], "items": [{"mon_id": dl.MON2_ID, "so_luong": 2, "don_gia": 1}]})
    assert r.status_code == 200, r.get_json()
    d = r.get_json()["data"]
    assert float(d["TongTien"]) == 50000 and float(d["SoTienGiam"]) == 5000 and float(d["ThanhTien"]) == 45000

    don = tao_don(admin).get_json()["data"]
    r = admin.post(f"{API}/promotions/validate", json={"ma_khuyen_mai": km["MaKhuyenMai"],
                                                       "don_hang_id": don["DonHangID"]})
    assert float(r.get_json()["data"]["SoTienGiam"]) == 4500
    assert admin.post(f"{API}/promotions/validate", json={"ma_khuyen_mai": "PYTESTKHONGCO",
                                                          "items": [{"mon_id": dl.MON_ID}]}).status_code == 404
    assert admin.post(f"{API}/promotions/validate", json={"ma_khuyen_mai": km["MaKhuyenMai"]}).status_code == 400


def test_phan_quyen_khuyen_mai(nv):
    assert nv.get(f"{API}/promotions").status_code == 403
    assert nv.post(f"{API}/promotions", json={}).status_code == 403
    c = _APP.test_client()
    assert c.get(f"{API}/promotions").status_code == 401


# =====================================================================
# Bao cao
# =====================================================================
DS_BAO_CAO = ["revenue", "orders", "top-products", "payments", "refunds", "inventory",
              "purchases", "promotions", "overview"]


@pytest.mark.parametrize("ten", DS_BAO_CAO)
def test_bao_cao_mo_duoc_va_kiem_ngay(admin, nv, ten):
    r = admin.get(f"{API}/reports/{ten}")
    assert r.status_code == 200, r.get_json()
    assert "TuNgay" in r.get_json()["data"]
    assert admin.get(f"{API}/reports/{ten}?tu_ngay=2026-13-01").status_code == 400
    assert admin.get(f"{API}/reports/{ten}?tu_ngay=2026-10-10&den_ngay=2026-10-01").status_code == 400
    assert admin.get(f"{API}/reports/{ten}?tu_ngay=2024-01-01&den_ngay=2026-01-01").status_code == 400
    assert nv.get(f"{API}/reports/{ten}").status_code == 403


def test_bao_cao_doanh_thu_mon_ban_chay_khuyen_mai(admin):
    hom_nay = datetime.date.today().isoformat()
    q = f"?tu_ngay={hom_nay}&den_ngay={hom_nay}"
    truoc = admin.get(f"{API}/reports/overview{q}").get_json()["data"]
    km = tao_km(admin, loai_giam_gia="SO_TIEN", gia_tri_giam=5000)
    don = tao_don(admin, [{"mon_id": dl.MON2_ID, "so_luong": 4}], ma_khuyen_mai=km["MaKhuyenMai"]).get_json()["data"]
    thu_tien(admin, don)  # thu 95.000

    sau = admin.get(f"{API}/reports/overview{q}").get_json()["data"]
    assert Decimal(str(sau["DoanhThu"])) - Decimal(str(truoc["DoanhThu"])) == 95000
    assert sau["SoDonDaThu"] == truoc["SoDonDaThu"] + 1

    dt = admin.get(f"{API}/reports/revenue{q}").get_json()["data"]
    assert len(dt["TheoKy"]) == 1 and Decimal(str(dt["TheoKy"][0]["DoanhThu"])) == Decimal(str(sau["DoanhThu"]))

    top = admin.get(f"{API}/reports/top-products{q}&limit=50").get_json()["data"]["items"]
    assert any(m["MonID"] == dl.MON2_ID and m["SoLuong"] >= 4 for m in top)

    kmr = admin.get(f"{API}/reports/promotions{q}").get_json()["data"]["items"]
    dong = next(x for x in kmr if x["KhuyenMaiID"] == km["KhuyenMaiID"])
    assert dong["SoLuot"] == 1 and float(dong["TongGiam"]) == 5000

    thang = admin.get(f"{API}/reports/revenue?tu_ngay=2026-01-01&den_ngay=2026-03-31&group_by=month").get_json()["data"]
    assert len(thang["TheoKy"]) == 3
    assert admin.get(f"{API}/reports/revenue?group_by=year").status_code == 400


# =====================================================================
# Nhan vien, ca, lich
# =====================================================================
def tao_nv(c, **kw):
    r = c.post(f"{API}/employees", json={"ho_ten": "Pytest Nhan Su " + uuid.uuid4().hex[:6], **kw})
    assert r.status_code == 201, r.get_json()
    return r.get_json()["data"]


def tao_ca(c, bat_dau, ket_thuc):
    r = c.post(f"{API}/shifts", json={"ten_ca": "Pytest Ca " + uuid.uuid4().hex[:6],
                                      "gio_bat_dau": bat_dau, "gio_ket_thuc": ket_thuc})
    assert r.status_code == 201, r.get_json()
    return r.get_json()["data"]


def _ngay(n=1):
    return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()


def test_ho_so_nhan_vien(admin):
    nv = tao_nv(admin, so_dien_thoai="0901234567", chuc_vu="Pha chế", ngay_vao_lam="2026-01-15")
    assert nv["MaNhanVien"].startswith("NV") and nv["TrangThai"] == "DANG_LAM"
    r = admin.put(f"{API}/employees/{nv['NhanVienID']}", json={"chuc_vu": "Thu ngân"})
    d = r.get_json()["data"]
    assert d["ChucVu"] == "Thu ngân" and d["SoDienThoai"] == "0901234567"
    assert admin.put(f"{API}/employees/{nv['NhanVienID']}", json={"so_dien_thoai": "abc"}).status_code == 400
    assert admin.post(f"{API}/employees", json={"ho_ten": " "}).status_code == 400
    r = admin.post(f"{API}/employees", json={"ho_ten": "Pytest trung ma", "ma_nhan_vien": nv["MaNhanVien"]})
    assert r.status_code == 409

    r = admin.get(f"{API}/employees?q={nv['MaNhanVien']}")
    assert [x["NhanVienID"] for x in r.get_json()["data"]["items"]] == [nv["NhanVienID"]]
    assert admin.get(f"{API}/employees/{nv['NhanVienID']}").get_json()["data"]["LichSapToi"] == []
    assert admin.get(f"{API}/employees/999999999").status_code == 404


def test_gan_tai_khoan_khong_trung(admin):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT TaiKhoanID FROM dbo.TaiKhoan WHERE Email = ?", (dl.ADMIN_EMAIL,))
        tk = cur.fetchval()
    a = tao_nv(admin, tai_khoan_id=tk)
    assert a["EmailTaiKhoan"] == dl.ADMIN_EMAIL
    r = admin.post(f"{API}/employees", json={"ho_ten": "Pytest B", "tai_khoan_id": tk})
    assert r.status_code == 409
    assert admin.post(f"{API}/employees", json={"ho_ten": "Pytest C", "tai_khoan_id": 999999999}).status_code == 404


def test_ca_lam_viec(admin):
    ca = tao_ca(admin, "22:00", "06:00")
    assert ca["QuaDem"] is True and ca["GioBatDau"] == "22:00"
    assert admin.post(f"{API}/shifts", json={"ten_ca": "Pytest X", "gio_bat_dau": "08:00",
                                             "gio_ket_thuc": "08:00"}).status_code == 400
    assert admin.post(f"{API}/shifts", json={"ten_ca": "Pytest X", "gio_bat_dau": "25:00",
                                             "gio_ket_thuc": "08:00"}).status_code == 400
    r = admin.post(f"{API}/shifts", json={"ten_ca": ca["TenCa"], "gio_bat_dau": "07:00", "gio_ket_thuc": "11:00"})
    assert r.status_code == 409
    r = admin.put(f"{API}/shifts/{ca['CaLamViecID']}", json={"gio_ket_thuc": "05:30", "trang_thai": False})
    d = r.get_json()["data"]
    assert d["GioKetThuc"] == "05:30" and d["TrangThai"] is False
    assert any(x["CaLamViecID"] == ca["CaLamViecID"] for x in admin.get(f"{API}/shifts?status=inactive").get_json()["data"])


def test_xep_lich_chong_trung_va_cham_cong(admin):
    nv = tao_nv(admin)
    sang = tao_ca(admin, "07:00", "12:00")
    chong = tao_ca(admin, "11:00", "15:00")
    chieu = tao_ca(admin, "12:00", "17:00")
    dem = tao_ca(admin, "22:00", "08:00")
    ngay = _ngay(2)

    r = admin.post(f"{API}/workSchedules", json={"nhan_vien_id": nv["NhanVienID"],
                                                 "ca_lam_viec_id": sang["CaLamViecID"], "ngay_lam": ngay})
    assert r.status_code == 201, r.get_json()
    lich = r.get_json()["data"]
    assert lich["TrangThai"] == "DA_XEP" and lich["GioBatDau"] == "07:00"

    def xep(ca, ngay_lam=ngay):
        return admin.post(f"{API}/workSchedules", json={
            "nhan_vien_id": nv["NhanVienID"], "ca_lam_viec_id": ca["CaLamViecID"], "ngay_lam": ngay_lam})

    assert xep(sang).status_code == 409                 # trung ca cung ngay
    assert xep(chong).status_code == 409                # chong gio 11-12
    assert xep(chieu).status_code == 201                # sat gio 12:00 la duoc
    # Ca dem hom truoc (22:00 -> 08:00) chong voi ca sang 07:00 hom nay
    hom_truoc = (datetime.date.fromisoformat(ngay) - datetime.timedelta(days=1)).isoformat()
    assert xep(dem, hom_truoc).status_code == 409
    assert xep(sang, "2020-01-01").status_code == 400

    r = admin.get(f"{API}/workSchedules?tu_ngay={ngay}&den_ngay={ngay}&nhan_vien_id={nv['NhanVienID']}")
    assert [x["TenCa"] for x in r.get_json()["data"]["items"]] == [sang["TenCa"], chieu["TenCa"]]

    # Chua den ngay -> chua cham cong
    r = admin.put(f"{API}/workSchedules/{lich['LichLamViecID']}", json={"trang_thai": "DA_LAM"})
    assert r.status_code == 409
    # Doi sang ca chong voi lich con lai -> chan
    r = admin.put(f"{API}/workSchedules/{lich['LichLamViecID']}", json={"ca_lam_viec_id": chong["CaLamViecID"]})
    assert r.status_code == 409
    r = admin.put(f"{API}/workSchedules/{lich['LichLamViecID']}", json={"ngay_lam": _ngay(3), "ghi_chu": "Doi ngay"})
    assert r.status_code == 200 and r.get_json()["data"]["GhiChu"] == "Doi ngay"
    r = admin.put(f"{API}/workSchedules/{lich['LichLamViecID']}", json={"trang_thai": "DA_HUY"})
    assert r.status_code == 200
    assert admin.put(f"{API}/workSchedules/{lich['LichLamViecID']}", json={"ghi_chu": "x"}).status_code == 409


def test_cham_cong_hom_nay_va_nghi_viec_huy_lich(admin):
    nv = tao_nv(admin)
    ca = tao_ca(admin, "06:00", "10:00")
    hom_nay = datetime.date.today().isoformat()
    lich = admin.post(f"{API}/workSchedules", json={"nhan_vien_id": nv["NhanVienID"],
                                                    "ca_lam_viec_id": ca["CaLamViecID"], "ngay_lam": hom_nay}).get_json()["data"]
    r = admin.put(f"{API}/workSchedules/{lich['LichLamViecID']}", json={"trang_thai": "DA_LAM"})
    assert r.status_code == 200
    # Da cham cong -> khong doi ca/ngay
    assert admin.put(f"{API}/workSchedules/{lich['LichLamViecID']}", json={"ngay_lam": _ngay(1)}).status_code == 409

    sap_toi = admin.post(f"{API}/workSchedules", json={"nhan_vien_id": nv["NhanVienID"],
                                                       "ca_lam_viec_id": ca["CaLamViecID"], "ngay_lam": _ngay(1)}).get_json()["data"]
    r = admin.patch(f"{API}/employees/{nv['NhanVienID']}/status", json={"trang_thai": "NGHI_VIEC"})
    assert r.status_code == 200 and r.get_json()["data"]["SoLichDaHuy"] == 1
    lich_moi = admin.get(f"{API}/workSchedules?tu_ngay={_ngay(1)}&den_ngay={_ngay(1)}&nhan_vien_id={nv['NhanVienID']}")
    assert lich_moi.get_json()["data"]["items"][0]["LichLamViecID"] == sap_toi["LichLamViecID"]
    assert lich_moi.get_json()["data"]["items"][0]["TrangThai"] == "DA_HUY"
    r = admin.post(f"{API}/workSchedules", json={"nhan_vien_id": nv["NhanVienID"],
                                                 "ca_lam_viec_id": ca["CaLamViecID"], "ngay_lam": _ngay(2)})
    assert r.status_code == 409
    assert admin.patch(f"{API}/employees/{nv['NhanVienID']}/status", json={"trang_thai": "X"}).status_code == 400


def test_nhan_vien_chi_xem_lich_cua_minh(admin, nv):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT TaiKhoanID FROM dbo.TaiKhoan WHERE Email = ?", (dl.NV_EMAIL,))
        tk = cur.fetchval()
    cua_minh = tao_nv(admin, tai_khoan_id=tk)
    nguoi_khac = tao_nv(admin)
    ca = tao_ca(admin, "13:00", "17:00")
    for x in (cua_minh, nguoi_khac):
        r = admin.post(f"{API}/workSchedules", json={"nhan_vien_id": x["NhanVienID"],
                                                     "ca_lam_viec_id": ca["CaLamViecID"], "ngay_lam": _ngay(1)})
        assert r.status_code == 201

    r = nv.get(f"{API}/workSchedules?nhan_vien_id={nguoi_khac['NhanVienID']}")
    assert r.status_code == 200
    assert {x["NhanVienID"] for x in r.get_json()["data"]["items"]} == {cua_minh["NhanVienID"]}
    assert nv.get(f"{API}/shifts").status_code == 200
    assert nv.get(f"{API}/employees").status_code == 403
    assert nv.post(f"{API}/workSchedules", json={}).status_code == 403
    assert nv.post(f"{API}/shifts", json={}).status_code == 403
