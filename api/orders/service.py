"""Logic nghiep vu module orders: DonHang, ChiTietDonHang (Sprint 2).

Nguyen tac:
- Tien luon tinh o backend tu gia trong CSDL (QD02), khong tin so tien client gui.
- Gia ban duoc chot vao ChiTietDonHang luc them mon (QD04).
- Don phai co it nhat 1 mon (QD03).
- Moi thao tac ghi khoa dong DonHang (UPDLOCK) de 2 nguoi sua cung luc khong lech tong tien.
- Loi tra ve dang (thong_bao, ma_http).
"""

import datetime
import uuid
from decimal import Decimal

from database.connection import fetch_all, fetch_one, get_connection

TRANG_THAI_DON = ("MOI", "CHO_PHA_CHE", "DANG_PHA_CHE", "HOAN_THANH", "DA_HUY")
# Chi duoc di toi 1 buoc; huy don dung API rieng.
BUOC_TIEP = {"MOI": "CHO_PHA_CHE", "CHO_PHA_CHE": "DANG_PHA_CHE", "DANG_PHA_CHE": "HOAN_THANH"}
# Don chi sua mon khi chua bat dau pha che.
TRANG_THAI_SUA_DUOC = ("MOI", "CHO_PHA_CHE")

# Trang thai thanh toan coi la "da thu tien" / "dang giu don" (khoa sua mon).
TT_DA_THU = ("THANH_CONG", "HOAN_MOT_PHAN", "DA_HOAN_TIEN")
TT_HIEU_LUC = ("CHO_XAC_NHAN",) + TT_DA_THU

SO_LUONG_TOI_DA = 999


def loi(thong_bao, ma=400):
    return None, (thong_bao, ma)


# ---------- Doc du lieu ----------
DON_SELECT = (
    "SELECT d.*, t.HoTen AS NguoiTao, "
    "COALESCE(tt.TrangThai, 'CHUA_THANH_TOAN') AS TrangThaiThanhToan, "
    "(SELECT COUNT(*) FROM dbo.ChiTietDonHang c WHERE c.DonHangID = d.DonHangID) AS SoDong, "
    "(SELECT COALESCE(SUM(c.SoLuong), 0) FROM dbo.ChiTietDonHang c WHERE c.DonHangID = d.DonHangID) AS SoMon "
    "FROM dbo.DonHang d "
    "LEFT JOIN dbo.TaiKhoan t ON t.TaiKhoanID = d.TaiKhoanID "
    # Moi don co toi da 1 giao dich hieu luc (index UQ_ThanhToan_DonHang_HieuLuc).
    "OUTER APPLY (SELECT TOP 1 p.TrangThai FROM dbo.ThanhToan p "
    "  WHERE p.DonHangID = d.DonHangID AND p.TrangThai <> 'THAT_BAI' "
    "  ORDER BY p.ThanhToanID DESC) tt"
)


def _gan_co_sua(don):
    """Them co DuocSuaMon de giao dien biet an/hien nut sua."""
    if don:
        don["DuocSuaMon"] = (
            don["TrangThai"] in TRANG_THAI_SUA_DUOC
            and don["TrangThaiThanhToan"] == "CHUA_THANH_TOAN"
        )
    return don


def _doc_don(cur, don_hang_id, khoa=False):
    """Doc 1 don. khoa=True: giu khoa dong toi het giao dich."""
    if khoa:
        cur.execute(
            "SELECT DonHangID FROM dbo.DonHang WITH (UPDLOCK, HOLDLOCK) WHERE DonHangID = ?",
            (don_hang_id,),
        )
        if not cur.fetchone():
            return None
    cur.execute(f"{DON_SELECT} WHERE d.DonHangID = ?", (don_hang_id,))
    return _gan_co_sua(fetch_one(cur))


def _doc_chi_tiet(cur, don_hang_id):
    cur.execute(
        "SELECT * FROM dbo.ChiTietDonHang WHERE DonHangID = ? ORDER BY ChiTietDonHangID",
        (don_hang_id,),
    )
    return fetch_all(cur)


