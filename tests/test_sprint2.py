"""Kiem thu Sprint 2: orders (9 API) + payments (8 API) - quy trinh ban hang.

Chay: py -3.12 -m pytest tests/ -v
"""

import pytest

from app import create_app
from database.connection import get_connection
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


def staff_client():
    c = create_app().test_client()
    login(c, dl.NV_EMAIL, dl.NV_MK)
    return c


def tao_don(client, items=None, ghi_chu=None):
    items = items or [{"mon_id": dl.MON_ID, "so_luong": 2}, {"mon_id": dl.MON2_ID, "so_luong": 1}]
    r = client.post("/api/v1/orders", json={"items": items, "ghi_chu": ghi_chu})
    assert r.status_code == 201, r.get_json()
    return r.get_json()["data"]


def thu_tien(client, don, phuong_thuc="TIEN_MAT", ma=None):
    r = client.post("/api/v1/payments", json={
        "don_hang_id": don["DonHangID"], "phuong_thuc": phuong_thuc, "so_tien": float(don["ThanhTien"])})
    assert r.status_code == 201, r.get_json()
    tt = r.get_json()["data"]
    r = client.post(f"/api/v1/payments/{tt['ThanhToanID']}/confirm", json={"ma_giao_dich": ma})
    assert r.status_code == 200, r.get_json()
    return r.get_json()["data"]


def doi_gia(mon_id, gia):
    with get_connection() as conn:
        conn.cursor().execute("UPDATE dbo.Mon SET GiaBan = ? WHERE MonID = ?", (gia, mon_id))
        conn.commit()


# ---------- 1-3. Tao don, them mon, tinh tien o backend ----------
def test_tao_don_tinh_tien_o_backend(client):
    login(client)
    # Client gui gia/thanh tien gia -> backend bo qua, tinh tu CSDL.
    don = tao_don(client, [
        {"mon_id": dl.MON_ID, "so_luong": 2, "don_gia": 1, "thanh_tien": 1},
        {"mon_id": dl.MON2_ID, "so_luong": 1, "ghi_chu": "  it da  "},
    ], ghi_chu="Ban 5")
    assert float(don["TongTien"]) == 2 * 10000 + 25000
    assert float(don["ThanhTien"]) == 45000
    assert don["TrangThai"] == "MOI"
    assert don["TrangThaiThanhToan"] == "CHUA_THANH_TOAN"
    assert don["MaDonHang"].startswith("DH") and "TMP" not in don["MaDonHang"]
    assert don["DuocSuaMon"] is True
    assert [c["GhiChu"] for c in don["ChiTiet"]] == [None, "it da"]

    r = client.get(f"/api/v1/orders/{don['DonHangID']}/items")
    assert len(r.get_json()["data"]) == 2
    r = client.get(f"/api/v1/orders?q={don['MaDonHang']}")
    assert r.get_json()["data"]["total"] == 1


@pytest.mark.parametrize("items, ma", [
    ([], 400),                                            # QD03: it nhat 1 mon
    ([{"mon_id": dl.MON_ID if dl.MON_ID else 0, "so_luong": 0}], 400),
    ([{"mon_id": 1, "so_luong": 1.5}], 400),             # so luong phai la so nguyen
    ([{"mon_id": 1, "so_luong": "abc"}], 400),
    ([{"mon_id": 999999, "so_luong": 1}], 404),
])
def test_tao_don_du_lieu_sai(client, items, ma):
    login(client)
    r = client.post("/api/v1/orders", json={"items": items})
    assert r.status_code == ma, r.get_json()


def test_khong_ban_mon_ngung_ban(client):
    login(client)
    r = client.post("/api/v1/orders", json={"items": [{"mon_id": dl.MON_NGUNG_ID, "so_luong": 1}]})
    assert r.status_code == 400
    assert "tam ngung" in r.get_json()["message"]


