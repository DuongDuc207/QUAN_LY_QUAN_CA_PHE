"""Logic nghiep vu module menu: DanhMuc, Mon (Sprint 1, Nguoi 2)."""

from database.connection import fetch_all, fetch_one, get_connection


# ---------- Danh muc ----------
def danh_sach_danh_muc(chi_hien_thi=True):
    with get_connection() as conn:
        cur = conn.cursor()
        sql = (
            "SELECT d.*, (SELECT COUNT(*) FROM dbo.Mon m WHERE m.DanhMucID = d.DanhMucID) AS SoMon "
            "FROM dbo.DanhMuc d"
        )
        if chi_hien_thi:
            sql += " WHERE d.TrangThai = 1"
        sql += " ORDER BY d.DanhMucID"
        cur.execute(sql)
        return fetch_all(cur)


def them_danh_muc(ten, mo_ta=None):
    ten = (ten or "").strip()
    if not ten:
        return None, "Ten danh muc la bat buoc"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dbo.DanhMuc (TenDanhMuc, MoTa, TrangThai, NgayTao) "
            "OUTPUT INSERTED.DanhMucID VALUES (?, ?, 1, SYSDATETIME())",
            (ten, (mo_ta or "").strip() or None),
        )
        new_id = cur.fetchval()
        conn.commit()
        return chi_tiet_danh_muc(new_id), None