def danh_sach_don(trang_thai="", tu_khoa="", ngay="", thanh_toan="", page=1, per_page=20):
    where, params = " WHERE 1=1", []
    if trang_thai:
        where += " AND d.TrangThai = ?"
        params.append(trang_thai)
    if tu_khoa:
        where += " AND d.MaDonHang LIKE ?"
        params.append(f"%{tu_khoa}%")
    if ngay:
        try:
            ngay_dt = datetime.date.fromisoformat(ngay)
        except ValueError:
            return loi("Ngay khong hop le (YYYY-MM-DD)")
        where += " AND d.ThoiGianDat >= ? AND d.ThoiGianDat < ?"
        params += [ngay_dt, ngay_dt + datetime.timedelta(days=1)]
    if thanh_toan == "chua":
        where += " AND tt.TrangThai IS NULL"
    elif thanh_toan == "da":
        where += " AND tt.TrangThai IN ('THANH_CONG', 'HOAN_MOT_PHAN', 'DA_HOAN_TIEN')"
    try:
        page = max(1, int(page or 1))
        per_page = min(100, max(1, int(per_page or 20)))
    except (TypeError, ValueError):
        page, per_page = 1, 20

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM ({DON_SELECT}{where}) x", params)
        total = cur.fetchval()
        cur.execute(
            f"{DON_SELECT}{where} ORDER BY d.DonHangID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            params + [(page - 1) * per_page, per_page],
        )
        items = [_gan_co_sua(r) for r in fetch_all(cur)]
        return {"items": items, "total": total, "page": page, "per_page": per_page}, None


def chi_tiet_don(don_hang_id):
    with get_connection() as conn:
        cur = conn.cursor()
        don = _doc_don(cur, don_hang_id)
        if not don:
            return None
        don["ChiTiet"] = _doc_chi_tiet(cur, don_hang_id)
        return don


def danh_sach_mon_cua_don(don_hang_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.DonHang WHERE DonHangID = ?", (don_hang_id,))
        if not cur.fetchone():
            return loi("Don hang khong ton tai", 404)
        return _doc_chi_tiet(cur, don_hang_id), None


# ---------- Kiem tra dau vao ----------
def _so_luong(gia_tri):
    """So nguyen duong, khong nhan 1.5 hay "2a"."""
    if isinstance(gia_tri, bool):
        return None
    if isinstance(gia_tri, float) and not gia_tri.is_integer():
        return None
    try:
        n = int(str(gia_tri).strip()) if not isinstance(gia_tri, (int, float)) else int(gia_tri)
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= SO_LUONG_TOI_DA else None


def _ghi_chu(gia_tri, toi_da=255):
    text = (gia_tri or "").strip() if isinstance(gia_tri, str) else ""
    return text[:toi_da] or None


def _chuan_hoa_dong(raw):
    """{mon_id, so_luong, ghi_chu[, chi_tiet_id]} -> dict hoac thong bao loi."""
    if not isinstance(raw, dict):
        return None, "Danh sach mon khong hop le"
    try:
        mon_id = int(raw.get("mon_id"))
    except (TypeError, ValueError):
        return None, "Mon khong ton tai"
    so_luong = _so_luong(raw.get("so_luong", 1))
    if so_luong is None:
        return None, f"So luong phai la so nguyen tu 1 den {SO_LUONG_TOI_DA}"
    chi_tiet_id = raw.get("chi_tiet_id")
    try:
        chi_tiet_id = int(chi_tiet_id) if chi_tiet_id not in (None, "") else None
    except (TypeError, ValueError):
        return None, "Mon trong don khong ton tai"
    return {
        "mon_id": mon_id,
        "so_luong": so_luong,
        "ghi_chu": _ghi_chu(raw.get("ghi_chu")),
        "chi_tiet_id": chi_tiet_id,
    }, None


def _mon_dang_ban(cur, mon_id):
    """Lay ten + gia hien tai cua mon dang ban; None neu khong ban duoc."""
    cur.execute(
        "SELECT m.MonID, m.TenMon, m.GiaBan, m.TrangThai, d.TrangThai AS NhomHienThi "
        "FROM dbo.Mon m JOIN dbo.DanhMuc d ON d.DanhMucID = m.DanhMucID WHERE m.MonID = ?",
        (mon_id,),
    )
    return fetch_one(cur)


def _kiem_tra_sua_duoc(don):
    if don["TrangThaiThanhToan"] != "CHUA_THANH_TOAN":
        return "Don da thu tien hoac dang cho xac nhan thanh toan, khong the sua mon"
    if don["TrangThai"] not in TRANG_THAI_SUA_DUOC:
        return "Don da bat dau pha che hoac da dong, khong the sua mon"
    return None


def _them_dong(cur, don_hang_id, dong):
    """Them mon (chot gia hien tai). Mon + ghi chu trung voi dong co san thi cong don."""
    mon = _mon_dang_ban(cur, dong["mon_id"])
    if not mon:
        return "Mon khong ton tai"
    if not mon["TrangThai"] or not mon["NhomHienThi"]:
        return "Mon dang tam ngung ban"
    cur.execute(
        "SELECT ChiTietDonHangID, SoLuong, DonGia FROM dbo.ChiTietDonHang "
        "WHERE DonHangID = ? AND MonID = ? AND ((GhiChu IS NULL AND ? IS NULL) OR GhiChu = ?)",
        (don_hang_id, dong["mon_id"], dong["ghi_chu"], dong["ghi_chu"]),
    )
    co_san = cur.fetchone()
    if co_san:
        so_luong = co_san.SoLuong + dong["so_luong"]
        if so_luong > SO_LUONG_TOI_DA:
            return f"So luong phai la so nguyen tu 1 den {SO_LUONG_TOI_DA}"
        cur.execute(
            "UPDATE dbo.ChiTietDonHang SET SoLuong = ?, ThanhTien = DonGia * ? WHERE ChiTietDonHangID = ?",
            (so_luong, so_luong, co_san.ChiTietDonHangID),
        )
        return None
    don_gia = Decimal(mon["GiaBan"])
    cur.execute(
        "INSERT INTO dbo.ChiTietDonHang (DonHangID, MonID, TenMon, DonGia, SoLuong, ThanhTien, GhiChu) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (don_hang_id, mon["MonID"], mon["TenMon"], don_gia, dong["so_luong"],
         don_gia * dong["so_luong"], dong["ghi_chu"]),
    )
    return None