# ---------- QD04: chot gia luc dat ----------
def test_gia_duoc_chot_khi_dat(client):
    login(client)
    don = tao_don(client, [{"mon_id": dl.MON_ID, "so_luong": 1}])
    try:
        doi_gia(dl.MON_ID, 99000)
        # Dong cu giu gia cu khi doi so luong
        ct = don["ChiTiet"][0]
        r = client.put(f"/api/v1/orders/{don['DonHangID']}/items", json={"items": [
            {"chi_tiet_id": ct["ChiTietDonHangID"], "mon_id": dl.MON_ID, "so_luong": 3}]})
        assert r.status_code == 200, r.get_json()
        assert float(r.get_json()["data"]["ThanhTien"]) == 30000
        # Mon them moi lay gia hien tai -> tach dong rieng? Khong: cung mon + ghi chu thi cong don
        # nen dung ghi chu khac de thay gia moi.
        r = client.post(f"/api/v1/orders/{don['DonHangID']}/items",
                        json={"mon_id": dl.MON_ID, "so_luong": 1, "ghi_chu": "size L"})
        d = r.get_json()["data"]
        assert [float(c["DonGia"]) for c in d["ChiTiet"]] == [10000, 99000]
        assert float(d["ThanhTien"]) == 30000 + 99000
    finally:
        doi_gia(dl.MON_ID, 10000)


# ---------- 2. Cap nhat so luong / them / xoa mon ----------
def test_them_mon_trung_thi_cong_don_va_xoa_mon(client):
    login(client)
    don = tao_don(client, [{"mon_id": dl.MON_ID, "so_luong": 1}])
    did = don["DonHangID"]
    r = client.post(f"/api/v1/orders/{did}/items", json={"mon_id": dl.MON_ID, "so_luong": 2})
    assert r.status_code == 201
    d = r.get_json()["data"]
    assert len(d["ChiTiet"]) == 1 and d["ChiTiet"][0]["SoLuong"] == 3

    r = client.post(f"/api/v1/orders/{did}/items", json={"mon_id": dl.MON2_ID, "so_luong": 1})
    d = r.get_json()["data"]
    assert float(d["ThanhTien"]) == 3 * 10000 + 25000

    # Xoa mon -> tinh lai tien
    ct2 = next(c for c in d["ChiTiet"] if c["MonID"] == dl.MON2_ID)
    r = client.delete(f"/api/v1/orders/{did}/items/{ct2['ChiTietDonHangID']}")
    assert r.status_code == 200
    assert float(r.get_json()["data"]["ThanhTien"]) == 30000

    # Khong xoa duoc mon cuoi cung (QD03)
    ct1 = r.get_json()["data"]["ChiTiet"][0]
    r = client.delete(f"/api/v1/orders/{did}/items/{ct1['ChiTietDonHangID']}")
    assert r.status_code == 400
    # Chi tiet cua don khac -> 404
    don2 = tao_don(client)
    r = client.delete(f"/api/v1/orders/{did}/items/{don2['ChiTiet'][0]['ChiTietDonHangID']}")
    assert r.status_code == 404


def test_put_items_thay_ca_danh_sach(client):
    login(client)
    don = tao_don(client)
    did = don["DonHangID"]
    giu = don["ChiTiet"][0]
    r = client.put(f"/api/v1/orders/{did}/items", json={"items": [
        {"chi_tiet_id": giu["ChiTietDonHangID"], "mon_id": giu["MonID"], "so_luong": 5}]})
    d = r.get_json()["data"]
    assert len(d["ChiTiet"]) == 1 and float(d["ThanhTien"]) == 50000
    # Danh sach rong bi chan
    assert client.put(f"/api/v1/orders/{did}/items", json={"items": []}).status_code == 400
    # chi_tiet_id khong khop mon -> 404
    r = client.put(f"/api/v1/orders/{did}/items", json={"items": [
        {"chi_tiet_id": giu["ChiTietDonHangID"], "mon_id": dl.MON2_ID, "so_luong": 1}]})
    assert r.status_code == 404


