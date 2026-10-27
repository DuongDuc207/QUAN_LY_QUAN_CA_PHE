"""Logic nghiep vu module payments: ThanhToan, HoaDon, HoanTien (Sprint 2).

Nguyen tac:
- So tien can thu lay tu DonHang.ThanhTien (backend tinh), client gui thi phai khop.
- Chong thanh toan trung: moi don chi co 1 giao dich chua that bai. Kiem tra trong
  giao dich co khoa dong DonHang + index UQ_ThanhToan_DonHang_HieuLuc o CSDL.
- Chi THANH_CONG khi duoc xac nhan (QD05); luc do moi lap hoa don.
- Tong tien hoan khong vuot so tien da thu.
- Loi tra ve dang (thong_bao, ma_http).
"""

from decimal import Decimal, InvalidOperation

import pyodbc

from api.orders.service import TT_DA_THU, _doc_chi_tiet, _doc_don, loi
from database.connection import fetch_all, fetch_one, get_connection

PHUONG_THUC = ("TIEN_MAT", "CHUYEN_KHOAN", "THE")
# Chuyen khoan / the phai co ma giao dich ngan hang khi xac nhan.
CAN_MA_GIAO_DICH = ("CHUYEN_KHOAN", "THE")


def _tien(gia_tri):
    """Doi sang Decimal 2 chu so; None neu khong hop le."""
    if isinstance(gia_tri, bool) or gia_tri in (None, ""):
        return None
    try:
        so = Decimal(str(gia_tri)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None
    return so if so.is_finite() else None


def _ma(gia_tri):
    text = (gia_tri or "").strip() if isinstance(gia_tri, str) else ""
    return text[:100] or None


# ---------- Doc du lieu ----------
TT_SELECT = (
    "SELECT p.*, d.MaDonHang, "
    "(SELECT COALESCE(SUM(h.SoTienHoan), 0) FROM dbo.HoanTien h "
    "  WHERE h.ThanhToanID = p.ThanhToanID AND h.TrangThai = 'HOAN_THANH') AS SoTienDaHoan "
    "FROM dbo.ThanhToan p JOIN dbo.DonHang d ON d.DonHangID = p.DonHangID"
)


def _doc_thanh_toan(cur, thanh_toan_id):
    cur.execute(f"{TT_SELECT} WHERE p.ThanhToanID = ?", (thanh_toan_id,))
    tt = fetch_one(cur)
    if tt:
        cur.execute(
            "SELECT * FROM dbo.HoanTien WHERE ThanhToanID = ? ORDER BY HoanTienID",
            (thanh_toan_id,),
        )
        tt["HoanTien"] = fetch_all(cur)
    return tt


def chi_tiet_thanh_toan(thanh_toan_id):
    with get_connection() as conn:
        return _doc_thanh_toan(conn.cursor(), thanh_toan_id)


def lich_su_thanh_toan(don_hang_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.DonHang WHERE DonHangID = ?", (don_hang_id,))
        if not cur.fetchone():
            return loi("Don hang khong ton tai", 404)
        cur.execute(f"{TT_SELECT} WHERE p.DonHangID = ? ORDER BY p.ThanhToanID DESC", (don_hang_id,))
        return fetch_all(cur), None


# ---------- Tao / xac nhan ----------
def tao_thanh_toan(don_hang_id, phuong_thuc, so_tien=None, ma_giao_dich=None):
    try:
        don_hang_id = int(don_hang_id)
    except (TypeError, ValueError):
        return loi("Don hang khong ton tai", 404)
    phuong_thuc = (phuong_thuc or "").strip().upper()
    if phuong_thuc not in PHUONG_THUC:
        return loi("Phuong thuc thanh toan khong hop le")

    with get_connection() as conn:
        cur = conn.cursor()
        don = _doc_don(cur, don_hang_id, khoa=True)
        if not don:
            conn.rollback()
            return loi("Don hang khong ton tai", 404)
        if don["TrangThai"] == "DA_HUY":
            conn.rollback()
            return loi("Don hang da huy, khong the thanh toan", 409)
        if don["TrangThaiThanhToan"] == "CHO_XAC_NHAN":
            conn.rollback()
            return loi("Don dang co giao dich cho xac nhan, hay xac nhan hoac bao that bai truoc", 409)
        if don["TrangThaiThanhToan"] != "CHUA_THANH_TOAN":
            conn.rollback()
            return loi("Don hang da duoc thanh toan", 409)

        can_thu = Decimal(don["ThanhTien"])
        if can_thu <= 0:
            conn.rollback()
            return loi("Don hang chua co mon nao de thanh toan")
        if so_tien is not None:
            gui_len = _tien(so_tien)
            if gui_len is None:
                conn.rollback()
                return loi("So tien khong hop le")
            if gui_len != can_thu:
                conn.rollback()
                return loi("So tien thanh toan khong khop voi so tien can thu", 409)

        try:
            cur.execute(
                "INSERT INTO dbo.ThanhToan (DonHangID, MaGiaoDich, PhuongThuc, SoTien, TrangThai, NgayTao) "
                "OUTPUT INSERTED.ThanhToanID VALUES (?, ?, ?, ?, 'CHO_XAC_NHAN', SYSDATETIME())",
                (don_hang_id, _ma(ma_giao_dich), phuong_thuc, can_thu),
            )
            thanh_toan_id = cur.fetchval()
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_trung(e))
        conn.commit()
        return _doc_thanh_toan(cur, thanh_toan_id), None


def _dich_loi_trung(e):
    text = str(e)
    if "UQ_ThanhToan_MaGiaoDich" in text:
        return "Ma giao dich da duoc su dung", 409
    if "UQ_ThanhToan_DonHang_HieuLuc" in text:
        return "Don hang da duoc thanh toan", 409
    return "Du lieu thanh toan khong hop le", 400


def xac_nhan_thanh_toan(thanh_toan_id, thanh_cong=True, ma_giao_dich=None):
    """Xac nhan ket qua giao dich. Thanh cong -> lap hoa don trong cung giao dich."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DonHangID FROM dbo.ThanhToan WHERE ThanhToanID = ?", (thanh_toan_id,))
        row = cur.fetchone()
        if not row:
            return loi("Giao dich thanh toan khong ton tai", 404)
        # Khoa don truoc roi moi doc lai giao dich -> 2 nguoi bam cung luc chi 1 nguoi qua.
        don = _doc_don(cur, row.DonHangID, khoa=True)
        cur.execute(
            "SELECT * FROM dbo.ThanhToan WITH (UPDLOCK) WHERE ThanhToanID = ?", (thanh_toan_id,)
        )
        tt = fetch_one(cur)
        if tt["TrangThai"] != "CHO_XAC_NHAN":
            conn.rollback()
            return loi("Giao dich nay da duoc xu ly truoc do", 409)

        if not thanh_cong:
            cur.execute(
                "UPDATE dbo.ThanhToan SET TrangThai = 'THAT_BAI' WHERE ThanhToanID = ?",
                (thanh_toan_id,),
            )
            conn.commit()
            return {"ThanhToan": _doc_thanh_toan(cur, thanh_toan_id), "HoaDon": None}, None

        if don["TrangThai"] == "DA_HUY":
            conn.rollback()
            return loi("Don hang da huy, khong the thanh toan", 409)
        # Mon bi khoa khi co giao dich cho, nhung van so lai cho chac.
        if Decimal(tt["SoTien"]) != Decimal(don["ThanhTien"]):
            conn.rollback()
            return loi("So tien thanh toan khong khop voi so tien can thu", 409)
        ma = _ma(ma_giao_dich) or tt["MaGiaoDich"]
        if tt["PhuongThuc"] in CAN_MA_GIAO_DICH and not ma:
            conn.rollback()
            return loi("Can nhap ma giao dich cua ngan hang de xac nhan")

        try:
            cur.execute(
                "UPDATE dbo.ThanhToan SET TrangThai = 'THANH_CONG', MaGiaoDich = ?, "
                "ThoiGianThanhToan = SYSDATETIME() WHERE ThanhToanID = ?",
                (ma, thanh_toan_id),
            )
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_trung(e))
        hoa_don_id = _lap_hoa_don(cur, don)
        conn.commit()
        return {
            "ThanhToan": _doc_thanh_toan(cur, thanh_toan_id),
            "HoaDon": _doc_hoa_don(cur, hoa_don_id),
        }, None


def _lap_hoa_don(cur, don):
    cur.execute(
        "INSERT INTO dbo.HoaDon (DonHangID, MaHoaDon, NgayLap, TongTien, GiamGia, ThanhTien, TrangThai) "
        "OUTPUT INSERTED.HoaDonID, INSERTED.NgayLap VALUES (?, ?, SYSDATETIME(), ?, ?, ?, 'DA_THANH_TOAN')",
        (don["DonHangID"], "TMP" + str(don["DonHangID"]), don["TongTien"], don["GiamGia"], don["ThanhTien"]),
    )
    hoa_don_id, ngay_lap = cur.fetchone()
    cur.execute(
        "UPDATE dbo.HoaDon SET MaHoaDon = ? WHERE HoaDonID = ?",
        (f"HD{ngay_lap:%y%m%d}-{hoa_don_id:05d}", hoa_don_id),
    )
    return hoa_don_id


# ---------- Hoan tien ----------
def _ghi_hoan_tien(cur, tt, so_tien, ly_do, ma_hoan=None):
    """Ghi 1 lan hoan + cap nhat trang thai giao dich va hoa don. Tra ve loi hoac None."""
    if tt["TrangThai"] not in ("THANH_CONG", "HOAN_MOT_PHAN"):
        return "Chi hoan tien cho giao dich da thanh toan thanh cong", 409
    da_thu = Decimal(tt["SoTien"])
    da_hoan = Decimal(tt["SoTienDaHoan"])
    con_lai = da_thu - da_hoan
    if so_tien <= 0:
        return "So tien hoan phai lon hon 0", 400
    if so_tien > con_lai:
        return f"So tien hoan vuot qua so tien con lai co the hoan ({con_lai:,.0f})", 409
    cur.execute(
        "INSERT INTO dbo.HoanTien (ThanhToanID, SoTienHoan, LyDo, TrangThai, MaGiaoDichHoan, NgayYeuCau, NgayHoanTien) "
        "VALUES (?, ?, ?, 'HOAN_THANH', ?, SYSDATETIME(), SYSDATETIME())",
        (tt["ThanhToanID"], so_tien, ly_do, ma_hoan),
    )
    moi = "DA_HOAN_TIEN" if da_hoan + so_tien == da_thu else "HOAN_MOT_PHAN"
    cur.execute("UPDATE dbo.ThanhToan SET TrangThai = ? WHERE ThanhToanID = ?", (moi, tt["ThanhToanID"]))
    cur.execute("UPDATE dbo.HoaDon SET TrangThai = ? WHERE DonHangID = ?", (moi, tt["DonHangID"]))
    return None


def _khoa_giao_dich_da_thu(cur, don_hang_id):
    cur.execute(
        f"{TT_SELECT} WHERE p.DonHangID = ? AND p.TrangThai IN ({','.join('?' * len(TT_DA_THU))})",
        (don_hang_id, *TT_DA_THU),
    )
    return fetch_one(cur)


def hoan_tien(thanh_toan_id, so_tien, ly_do, ma_giao_dich_hoan=None):
    ly_do = (ly_do or "").strip()[:500] if isinstance(ly_do, str) else ""
    if not ly_do:
        return loi("Ly do hoan tien la bat buoc")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DonHangID FROM dbo.ThanhToan WHERE ThanhToanID = ?", (thanh_toan_id,))
        row = cur.fetchone()
        if not row:
            return loi("Giao dich thanh toan khong ton tai", 404)
        _doc_don(cur, row.DonHangID, khoa=True)
        cur.execute(f"{TT_SELECT} WHERE p.ThanhToanID = ?", (thanh_toan_id,))
        tt = fetch_one(cur)
        # Bo trong so tien = hoan toan bo phan con lai.
        tien = _tien(so_tien) if so_tien not in (None, "") else Decimal(tt["SoTien"]) - Decimal(tt["SoTienDaHoan"])
        if tien is None:
            conn.rollback()
            return loi("So tien hoan khong hop le")
        err = _ghi_hoan_tien(cur, tt, tien, ly_do, _ma(ma_giao_dich_hoan))
        if err:
            conn.rollback()
            return loi(*err)
        conn.commit()
        return _doc_thanh_toan(cur, thanh_toan_id), None


def hoan_phan_con_lai(cur, don_hang_id, ly_do):
    """Dung khi huy don da thu tien (goi trong giao dich cua huy_don, da khoa don)."""
    tt = _khoa_giao_dich_da_thu(cur, don_hang_id)
    if not tt:
        return None
    con_lai = Decimal(tt["SoTien"]) - Decimal(tt["SoTienDaHoan"])
    if con_lai <= 0:
        return None
    return _ghi_hoan_tien(cur, tt, con_lai, ly_do[:500])


# ---------- Hoa don ----------
def _doc_hoa_don(cur, hoa_don_id):
    cur.execute(
        "SELECT h.*, d.MaDonHang, d.ThoiGianDat, d.GhiChu, d.TrangThai AS TrangThaiDon, "
        "t.HoTen AS NguoiTao "
        "FROM dbo.HoaDon h JOIN dbo.DonHang d ON d.DonHangID = h.DonHangID "
        "LEFT JOIN dbo.TaiKhoan t ON t.TaiKhoanID = d.TaiKhoanID WHERE h.HoaDonID = ?",
        (hoa_don_id,),
    )
    hd = fetch_one(cur)
    if not hd:
        return None
    hd["ChiTiet"] = _doc_chi_tiet(cur, hd["DonHangID"])
    tt = _khoa_giao_dich_da_thu(cur, hd["DonHangID"])
    hd["ThanhToan"] = tt
    hd["SoTienDaHoan"] = tt["SoTienDaHoan"] if tt else 0
    return hd


def chi_tiet_hoa_don(hoa_don_id):
    with get_connection() as conn:
        return _doc_hoa_don(conn.cursor(), hoa_don_id)


def hoa_don_cua_don(don_hang_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.DonHang WHERE DonHangID = ?", (don_hang_id,))
        if not cur.fetchone():
            return loi("Don hang khong ton tai", 404)
        cur.execute("SELECT HoaDonID FROM dbo.HoaDon WHERE DonHangID = ?", (don_hang_id,))
        row = cur.fetchone()
        if not row:
            return loi("Don hang chua co hoa don (chua thanh toan)", 404)
        return _doc_hoa_don(cur, row.HoaDonID), None
