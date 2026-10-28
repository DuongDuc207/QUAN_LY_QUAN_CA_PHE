"""Logic nghiep vu module auth: TaiKhoan, VaiTro, Quyen (Sprint 1, Nguoi 1)."""

from werkzeug.security import check_password_hash, generate_password_hash

from database.connection import fetch_all, fetch_one, get_connection

TRANG_THAI_HOP_LE = ("HOAT_DONG", "KHOA")


# ---------- Helpers ----------
def _quyen_cua_vai_tro(cursor, vai_tro_id):
    cursor.execute(
        "SELECT q.TenQuyen FROM dbo.VaiTroQuyen vq "
        "JOIN dbo.Quyen q ON q.QuyenID = vq.QuyenID "
        "WHERE vq.VaiTroID = ?",
        (vai_tro_id,),
    )
    return [r[0] for r in cursor.fetchall()]


def _tai_khoan_dict(row, quyens=None):
    data = dict(row)
    data.pop("MatKhauHash", None)
    if quyens is not None:
        data["Quyens"] = quyens
    return data


def _require_login(session):
    return session.get("tai_khoan_id")


def _require_perm(session, ten_quyen):
    return ten_quyen in (session.get("quyens") or [])


# ---------- Auth ----------
def dang_nhap(email, password):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT t.*, v.TenVaiTro FROM dbo.TaiKhoan t "
            "JOIN dbo.VaiTro v ON v.VaiTroID = t.VaiTroID "
            "WHERE t.Email = ?",
            (email,),
        )
        row = fetch_one(cur)
        if not row:
            return None, "Email hoac mat khau khong dung"
        if row["TrangThai"] != "HOAT_DONG":
            return None, "Tai khoan da bi khoa"
        if not check_password_hash(row["MatKhauHash"], password):
            return None, "Email hoac mat khau khong dung"
        quyens = _quyen_cua_vai_tro(cur, row["VaiTroID"])
        return _tai_khoan_dict(row, quyens), None


def lay_thong_tin_hien_tai(tai_khoan_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT t.*, v.TenVaiTro FROM dbo.TaiKhoan t "
            "JOIN dbo.VaiTro v ON v.VaiTroID = t.VaiTroID "
            "WHERE t.TaiKhoanID = ?",
            (tai_khoan_id,),
        )
        row = fetch_one(cur)
        if not row:
            return None
        return _tai_khoan_dict(row, _quyen_cua_vai_tro(cur, row["VaiTroID"]))


# ---------- Tai khoan ----------
def danh_sach_tai_khoan(tu_khoa="", trang_thai=""):
    with get_connection() as conn:
        cur = conn.cursor()
        sql = (
            "SELECT t.TaiKhoanID, t.HoTen, t.Email, t.SoDienThoai, t.TrangThai, "
            "t.NgayTao, t.NgayCapNhat, t.VaiTroID, v.TenVaiTro "
            "FROM dbo.TaiKhoan t JOIN dbo.VaiTro v ON v.VaiTroID = t.VaiTroID WHERE 1=1"
        )
        params = []
        if tu_khoa:
            sql += " AND (t.HoTen LIKE ? OR t.Email LIKE ?)"
            params += [f"%{tu_khoa}%", f"%{tu_khoa}%"]
        if trang_thai:
            sql += " AND t.TrangThai = ?"
            params.append(trang_thai)
        sql += " ORDER BY t.TaiKhoanID DESC"
        cur.execute(sql, params)
        return fetch_all(cur)


def chi_tiet_tai_khoan(tai_khoan_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT t.TaiKhoanID, t.HoTen, t.Email, t.SoDienThoai, t.TrangThai, "
            "t.NgayTao, t.NgayCapNhat, t.VaiTroID, v.TenVaiTro "
            "FROM dbo.TaiKhoan t JOIN dbo.VaiTro v ON v.VaiTroID = t.VaiTroID "
            "WHERE t.TaiKhoanID = ?",
            (tai_khoan_id,),
        )
        row = fetch_one(cur)
        if not row:
            return None
        row["Quyens"] = _quyen_cua_vai_tro(cur, row["VaiTroID"])
        return row


def tao_tai_khoan(ho_ten, email, password, vai_tro_id, so_dien_thoai=None):
    if not ho_ten or not email or not password:
        return None, "Ho ten, email va mat khau la bat buoc"
    if len(password) < 6:
        return None, "Mat khau phai tu 6 ky tu tro len"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.VaiTro WHERE VaiTroID = ?", (vai_tro_id,))
        if not cur.fetchone():
            return None, "Vai tro khong ton tai"
        cur.execute("SELECT 1 FROM dbo.TaiKhoan WHERE Email = ?", (email,))
        if cur.fetchone():
            return None, "Email da duoc su dung"
        cur.execute(
            "INSERT INTO dbo.TaiKhoan (VaiTroID, HoTen, Email, MatKhauHash, SoDienThoai, TrangThai, NgayTao) "
            "OUTPUT INSERTED.TaiKhoanID VALUES (?, ?, ?, ?, ?, 'HOAT_DONG', SYSDATETIME())",
            (vai_tro_id, ho_ten, email, generate_password_hash(password), so_dien_thoai),
        )
        new_id = cur.fetchval()
        conn.commit()
        return chi_tiet_tai_khoan(new_id), None