# ---------- 4. Trang thai don ----------
def test_trang_thai_chi_di_tung_buoc(client):
    login(client)
    don = tao_don(client)
    did = don["DonHangID"]
    # Nhay coc bi chan
    r = client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": "HOAN_THANH"})
    assert r.status_code == 409
    # DA_HUY phai qua API huy
    r = client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": "DA_HUY"})
    assert r.status_code == 400
    assert client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": "XYZ"}).status_code == 400

    for tt in ("CHO_PHA_CHE", "DANG_PHA_CHE"):
        r = client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": tt})
        assert r.status_code == 200 and r.get_json()["data"]["TrangThai"] == tt
    # Dang pha che -> khong sua mon
    assert r.get_json()["data"]["DuocSuaMon"] is False
    r = client.post(f"/api/v1/orders/{did}/items", json={"mon_id": dl.MON_ID, "so_luong": 1})
    assert r.status_code == 400
    r = client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": "HOAN_THANH"})
    assert r.get_json()["data"]["TrangThai"] == "HOAN_THANH"
    # Khong lui lai
    r = client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": "MOI"})
    assert r.status_code == 409
    # Don hoan thanh khong huy
    assert client.post(f"/api/v1/orders/{did}/cancel", json={"ly_do": "x"}).status_code == 409


# ---------- 5. Huy don ----------
def test_huy_don_bat_buoc_ly_do(client):
    login(client)
    don = tao_don(client)
    did = don["DonHangID"]
    assert client.post(f"/api/v1/orders/{did}/cancel", json={"ly_do": "   "}).status_code == 400
    r = client.post(f"/api/v1/orders/{did}/cancel", json={"ly_do": "Khach doi y"})
    assert r.status_code == 200
    d = r.get_json()["data"]
    assert d["TrangThai"] == "DA_HUY" and d["LyDoHuy"] == "Khach doi y"
    assert client.post(f"/api/v1/orders/{did}/cancel", json={"ly_do": "lai"}).status_code == 409
    # Don huy khong thanh toan, khong sua mon
    r = client.post("/api/v1/payments", json={"don_hang_id": did, "phuong_thuc": "TIEN_MAT"})
    assert r.status_code == 409
    r = client.post(f"/api/v1/orders/{did}/items", json={"mon_id": dl.MON_ID, "so_luong": 1})
    assert r.status_code == 400


def test_huy_don_dang_cho_thanh_toan_thi_giao_dich_that_bai(client):
    login(client)
    don = tao_don(client)
    r = client.post("/api/v1/payments", json={"don_hang_id": don["DonHangID"], "phuong_thuc": "CHUYEN_KHOAN"})
    tid = r.get_json()["data"]["ThanhToanID"]
    r = client.post(f"/api/v1/orders/{don['DonHangID']}/cancel", json={"ly_do": "Khach bo di"})
    assert r.status_code == 200
    assert client.get(f"/api/v1/payments/{tid}").get_json()["data"]["TrangThai"] == "THAT_BAI"


def test_huy_don_da_thu_tien_phai_hoan(client):
    login(client)
    don = tao_don(client)
    did = don["DonHangID"]
    kq = thu_tien(client, don)
    tid = kq["ThanhToan"]["ThanhToanID"]
    # Khong chon hoan tien -> tu choi
    r = client.post(f"/api/v1/orders/{did}/cancel", json={"ly_do": "Het nguyen lieu"})
    assert r.status_code == 409
    # Nhan vien khong co quyen hoan tien -> 403
    r = staff_client().post(f"/api/v1/orders/{did}/cancel", json={"ly_do": "x", "hoan_tien": True})
    assert r.status_code == 403
    # Quan tri: huy + hoan toan bo trong 1 giao dich
    r = client.post(f"/api/v1/orders/{did}/cancel", json={"ly_do": "Het nguyen lieu", "hoan_tien": True})
    assert r.status_code == 200, r.get_json()
    tt = client.get(f"/api/v1/payments/{tid}").get_json()["data"]
    assert tt["TrangThai"] == "DA_HOAN_TIEN"
    assert float(tt["SoTienDaHoan"]) == float(don["ThanhTien"])
    assert tt["HoanTien"][0]["LyDo"].endswith("Het nguyen lieu")
    hd = client.get(f"/api/v1/orders/{did}/invoice").get_json()["data"]
    assert hd["TrangThai"] == "DA_HOAN_TIEN"