def chi_tiet_danh_muc(danh_muc_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM dbo.DanhMuc WHERE DanhMucID = ?", (danh_muc_id,))
        return fetch_one(cur)


def sua_danh_muc(danh_muc_id, ten=None, mo_ta=None, trang_thai=None):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.DanhMuc WHERE DanhMucID = ?", (danh_muc_id,))
        if not cur.fetchone():
            return None, "Danh muc khong ton tai"
        sets, params = [], []
        if ten is not None:
            if not ten.strip():
                return None, "Ten danh muc khong duoc de trong"
            sets.append("TenDanhMuc = ?")
            params.append(ten.strip())
        if mo_ta is not None:
            sets.append("MoTa = ?")
            params.append(mo_ta.strip() or None)
        if trang_thai is not None:
            sets.append("TrangThai = ?")
            params.append(1 if trang_thai else 0)
        if not sets:
            return None, "Khong co gi de cap nhat"
        params.append(danh_muc_id)
        cur.execute(f"UPDATE dbo.DanhMuc SET {', '.join(sets)} WHERE DanhMucID = ?", params)
        conn.commit()
        return chi_tiet_danh_muc(danh_muc_id), None


def xoa_danh_muc(danh_muc_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM dbo.DanhMuc WHERE DanhMucID = ?", (danh_muc_id,))
        row = fetch_one(cur)
        if not row:
            return None, "Danh muc khong ton tai"
        cur.execute("SELECT COUNT(*) FROM dbo.Mon WHERE DanhMucID = ?", (danh_muc_id,))
        if cur.fetchone()[0] > 0:
            return None, "Danh muc dang co mon, khong the xoa (hay tat hien thi thay vi xoa)"
        cur.execute("DELETE FROM dbo.DanhMuc WHERE DanhMucID = ?", (danh_muc_id,))
        conn.commit()
        return row, None


# ---------- Mon ----------
MON_SELECT = (
    "SELECT m.*, d.TenDanhMuc FROM dbo.Mon m "
    "JOIN dbo.DanhMuc d ON d.DanhMucID = m.DanhMucID"
)


def danh_sach_mon(danh_muc_id=None, chi_dang_ban=False, tu_khoa="", page=1, per_page=20):
    with get_connection() as conn:
        cur = conn.cursor()
        where, params = " WHERE 1=1", []
        if danh_muc_id:
            where += " AND m.DanhMucID = ?"
            params.append(danh_muc_id)
        if chi_dang_ban:
            where += " AND m.TrangThai = 1 AND d.TrangThai = 1"
        if tu_khoa:
            where += " AND (m.TenMon LIKE ? OR m.MoTa LIKE ?)"
            params += [f"%{tu_khoa}%", f"%{tu_khoa}%"]
        cur.execute(f"SELECT COUNT(*) FROM dbo.Mon m JOIN dbo.DanhMuc d ON d.DanhMucID = m.DanhMucID{where}", params)
        total = cur.fetchone()[0]
        page = max(1, int(page or 1))
        per_page = min(100, max(1, int(per_page or 20)))
        offset = (page - 1) * per_page
        cur.execute(
            f"{MON_SELECT}{where} ORDER BY m.MonID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            params + [offset, per_page],
        )
        return {"items": fetch_all(cur), "total": total, "page": page, "per_page": per_page}


def chi_tiet_mon(mon_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"{MON_SELECT} WHERE m.MonID = ?", (mon_id,))
        return fetch_one(cur)


def _kiem_tra_mon(danh_muc_id, gia_ban, cursor):
    if not danh_muc_id:
        return "Danh muc la bat buoc"
    cursor.execute("SELECT TrangThai FROM dbo.DanhMuc WHERE DanhMucID = ?", (danh_muc_id,))
    dm = cursor.fetchone()
    if not dm:
        return "Danh muc khong ton tai"
    try:
        if float(gia_ban) < 0:
            return "Gia ban khong duoc am"
    except (TypeError, ValueError):
        return "Gia ban khong hop le"
    return None


def them_mon(ten_mon, danh_muc_id, gia_ban, mo_ta=None, hinh_anh=None):
    ten_mon = (ten_mon or "").strip()
    if not ten_mon:
        return None, "Ten mon la bat buoc"
    with get_connection() as conn:
        cur = conn.cursor()
        err = _kiem_tra_mon(danh_muc_id, gia_ban, cur)
        if err:
            return None, err
        cur.execute(
            "INSERT INTO dbo.Mon (DanhMucID, TenMon, MoTa, GiaBan, HinhAnh, TrangThai, NgayTao) "
            "OUTPUT INSERTED.MonID VALUES (?, ?, ?, ?, ?, 1, SYSDATETIME())",
            (danh_muc_id, ten_mon, (mo_ta or "").strip() or None, float(gia_ban), hinh_anh or None),
        )
        new_id = cur.fetchval()
        conn.commit()
        return chi_tiet_mon(new_id), None


def sua_mon(mon_id, ten_mon=None, danh_muc_id=None, gia_ban=None, mo_ta=None, hinh_anh=None):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.Mon WHERE MonID = ?", (mon_id,))
        if not cur.fetchone():
            return None, "Mon khong ton tai"
        sets, params = [], []
        if ten_mon is not None:
            if not ten_mon.strip():
                return None, "Ten mon khong duoc de trong"
            sets.append("TenMon = ?")
            params.append(ten_mon.strip())
        if danh_muc_id is not None:
            cur.execute("SELECT 1 FROM dbo.DanhMuc WHERE DanhMucID = ?", (danh_muc_id,))
            if not cur.fetchone():
                return None, "Danh muc khong ton tai"
            sets.append("DanhMucID = ?")
            params.append(danh_muc_id)
        if gia_ban is not None:
            try:
                if float(gia_ban) < 0:
                    return None, "Gia ban khong duoc am"
            except (TypeError, ValueError):
                return None, "Gia ban khong hop le"
            sets.append("GiaBan = ?")
            params.append(float(gia_ban))
        if mo_ta is not None:
            sets.append("MoTa = ?")
            params.append(mo_ta.strip() or None)
        if hinh_anh is not None:
            sets.append("HinhAnh = ?")
            params.append(hinh_anh or None)
        if not sets:
            return None, "Khong co gi de cap nhat"
        sets.append("NgayCapNhat = SYSDATETIME()")
        params.append(mon_id)
        cur.execute(f"UPDATE dbo.Mon SET {', '.join(sets)} WHERE MonID = ?", params)
        conn.commit()
        return chi_tiet_mon(mon_id), None


def doi_trang_thai_mon(mon_id, dang_ban):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.Mon WHERE MonID = ?", (mon_id,))
        if not cur.fetchone():
            return None, "Mon khong ton tai"
        cur.execute(
            "UPDATE dbo.Mon SET TrangThai = ?, NgayCapNhat = SYSDATETIME() WHERE MonID = ?",
            (1 if dang_ban else 0, mon_id),
        )
        conn.commit()
        return chi_tiet_mon(mon_id), None


def tim_kiem_mon(tu_khoa, chi_dang_ban=True):
    tu_khoa = (tu_khoa or "").strip()
    if not tu_khoa:
        return {"items": [], "total": 0}
    result = danh_sach_mon(tu_khoa=tu_khoa, chi_dang_ban=chi_dang_ban, page=1, per_page=50)
    return result