def cap_nhat_tai_khoan(tai_khoan_id, ho_ten=None, vai_tro_id=None, so_dien_thoai=None, mat_khau=None):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.TaiKhoan WHERE TaiKhoanID = ?", (tai_khoan_id,))
        if not cur.fetchone():
            return None, "Tai khoan khong ton tai"
        sets, params = [], []
        if ho_ten is not None:
            if not ho_ten.strip():
                return None, "Ho ten khong duoc de trong"
            sets.append("HoTen = ?")
            params.append(ho_ten.strip())
        if vai_tro_id is not None:
            cur.execute("SELECT 1 FROM dbo.VaiTro WHERE VaiTroID = ?", (vai_tro_id,))
            if not cur.fetchone():
                return None, "Vai tro khong ton tai"
            sets.append("VaiTroID = ?")
            params.append(vai_tro_id)
        if so_dien_thoai is not None:
            sets.append("SoDienThoai = ?")
            params.append(so_dien_thoai or None)
        if mat_khau:
            if len(mat_khau) < 6:
                return None, "Mat khau phai tu 6 ky tu tro len"
            sets.append("MatKhauHash = ?")
            params.append(generate_password_hash(mat_khau))
        if not sets:
            return None, "Khong co gi de cap nhat"
        sets.append("NgayCapNhat = SYSDATETIME()")
        params.append(tai_khoan_id)
        cur.execute(f"UPDATE dbo.TaiKhoan SET {', '.join(sets)} WHERE TaiKhoanID = ?", params)
        conn.commit()
        return chi_tiet_tai_khoan(tai_khoan_id), None


def doi_trang_thai_tai_khoan(tai_khoan_id, trang_thai, self_id=None):
    if trang_thai not in TRANG_THAI_HOP_LE:
        return None, "Trang thai phai la HOAT_DONG hoac KHOA"
    if self_id and int(self_id) == int(tai_khoan_id) and trang_thai == "KHOA":
        return None, "Khong the tu khoa tai khoan cua chinh minh"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.TaiKhoan WHERE TaiKhoanID = ?", (tai_khoan_id,))
        if not cur.fetchone():
            return None, "Tai khoan khong ton tai"
        cur.execute(
            "UPDATE dbo.TaiKhoan SET TrangThai = ?, NgayCapNhat = SYSDATETIME() WHERE TaiKhoanID = ?",
            (trang_thai, tai_khoan_id),
        )
        conn.commit()
        return chi_tiet_tai_khoan(tai_khoan_id), None


# ---------- Vai tro & quyen ----------
def danh_sach_vai_tro():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM dbo.VaiTro ORDER BY VaiTroID")
        roles = fetch_all(cur)
        for r in roles:
            r["Quyens"] = _quyen_cua_vai_tro(cur, r["VaiTroID"])
        return roles


def danh_sach_quyen():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM dbo.Quyen ORDER BY QuyenID")
        return fetch_all(cur)


def cap_nhat_quyen_cua_vai_tro(vai_tro_id, quyen_ids):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM dbo.VaiTro WHERE VaiTroID = ?", (vai_tro_id,))
        if not cur.fetchone():
            return None, "Vai tro khong ton tai"
        quyen_ids = list(dict.fromkeys([int(x) for x in (quyen_ids or [])]))
        if quyen_ids:
            placeholders = ",".join("?" * len(quyen_ids))
            cur.execute(f"SELECT QuyenID FROM dbo.Quyen WHERE QuyenID IN ({placeholders})", quyen_ids)
            hop_le = {r[0] for r in cur.fetchall()}
            la = [x for x in quyen_ids if x not in hop_le]
            if la:
                return None, f"Quyen khong ton tai: {la}"
        cur.execute("DELETE FROM dbo.VaiTroQuyen WHERE VaiTroID = ?", (vai_tro_id,))
        for qid in quyen_ids:
            cur.execute("INSERT INTO dbo.VaiTroQuyen (VaiTroID, QuyenID) VALUES (?, ?)", (vai_tro_id, qid))
        conn.commit()
        cur.execute("SELECT * FROM dbo.VaiTro WHERE VaiTroID = ?", (vai_tro_id,))
        role = fetch_one(cur)
        role["Quyens"] = _quyen_cua_vai_tro(cur, vai_tro_id)
        return role, None