# ---------- 6-7. Thanh toan, hoa don ----------
def test_thanh_toan_tien_mat_lap_hoa_don(client):
    login(client)
    don = tao_don(client)
    did = don["DonHangID"]
    # Chua thanh toan -> chua co hoa don
    assert client.get(f"/api/v1/orders/{did}/invoice").status_code == 404
    # So tien khong khop bi chan
    r = client.post("/api/v1/payments", json={"don_hang_id": did, "phuong_thuc": "TIEN_MAT", "so_tien": 1000})
    assert r.status_code == 409
    assert client.post("/api/v1/payments", json={"don_hang_id": did, "phuong_thuc": "BITCOIN"}).status_code == 400

    kq = thu_tien(client, don)
    tt, hd = kq["ThanhToan"], kq["HoaDon"]
    assert tt["TrangThai"] == "THANH_CONG" and tt["ThoiGianThanhToan"]
    assert float(tt["SoTien"]) == 45000
    assert hd["MaHoaDon"].startswith("HD") and float(hd["ThanhTien"]) == 45000
    assert len(hd["ChiTiet"]) == 2

    assert client.get(f"/api/v1/invoices/{hd['HoaDonID']}").get_json()["data"]["DonHangID"] == did
    assert client.get(f"/api/v1/orders/{did}/invoice").get_json()["data"]["HoaDonID"] == hd["HoaDonID"]
    lich_su = client.get(f"/api/v1/orders/{did}/payments").get_json()["data"]
    assert [p["TrangThai"] for p in lich_su] == ["THANH_CONG"]

    # Da thanh toan -> khong sua mon, don hien da thu
    d = client.get(f"/api/v1/orders/{did}").get_json()["data"]
    assert d["TrangThaiThanhToan"] == "THANH_CONG" and d["DuocSuaMon"] is False
    assert client.post(f"/api/v1/orders/{did}/items", json={"mon_id": dl.MON_ID}).status_code == 400

    # Trang in: HTML, co so tien dinh dang, khong lo ma he thong
    r = client.get(f"/api/v1/invoices/{hd['HoaDonID']}/print")
    assert r.status_code == 200 and r.mimetype == "text/html"
    html = r.get_data(as_text=True)
    assert hd["MaHoaDon"] in html and "45.000 ₫" in html and "Tiền mặt" in html
    for ma in ("TIEN_MAT", "THANH_CONG", "DA_THANH_TOAN", "None"):
        assert ma not in html


def test_chuyen_khoan_can_ma_giao_dich_va_that_bai_thi_tra_lai(client):
    login(client)
    don = tao_don(client)
    did = don["DonHangID"]
    r = client.post("/api/v1/payments", json={"don_hang_id": did, "phuong_thuc": "CHUYEN_KHOAN"})
    t1 = r.get_json()["data"]["ThanhToanID"]
    # Dang cho -> khong tao giao dich thu 2
    r = client.post("/api/v1/payments", json={"don_hang_id": did, "phuong_thuc": "TIEN_MAT"})
    assert r.status_code == 409
    # Thieu ma giao dich
    assert client.post(f"/api/v1/payments/{t1}/confirm", json={}).status_code == 400
    # Bao that bai -> khong co hoa don, duoc thanh toan lai
    r = client.post(f"/api/v1/payments/{t1}/confirm", json={"thanh_cong": False})
    assert r.get_json()["data"]["ThanhToan"]["TrangThai"] == "THAT_BAI"
    assert r.get_json()["data"]["HoaDon"] is None
    assert client.post(f"/api/v1/payments/{t1}/confirm", json={}).status_code == 409

    ma = f"PYTEST-{did}"
    kq = thu_tien(client, client.get(f"/api/v1/orders/{did}").get_json()["data"], "CHUYEN_KHOAN", ma)
    assert kq["ThanhToan"]["MaGiaoDich"] == ma
    lich_su = client.get(f"/api/v1/orders/{did}/payments").get_json()["data"]
    assert sorted(p["TrangThai"] for p in lich_su) == ["THANH_CONG", "THAT_BAI"]

    # Ma giao dich trung voi don khac bi chan
    don2 = tao_don(client)
    r = client.post("/api/v1/payments", json={"don_hang_id": don2["DonHangID"], "phuong_thuc": "THE"})
    t2 = r.get_json()["data"]["ThanhToanID"]
    r = client.post(f"/api/v1/payments/{t2}/confirm", json={"ma_giao_dich": ma})
    assert r.status_code == 409