def _tinh_lai_tien(cur, don_hang_id):
    """TongTien = tong ThanhTien cac dong; GiamGia = 0 (khuyen mai o Sprint sau)."""
    cur.execute(
        "UPDATE d SET TongTien = x.Tong, GiamGia = 0, ThanhTien = x.Tong, NgayCapNhat = SYSDATETIME() "
        "FROM dbo.DonHang d CROSS APPLY (SELECT COALESCE(SUM(c.ThanhTien), 0) AS Tong "
        "  FROM dbo.ChiTietDonHang c WHERE c.DonHangID = d.DonHangID) x "
        "WHERE d.DonHangID = ?",
        (don_hang_id,),
    )


def _ket_qua(cur, don_hang_id):
    don = _doc_don(cur, don_hang_id)
    don["ChiTiet"] = _doc_chi_tiet(cur, don_hang_id)
    return don


# ---------- Ghi du lieu ----------
def tao_don(tai_khoan_id, items, ghi_chu=None):
    if not isinstance(items, list) or not items:
        return loi("Don hang phai co it nhat 1 mon")
    dong_list = []
    for raw in items:
        dong, err = _chuan_hoa_dong(raw)
        if err:
            return loi(err)
        dong["chi_tiet_id"] = None
        dong_list.append(dong)

    with get_connection() as conn:
        cur = conn.cursor()
        # Ma tam de qua rang buoc UNIQUE, doi sang ma that ngay sau khi co ID.
        cur.execute(
            "INSERT INTO dbo.DonHang (TaiKhoanID, MaDonHang, ThoiGianDat, TrangThai, GhiChu) "
            "OUTPUT INSERTED.DonHangID, INSERTED.ThoiGianDat VALUES (?, ?, SYSDATETIME(), 'MOI', ?)",
            (tai_khoan_id, "TMP" + uuid.uuid4().hex[:20], _ghi_chu(ghi_chu, 500)),
        )
        row = cur.fetchone()
        don_hang_id, thoi_gian = row[0], row[1]
        for dong in dong_list:
            err = _them_dong(cur, don_hang_id, dong)
            if err:
                conn.rollback()
                return loi(err, 404 if "khong ton tai" in err else 400)
        cur.execute(
            "UPDATE dbo.DonHang SET MaDonHang = ? WHERE DonHangID = ?",
            (f"DH{thoi_gian:%y%m%d}-{don_hang_id:05d}", don_hang_id),
        )
        _tinh_lai_tien(cur, don_hang_id)
        conn.commit()
        return _ket_qua(cur, don_hang_id), None