# ---------- 8. Chong thanh toan trung + hoan tien ----------
def test_chong_thanh_toan_trung(client):
    login(client)
    don = tao_don(client)
    did = don["DonHangID"]
    r = client.post("/api/v1/payments", json={"don_hang_id": did, "phuong_thuc": "TIEN_MAT"})
    tid = r.get_json()["data"]["ThanhToanID"]
    assert client.post(f"/api/v1/payments/{tid}/confirm", json={}).status_code == 200
    # Xac nhan lai lan 2 (bam 2 lan) -> 409, khong tao hoa don thu 2
    assert client.post(f"/api/v1/payments/{tid}/confirm", json={}).status_code == 409
    # Tao giao dich moi cho don da thu -> 409
    r = client.post("/api/v1/payments", json={"don_hang_id": did, "phuong_thuc": "TIEN_MAT"})
    assert r.status_code == 409
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM dbo.HoaDon WHERE DonHangID = ?", (did,))
        assert cur.fetchval() == 1
        cur.execute("SELECT COUNT(*) FROM dbo.ThanhToan WHERE DonHangID = ? AND TrangThai = 'THANH_CONG'", (did,))
        assert cur.fetchval() == 1


def test_csdl_chan_thanh_toan_trung_khi_bo_qua_backend():
    """Index loc o CSDL la lop bao ve cuoi: ghi thang 2 giao dich hieu luc cho 1 don bi loi."""
    import pyodbc

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dbo.DonHang (TaiKhoanID, MaDonHang, TongTien, GiamGia, ThanhTien) "
            "OUTPUT INSERTED.DonHangID SELECT TaiKhoanID, 'PYTEST-UQ', 1, 0, 1 FROM dbo.TaiKhoan WHERE Email = ?",
            (dl.ADMIN_EMAIL,),
        )
        did = cur.fetchval()
        try:
            cur.execute("INSERT INTO dbo.ThanhToan (DonHangID, PhuongThuc, SoTien, TrangThai) VALUES (?, 'TIEN_MAT', 1, 'THANH_CONG')", (did,))
            with pytest.raises(pyodbc.IntegrityError):
                cur.execute("INSERT INTO dbo.ThanhToan (DonHangID, PhuongThuc, SoTien, TrangThai) VALUES (?, 'TIEN_MAT', 1, 'CHO_XAC_NHAN')", (did,))
        finally:
            conn.rollback()


def test_hoan_tien_mot_phan_roi_toan_bo(client):
    login(client)
    don = tao_don(client)
    kq = thu_tien(client, don)
    tid = kq["ThanhToan"]["ThanhToanID"]
    url = f"/api/v1/payments/{tid}/refund"
    assert client.post(url, json={"so_tien": 10000}).status_code == 400          # thieu ly do
    assert client.post(url, json={"so_tien": 0, "ly_do": "x"}).status_code == 400
    assert client.post(url, json={"so_tien": 999999, "ly_do": "x"}).status_code == 409
    # Nhan vien khong co quyen hoan tien
    assert staff_client().post(url, json={"so_tien": 1000, "ly_do": "x"}).status_code == 403

    r = client.post(url, json={"so_tien": 10000, "ly_do": "Pha sai 1 ly"})
    tt = r.get_json()["data"]
    assert tt["TrangThai"] == "HOAN_MOT_PHAN" and float(tt["SoTienDaHoan"]) == 10000
    hd = client.get(f"/api/v1/invoices/{kq['HoaDon']['HoaDonID']}").get_json()["data"]
    assert hd["TrangThai"] == "HOAN_MOT_PHAN"
    # Hoan vuot phan con lai
    assert client.post(url, json={"so_tien": 35001, "ly_do": "x"}).status_code == 409
    # Bo trong so tien = hoan het phan con lai
    r = client.post(url, json={"ly_do": "Khach tra lai"})
    tt = r.get_json()["data"]
    assert tt["TrangThai"] == "DA_HOAN_TIEN" and float(tt["SoTienDaHoan"]) == 45000
    assert len(tt["HoanTien"]) == 2
    assert client.post(url, json={"so_tien": 1, "ly_do": "x"}).status_code == 409