def them_mon_vao_don(don_hang_id, raw):
    dong, err = _chuan_hoa_dong(raw)
    if err:
        return loi(err)
    with get_connection() as conn:
        cur = conn.cursor()
        don = _doc_don(cur, don_hang_id, khoa=True)
        if not don:
            conn.rollback()
            return loi("Don hang khong ton tai", 404)
        err = _kiem_tra_sua_duoc(don) or _them_dong(cur, don_hang_id, dong)
        if err:
            conn.rollback()
            return loi(err, 404 if "khong ton tai" in err else 400)
        _tinh_lai_tien(cur, don_hang_id)
        conn.commit()
        return _ket_qua(cur, don_hang_id), None


def cap_nhat_danh_sach_mon(don_hang_id, items):
    """Thay ca danh sach mon.

    Dong co chi_tiet_id: giu gia da chot, chi doi so luong / ghi chu.
    Dong khong co chi_tiet_id: mon moi, chot gia hien tai.
    Dong cu khong con trong danh sach: bi xoa.
    """
    if not isinstance(items, list) or not items:
        return loi("Don hang phai co it nhat 1 mon")
    dong_list = []
    for raw in items:
        dong, err = _chuan_hoa_dong(raw)
        if err:
            return loi(err)
        dong_list.append(dong)

    with get_connection() as conn:
        cur = conn.cursor()
        don = _doc_don(cur, don_hang_id, khoa=True)
        if not don:
            conn.rollback()
            return loi("Don hang khong ton tai", 404)
        err = _kiem_tra_sua_duoc(don)
        if err:
            conn.rollback()
            return loi(err)

        hien_co = {c["ChiTietDonHangID"]: c for c in _doc_chi_tiet(cur, don_hang_id)}
        giu_lai = set()
        moi = []
        for dong in dong_list:
            if dong["chi_tiet_id"] is None:
                moi.append(dong)
                continue
            cu = hien_co.get(dong["chi_tiet_id"])
            if not cu or cu["MonID"] != dong["mon_id"] or dong["chi_tiet_id"] in giu_lai:
                conn.rollback()
                return loi("Mon trong don khong ton tai", 404)
            giu_lai.add(dong["chi_tiet_id"])
            cur.execute(
                "UPDATE dbo.ChiTietDonHang SET SoLuong = ?, ThanhTien = DonGia * ?, GhiChu = ? "
                "WHERE ChiTietDonHangID = ?",
                (dong["so_luong"], dong["so_luong"], dong["ghi_chu"], dong["chi_tiet_id"]),
            )
        for ct_id in set(hien_co) - giu_lai:
            cur.execute("DELETE FROM dbo.ChiTietDonHang WHERE ChiTietDonHangID = ?", (ct_id,))
        for dong in moi:
            err = _them_dong(cur, don_hang_id, dong)
            if err:
                conn.rollback()
                return loi(err, 404 if "khong ton tai" in err else 400)
        _tinh_lai_tien(cur, don_hang_id)
        conn.commit()
        return _ket_qua(cur, don_hang_id), None


def xoa_mon_khoi_don(don_hang_id, chi_tiet_id):
    with get_connection() as conn:
        cur = conn.cursor()
        don = _doc_don(cur, don_hang_id, khoa=True)
        if not don:
            conn.rollback()
            return loi("Don hang khong ton tai", 404)
        err = _kiem_tra_sua_duoc(don)
        if err:
            conn.rollback()
            return loi(err)
        cur.execute(
            "SELECT 1 FROM dbo.ChiTietDonHang WHERE ChiTietDonHangID = ? AND DonHangID = ?",
            (chi_tiet_id, don_hang_id),
        )
        if not cur.fetchone():
            conn.rollback()
            return loi("Mon trong don khong ton tai", 404)
        if don["SoDong"] <= 1:
            conn.rollback()
            return loi("Don hang phai co it nhat 1 mon. Muon bo het mon thi hay huy don")
        cur.execute("DELETE FROM dbo.ChiTietDonHang WHERE ChiTietDonHangID = ?", (chi_tiet_id,))
        _tinh_lai_tien(cur, don_hang_id)
        conn.commit()
        return _ket_qua(cur, don_hang_id), None


def doi_trang_thai_don(don_hang_id, trang_thai):
    trang_thai = (trang_thai or "").strip().upper()
    if trang_thai not in TRANG_THAI_DON:
        return loi("Trang thai don khong hop le")
    if trang_thai == "DA_HUY":
        return loi("Huy don phai kem ly do, hay dung chuc nang huy don")
    with get_connection() as conn:
        cur = conn.cursor()
        don = _doc_don(cur, don_hang_id, khoa=True)
        if not don:
            conn.rollback()
            return loi("Don hang khong ton tai", 404)
        if BUOC_TIEP.get(don["TrangThai"]) != trang_thai:
            conn.rollback()
            return loi("Khong the chuyen don sang trang thai nay", 409)
        cur.execute(
            "UPDATE dbo.DonHang SET TrangThai = ?, NgayCapNhat = SYSDATETIME() WHERE DonHangID = ?",
            (trang_thai, don_hang_id),
        )
        conn.commit()
        return _ket_qua(cur, don_hang_id), None


def huy_don(don_hang_id, ly_do, hoan_tien=False, duoc_hoan_tien=False):
    """Huy don (QD07).

    - Giao dich dang cho xac nhan -> chuyen THAT_BAI.
    - Don da thu tien: hoan_tien=True (va co quyen) thi hoan phan con lai ngay trong
      cung giao dich; neu khong thi tu choi de khong mat dau tien da thu.
    """
    ly_do = _ghi_chu(ly_do, 500)
    if not ly_do:
        return loi("Ly do huy la bat buoc")
    from api.payments import service as tt_service  # tranh import vong

    with get_connection() as conn:
        cur = conn.cursor()
        don = _doc_don(cur, don_hang_id, khoa=True)
        if not don:
            conn.rollback()
            return loi("Don hang khong ton tai", 404)
        if don["TrangThai"] == "DA_HUY":
            conn.rollback()
            return loi("Don hang da huy truoc do", 409)
        if don["TrangThai"] == "HOAN_THANH":
            conn.rollback()
            return loi("Don da hoan thanh, khong the huy. Neu khach tra lai hay dung hoan tien", 409)

        if don["TrangThaiThanhToan"] in ("THANH_CONG", "HOAN_MOT_PHAN"):
            if not hoan_tien:
                conn.rollback()
                return loi("Don da thu tien, can hoan tien cho khach truoc khi huy", 409)
            if not duoc_hoan_tien:
                conn.rollback()
                return loi("Khong co quyen hoan tien", 403)
            err = tt_service.hoan_phan_con_lai(cur, don_hang_id, "Huỷ đơn: " + ly_do)
            if err:
                conn.rollback()
                return loi(*err)

        cur.execute(
            "UPDATE dbo.ThanhToan SET TrangThai = 'THAT_BAI' "
            "WHERE DonHangID = ? AND TrangThai = 'CHO_XAC_NHAN'",
            (don_hang_id,),
        )
        cur.execute(
            "UPDATE dbo.DonHang SET TrangThai = 'DA_HUY', LyDoHuy = ?, NgayCapNhat = SYSDATETIME() "
            "WHERE DonHangID = ?",
            (ly_do, don_hang_id),
        )
        conn.commit()
        return _ket_qua(cur, don_hang_id), None