def test_khong_hoan_giao_dich_chua_thanh_cong(client):
    login(client)
    don = tao_don(client)
    r = client.post("/api/v1/payments", json={"don_hang_id": don["DonHangID"], "phuong_thuc": "TIEN_MAT"})
    tid = r.get_json()["data"]["ThanhToanID"]
    r = client.post(f"/api/v1/payments/{tid}/refund", json={"so_tien": 1000, "ly_do": "x"})
    assert r.status_code == 409


# ---------- Phan quyen ----------
def test_phan_quyen_ban_hang():
    anon = create_app().test_client()
    assert anon.get("/api/v1/orders").status_code == 401
    assert anon.post("/api/v1/payments", json={}).status_code == 401
    r = anon.get("/api/v1/invoices/1/print")
    assert r.status_code == 401 and r.mimetype == "text/html"

    # Nhan vien: ban hang + thu tien duoc
    nv = staff_client()
    don = tao_don(nv)
    kq = thu_tien(nv, don)
    assert nv.get(f"/api/v1/invoices/{kq['HoaDon']['HoaDonID']}/print").status_code == 200


def test_loc_danh_sach_don(client):
    login(client)
    don = tao_don(client)
    r = client.get("/api/v1/orders?status=MOI&paid=chua&per_page=100")
    ids = [d["DonHangID"] for d in r.get_json()["data"]["items"]]
    assert don["DonHangID"] in ids
    r = client.get("/api/v1/orders?paid=da&per_page=100")
    assert don["DonHangID"] not in [d["DonHangID"] for d in r.get_json()["data"]["items"]]
    assert client.get("/api/v1/orders?date=khong-phai-ngay").status_code == 400
    assert client.get("/api/v1/orders/999999").status_code == 404
    assert client.get("/api/v1/orders/999999/items").status_code == 404
    assert client.get("/api/v1/orders/999999/payments").status_code == 404
    assert client.get("/api/v1/payments/999999").status_code == 404
    assert client.get("/api/v1/invoices/999999").status_code == 404


def test_ngay_gio_tra_dang_iso(client):
    """Tranh trinh duyet hieu nham mui gio (Flask mac dinh tra 'GMT')."""
    login(client)
    don = tao_don(client)
    assert "GMT" not in don["ThoiGianDat"] and "T" in don["ThoiGianDat"]


# ---------- 9. Quy trinh ban hang tron ven ----------
def test_quy_trinh_ban_hang_tron_ven(client):
    login(client)
    # Vi du tai lieu: 2 x A + 1 x B
    don = tao_don(client)
    did = don["DonHangID"]
    client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": "CHO_PHA_CHE"})
    # Cho pha che van con sua duoc mon
    r = client.post(f"/api/v1/orders/{did}/items", json={"mon_id": dl.MON2_ID, "so_luong": 1})
    assert float(r.get_json()["data"]["ThanhTien"]) == 70000
    kq = thu_tien(client, r.get_json()["data"])
    assert float(kq["HoaDon"]["ThanhTien"]) == 70000
    for tt in ("DANG_PHA_CHE", "HOAN_THANH"):
        assert client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": tt}).status_code == 200
    d = client.get(f"/api/v1/orders/{did}").get_json()["data"]
    assert d["TrangThai"] == "HOAN_THANH" and d["TrangThaiThanhToan"] == "THANH_CONG"
