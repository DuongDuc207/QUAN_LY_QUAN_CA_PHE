"""Logic nghiep vu module employees: NhanVien, CaLamViec, LichLamViec (Sprint 4).

Nguyen tac:
- Ho so nhan vien khong bi xoa, chi doi trang thai (DANG_LAM | TAM_NGHI | NGHI_VIEC).
- Moi ho so gan toi da 1 tai khoan dang nhap (UQ_NhanVien_TaiKhoanID) va nguoc lai.
- Chi xep lich cho nhan vien DANG_LAM vao ca dang dung. Mot nguoi khong bi xep 2 ca
  chong gio trong cung ngay. Khoa dong NhanVien (UPDLOCK, HOLDLOCK) khi xep lich de 2 nguoi
  xep cung luc khong lot trung.
- Ca qua dem (vd 22:00-06:00) tinh gio ket thuc sang ngay hom sau.
- Loi tra ve dang (None, (thong_bao, ma_http)).
"""

import datetime
import re
import uuid
from contextlib import closing

import pyodbc

from api.orders.service import loi
from database.connection import fetch_all, fetch_one, get_connection

TRANG_THAI_NV = ("DANG_LAM", "TAM_NGHI", "NGHI_VIEC")
TRANG_THAI_LICH = ("DA_XEP", "DA_LAM", "VANG", "DA_HUY")
_RE_SDT = re.compile(r"[0-9+ .\-]{8,15}")
_RE_MA_NV = re.compile(r"[A-Z0-9_-]{2,30}")
_RE_GIO = re.compile(r"([01]\d|2[0-3]):([0-5]\d)(:00)?")
MSG_BODY_SAI = "Du lieu gui len khong hop le"


# ---------- Tien ich ----------
def _id(gia_tri):
    if isinstance(gia_tri, bool) or gia_tri in (None, ""):
        return None
    if isinstance(gia_tri, float):
        if not gia_tri.is_integer():
            return None
        gia_tri = int(gia_tri)
    try:
        n = int(str(gia_tri).strip())
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= 2147483647 else None


def _chuoi(gia_tri, toi_da):
    """(chuoi_da_chuan_hoa_hoac_None, hop_le)."""
    if gia_tri is None:
        return None, True
    if not isinstance(gia_tri, str):
        return None, False
    return gia_tri.strip()[:toi_da] or None, True


def _ngay(gia_tri):
    if isinstance(gia_tri, datetime.date) and not isinstance(gia_tri, datetime.datetime):
        return gia_tri
    if not isinstance(gia_tri, str) or not gia_tri.strip():
        return None
    try:
        return datetime.date.fromisoformat(gia_tri.strip())
    except ValueError:
        return None


def _gio(gia_tri):
    if isinstance(gia_tri, datetime.time):
        return gia_tri.replace(second=0, microsecond=0)
    if not isinstance(gia_tri, str):
        return None
    m = _RE_GIO.fullmatch(gia_tri.strip())
    return datetime.time(int(m.group(1)), int(m.group(2))) if m else None


def _phan_trang(page, per_page):
    try:
        return max(1, int(page or 1)), min(100, max(1, int(per_page or 20)))
    except (TypeError, ValueError):
        return 1, 20


def _gio_str(t):
    """TIME (pyodbc tra time hoac chuoi 'HH:MM:SS') -> 'HH:MM'."""
    t = _gio(t)
    return t.strftime("%H:%M") if t else None


def _ca_ra_ngoai(ca):
    """TIME khong dua duoc vao JSON -> doi sang 'HH:MM'."""
    if ca:
        ca["GioBatDau"] = _gio_str(ca["GioBatDau"])
        ca["GioKetThuc"] = _gio_str(ca["GioKetThuc"])
        ca["QuaDem"] = ca["GioKetThuc"] < ca["GioBatDau"]
    return ca


def _khoang_phut(bat_dau, ket_thuc):
    """(phut_bat_dau, phut_ket_thuc) tinh tu 00:00 cua ngay lam; ca qua dem cong 24h."""
    a = bat_dau.hour * 60 + bat_dau.minute
    b = ket_thuc.hour * 60 + ket_thuc.minute
    return a, (b + 1440 if b <= a else b)


# =====================================================================
# Nhan vien (80-84)
# =====================================================================
NV_SELECT = (
    "SELECT n.*, t.Email AS EmailTaiKhoan, t.HoTen AS TenTaiKhoan FROM dbo.NhanVien n "
    "LEFT JOIN dbo.TaiKhoan t ON t.TaiKhoanID = n.TaiKhoanID"
)


def _doc_nv(cur, nv_id):
    cur.execute(f"{NV_SELECT} WHERE n.NhanVienID = ?", (nv_id,))
    return fetch_one(cur)


def danh_sach_nv(tu_khoa="", trang_thai="", page=1, per_page=20):
    where, params = " WHERE 1=1", []
    tu_khoa = (tu_khoa or "").strip()
    if tu_khoa:
        where += " AND (n.HoTen LIKE ? OR n.MaNhanVien LIKE ? OR n.SoDienThoai LIKE ?)"
        params += [f"%{tu_khoa}%"] * 3
    trang_thai = (trang_thai or "").strip().upper()
    if trang_thai:
        if trang_thai not in TRANG_THAI_NV:
            return loi("Trang thai nhan vien khong hop le")
        where += " AND n.TrangThai = ?"
        params.append(trang_thai)
    page, per_page = _phan_trang(page, per_page)
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM dbo.NhanVien n{where}", params)
        total = cur.fetchval()
        cur.execute(
            f"{NV_SELECT}{where} ORDER BY CASE n.TrangThai WHEN 'DANG_LAM' THEN 0 WHEN 'TAM_NGHI' THEN 1 ELSE 2 END, "
            "n.HoTen, n.NhanVienID OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            params + [(page - 1) * per_page, per_page],
        )
        return {"items": fetch_all(cur), "total": total, "page": page, "per_page": per_page}, None


def chi_tiet_nv(nv_id):
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        nv = _doc_nv(cur, nv_id)
        if not nv:
            return loi("Nhan vien khong ton tai", 404)
        cur.execute(
            f"{LICH_SELECT} WHERE l.NhanVienID = ? AND l.NgayLam >= CAST(SYSDATETIME() AS DATE) "
            "AND l.TrangThai <> 'DA_HUY' ORDER BY l.NgayLam, c.GioBatDau",
            (nv_id,),
        )
        nv["LichSapToi"] = [_lich_ra_ngoai(r) for r in fetch_all(cur)[:14]]
        return nv, None


def _chuan_hoa_nv(body, cu=None):
    if not isinstance(body, dict):
        return None, MSG_BODY_SAI
    cu = cu or {}
    gui = lambda k: k in body or not cu  # noqa: E731

    ho_ten = body.get("ho_ten") if gui("ho_ten") else cu["HoTen"]
    ho_ten = ho_ten.strip()[:100] if isinstance(ho_ten, str) else ""
    if not ho_ten:
        return None, "Ho ten nhan vien la bat buoc"

    if gui("ma_nhan_vien"):
        raw = body.get("ma_nhan_vien")
        if raw in (None, "") and not cu:
            ma = None  # tu sinh
        else:
            ma = raw.strip().upper() if isinstance(raw, str) else ""
            if not _RE_MA_NV.fullmatch(ma):
                return None, "Ma nhan vien phai tu 2 den 30 ky tu, chi gom chu, so, dau gach"
    else:
        ma = cu["MaNhanVien"]

    if gui("so_dien_thoai"):
        sdt, ok = _chuoi(body.get("so_dien_thoai"), 15)
        if not ok or (sdt and not _RE_SDT.fullmatch(sdt)):
            return None, "So dien thoai khong hop le"
    else:
        sdt = cu["SoDienThoai"]

    if gui("dia_chi"):
        dia_chi, ok = _chuoi(body.get("dia_chi"), 255)
        if not ok:
            return None, "Dia chi khong hop le"
    else:
        dia_chi = cu["DiaChi"]

    if gui("chuc_vu"):
        chuc_vu, ok = _chuoi(body.get("chuc_vu"), 50)
        if not ok:
            return None, "Chuc vu khong hop le"
    else:
        chuc_vu = cu["ChucVu"]

    if gui("ngay_vao_lam"):
        raw = body.get("ngay_vao_lam")
        ngay_vao = None if raw in (None, "") else _ngay(raw)
        if raw not in (None, "") and not ngay_vao:
            return None, "Ngay vao lam khong hop le"
    else:
        ngay_vao = cu["NgayVaoLam"]

    if gui("tai_khoan_id"):
        raw = body.get("tai_khoan_id")
        tk_id = None if raw in (None, "") else _id(raw)
        if raw not in (None, "") and not tk_id:
            return None, "Tai khoan khong ton tai"
    else:
        tk_id = cu["TaiKhoanID"]

    return {"ho_ten": ho_ten, "ma": ma, "sdt": sdt, "dia_chi": dia_chi, "chuc_vu": chuc_vu,
            "ngay_vao": ngay_vao, "tk_id": tk_id}, None


def _kiem_tai_khoan(cur, tk_id):
    if tk_id is None:
        return None
    cur.execute("SELECT 1 FROM dbo.TaiKhoan WHERE TaiKhoanID = ?", (tk_id,))
    return None if cur.fetchone() else ("Tai khoan khong ton tai", 404)


def _dich_loi_nv(e):
    text = str(e)
    if "UQ_NhanVien_MaNhanVien" in text:
        return "Ma nhan vien da ton tai", 409
    if "UQ_NhanVien_TaiKhoanID" in text:
        return "Tai khoan nay da gan cho nhan vien khac", 409
    return "Du lieu nhan vien khong hop le", 400


def tao_nv(body):
    d, err = _chuan_hoa_nv(body)
    if err:
        return loi(err)
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        err = _kiem_tai_khoan(cur, d["tk_id"])
        if err:
            return loi(*err)
        try:
            cur.execute(
                "INSERT INTO dbo.NhanVien (TaiKhoanID, MaNhanVien, HoTen, SoDienThoai, DiaChi, ChucVu, "
                "NgayVaoLam, TrangThai, NgayTao) OUTPUT INSERTED.NhanVienID "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'DANG_LAM', SYSDATETIME())",
                (d["tk_id"], d["ma"] or "TMP" + uuid.uuid4().hex[:20], d["ho_ten"], d["sdt"],
                 d["dia_chi"], d["chuc_vu"], d["ngay_vao"]),
            )
            nv_id = cur.fetchval()
            if not d["ma"]:
                cur.execute("UPDATE dbo.NhanVien SET MaNhanVien = ? WHERE NhanVienID = ?", (f"NV{nv_id:05d}", nv_id))
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_nv(e))
        conn.commit()
        return _doc_nv(cur, nv_id), None


def cap_nhat_nv(nv_id, body):
    if not isinstance(body, dict) or not body:
        return loi("Khong co gi de cap nhat")
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cu = _doc_nv(cur, nv_id)
        if not cu:
            return loi("Nhan vien khong ton tai", 404)
        d, err = _chuan_hoa_nv(body, cu)
        if err:
            return loi(err)
        err = _kiem_tai_khoan(cur, d["tk_id"])
        if err:
            return loi(*err)
        try:
            cur.execute(
                "UPDATE dbo.NhanVien SET TaiKhoanID = ?, MaNhanVien = ?, HoTen = ?, SoDienThoai = ?, DiaChi = ?, "
                "ChucVu = ?, NgayVaoLam = ?, NgayCapNhat = SYSDATETIME() WHERE NhanVienID = ?",
                (d["tk_id"], d["ma"], d["ho_ten"], d["sdt"], d["dia_chi"], d["chuc_vu"], d["ngay_vao"], nv_id),
            )
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_nv(e))
        conn.commit()
        return _doc_nv(cur, nv_id), None


def doi_trang_thai_nv(nv_id, trang_thai):
    """Nghi viec: huy luon cac lich DA_XEP tu hom nay tro di (khong de lich treo)."""
    trang_thai = (trang_thai or "").strip().upper() if isinstance(trang_thai, str) else ""
    if trang_thai not in TRANG_THAI_NV:
        return loi("Trang thai nhan vien khong hop le")
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE dbo.NhanVien SET TrangThai = ?, NgayCapNhat = SYSDATETIME() WHERE NhanVienID = ?",
            (trang_thai, nv_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return loi("Nhan vien khong ton tai", 404)
        so_lich_huy = 0
        if trang_thai == "NGHI_VIEC":
            cur.execute(
                "UPDATE dbo.LichLamViec SET TrangThai = 'DA_HUY', NgayCapNhat = SYSDATETIME(), "
                "GhiChu = COALESCE(GhiChu, N'Nhân viên nghỉ việc') "
                "WHERE NhanVienID = ? AND TrangThai = 'DA_XEP' AND NgayLam >= CAST(SYSDATETIME() AS DATE)",
                (nv_id,),
            )
            so_lich_huy = cur.rowcount
        conn.commit()
        nv = _doc_nv(cur, nv_id)
        nv["SoLichDaHuy"] = so_lich_huy
        return nv, None


# =====================================================================
# Ca lam viec (85-87)
# =====================================================================
def danh_sach_ca(trang_thai=""):
    trang_thai = (trang_thai or "").strip().lower()
    if trang_thai not in ("", "active", "inactive"):
        return loi("Trang thai loc khong hop le")
    sql = (
        "SELECT c.*, (SELECT COUNT(*) FROM dbo.LichLamViec l WHERE l.CaLamViecID = c.CaLamViecID "
        " AND l.TrangThai <> 'DA_HUY' AND l.NgayLam >= CAST(SYSDATETIME() AS DATE)) AS SoLichSapToi "
        "FROM dbo.CaLamViec c"
    )
    if trang_thai:
        sql += f" WHERE c.TrangThai = {1 if trang_thai == 'active' else 0}"
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(sql + " ORDER BY c.GioBatDau, c.TenCa")
        return [_ca_ra_ngoai(r) for r in fetch_all(cur)], None


def _doc_ca(cur, ca_id):
    cur.execute("SELECT * FROM dbo.CaLamViec WHERE CaLamViecID = ?", (ca_id,))
    return fetch_one(cur)


def _chuan_hoa_ca(body, cu=None):
    if not isinstance(body, dict):
        return None, MSG_BODY_SAI
    cu = cu or {}
    gui = lambda k: k in body or not cu  # noqa: E731
    ten = body.get("ten_ca") if gui("ten_ca") else cu["TenCa"]
    ten = ten.strip()[:50] if isinstance(ten, str) else ""
    if not ten:
        return None, "Ten ca la bat buoc"
    bat_dau = _gio(body.get("gio_bat_dau")) if gui("gio_bat_dau") else _gio(cu["GioBatDau"])
    ket_thuc = _gio(body.get("gio_ket_thuc")) if gui("gio_ket_thuc") else _gio(cu["GioKetThuc"])
    if not bat_dau or not ket_thuc:
        return None, "Gio lam viec khong hop le (HH:MM)"
    if bat_dau == ket_thuc:
        return None, "Gio bat dau va gio ket thuc khong duoc trung nhau"
    if gui("mo_ta"):
        mo_ta, ok = _chuoi(body.get("mo_ta"), 255)
        if not ok:
            return None, "Mo ta khong hop le"
    else:
        mo_ta = cu["MoTa"]
    trang_thai = cu.get("TrangThai", True)
    if "trang_thai" in body:
        if not isinstance(body["trang_thai"], bool):
            return None, "Trang thai phai la true hoac false"
        trang_thai = body["trang_thai"]
    return {"ten": ten, "bat_dau": bat_dau, "ket_thuc": ket_thuc, "mo_ta": mo_ta, "trang_thai": trang_thai}, None


def _dich_loi_ca(e):
    if "UQ_CaLamViec_TenCa" in str(e):
        return "Ten ca da ton tai", 409
    return "Du lieu ca lam viec khong hop le", 400


def tao_ca(body):
    d, err = _chuan_hoa_ca(body)
    if err:
        return loi(err)
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO dbo.CaLamViec (TenCa, GioBatDau, GioKetThuc, MoTa, TrangThai) "
                "OUTPUT INSERTED.CaLamViecID VALUES (?, ?, ?, ?, ?)",
                (d["ten"], d["bat_dau"], d["ket_thuc"], d["mo_ta"], 1 if d["trang_thai"] else 0),
            )
            ca_id = cur.fetchval()
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_ca(e))
        conn.commit()
        return _ca_ra_ngoai(_doc_ca(cur, ca_id)), None


def cap_nhat_ca(ca_id, body):
    """Doi gio cua ca dang co lich sap toi: kiem tra lai trung gio cho tung nhan vien."""
    if not isinstance(body, dict) or not body:
        return loi("Khong co gi de cap nhat")
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM dbo.CaLamViec WITH (UPDLOCK, HOLDLOCK) WHERE CaLamViecID = ?", (ca_id,))
        cu = fetch_one(cur)
        if not cu:
            conn.rollback()
            return loi("Ca lam viec khong ton tai", 404)
        d, err = _chuan_hoa_ca(body, cu)
        if err:
            conn.rollback()
            return loi(err)
        if (d["bat_dau"], d["ket_thuc"]) != (_gio(cu["GioBatDau"]), _gio(cu["GioKetThuc"])):
            a1, b1 = _khoang_phut(d["bat_dau"], d["ket_thuc"])
            cur.execute(
                "SELECT c2.GioBatDau, c2.GioKetThuc FROM dbo.LichLamViec l1 "
                "JOIN dbo.LichLamViec l2 ON l2.NhanVienID = l1.NhanVienID AND l2.NgayLam = l1.NgayLam "
                " AND l2.LichLamViecID <> l1.LichLamViecID AND l2.TrangThai <> 'DA_HUY' "
                "JOIN dbo.CaLamViec c2 ON c2.CaLamViecID = l2.CaLamViecID AND c2.CaLamViecID <> ? "
                "WHERE l1.CaLamViecID = ? AND l1.TrangThai <> 'DA_HUY' "
                "AND l1.NgayLam >= CAST(SYSDATETIME() AS DATE)",
                (ca_id, ca_id),
            )
            for r in cur.fetchall():
                a2, b2 = _khoang_phut(_gio(r.GioBatDau), _gio(r.GioKetThuc))
                if a1 < b2 and a2 < b1:
                    conn.rollback()
                    return loi("Gio moi bi chong voi ca khac cua nhan vien da duoc xep lich", 409)
        try:
            cur.execute(
                "UPDATE dbo.CaLamViec SET TenCa = ?, GioBatDau = ?, GioKetThuc = ?, MoTa = ?, TrangThai = ? "
                "WHERE CaLamViecID = ?",
                (d["ten"], d["bat_dau"], d["ket_thuc"], d["mo_ta"], 1 if d["trang_thai"] else 0, ca_id),
            )
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_ca(e))
        conn.commit()
        return _ca_ra_ngoai(_doc_ca(cur, ca_id)), None


# =====================================================================
# Lich lam viec (88-90)
# =====================================================================
LICH_SELECT = (
    "SELECT l.*, n.HoTen, n.MaNhanVien, n.TrangThai AS TrangThaiNhanVien, "
    "c.TenCa, c.GioBatDau, c.GioKetThuc FROM dbo.LichLamViec l "
    "JOIN dbo.NhanVien n ON n.NhanVienID = l.NhanVienID "
    "JOIN dbo.CaLamViec c ON c.CaLamViecID = l.CaLamViecID"
)


def _lich_ra_ngoai(r):
    if r:
        r["GioBatDau"] = _gio_str(r["GioBatDau"])
        r["GioKetThuc"] = _gio_str(r["GioKetThuc"])
    return r


def _doc_lich(cur, lich_id):
    cur.execute(f"{LICH_SELECT} WHERE l.LichLamViecID = ?", (lich_id,))
    return _lich_ra_ngoai(fetch_one(cur))


def danh_sach_lich(tu_ngay="", den_ngay="", nhan_vien_id="", ca_id="", trang_thai="", tai_khoan_id=None):
    """tai_khoan_id: chi xem lich cua chinh minh (nguoi khong co quyen xem nhan su)."""
    where, params = " WHERE 1=1", []
    tu = _ngay(tu_ngay) if (tu_ngay or "").strip() else datetime.date.today()
    den = _ngay(den_ngay) if (den_ngay or "").strip() else tu + datetime.timedelta(days=6)
    if not tu or not den:
        return loi("Ngay khong hop le (YYYY-MM-DD)")
    if tu > den:
        return loi("Ngay bat dau phai truoc hoac bang ngay ket thuc")
    if (den - tu).days > 92:
        return loi("Khoang thoi gian toi da 93 ngay")
    where += " AND l.NgayLam >= ? AND l.NgayLam <= ?"
    params += [tu, den]
    for gia_tri, cot, ten in ((nhan_vien_id, "l.NhanVienID", "Nhan vien"), (ca_id, "l.CaLamViecID", "Ca lam viec")):
        if (str(gia_tri or "")).strip():
            so = _id(gia_tri)
            if not so:
                return loi(f"{ten} khong ton tai", 404)
            where += f" AND {cot} = ?"
            params.append(so)
    trang_thai = (trang_thai or "").strip().upper()
    if trang_thai:
        if trang_thai not in TRANG_THAI_LICH:
            return loi("Trang thai lich khong hop le")
        where += " AND l.TrangThai = ?"
        params.append(trang_thai)
    if tai_khoan_id is not None:
        where += " AND n.TaiKhoanID = ?"
        params.append(tai_khoan_id)
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(f"{LICH_SELECT}{where} ORDER BY l.NgayLam, c.GioBatDau, n.HoTen, l.LichLamViecID", params)
        items = [_lich_ra_ngoai(r) for r in fetch_all(cur)]
    return {"TuNgay": tu, "DenNgay": den, "items": items, "total": len(items)}, None


def _kiem_tra_xep(cur, nv_id, ca_id, ngay, bo_qua_lich_id=None):
    """Khoa nhan vien roi kiem tra dieu kien xep lich. Tra ve loi hoac None."""
    cur.execute("SELECT TrangThai FROM dbo.NhanVien WITH (UPDLOCK, HOLDLOCK) WHERE NhanVienID = ?", (nv_id,))
    row = cur.fetchone()
    if not row:
        return "Nhan vien khong ton tai", 404
    if row.TrangThai != "DANG_LAM":
        return "Nhan vien khong o trang thai dang lam, khong the xep lich", 409
    ca = _doc_ca(cur, ca_id)
    if not ca:
        return "Ca lam viec khong ton tai", 404
    if not ca["TrangThai"]:
        return "Ca lam viec da ngung su dung", 409
    a1, b1 = _khoang_phut(_gio(ca["GioBatDau"]), _gio(ca["GioKetThuc"]))
    # Ca hom truoc qua dem cung co the chong sang dau ngay hom nay.
    cur.execute(
        "SELECT l.NgayLam, c.GioBatDau, c.GioKetThuc FROM dbo.LichLamViec l "
        "JOIN dbo.CaLamViec c ON c.CaLamViecID = l.CaLamViecID "
        "WHERE l.NhanVienID = ? AND l.TrangThai <> 'DA_HUY' AND l.NgayLam BETWEEN ? AND ? "
        "AND (? IS NULL OR l.LichLamViecID <> ?)",
        (nv_id, ngay - datetime.timedelta(days=1), ngay + datetime.timedelta(days=1),
         bo_qua_lich_id, bo_qua_lich_id),
    )
    for r in cur.fetchall():
        lech = (r.NgayLam - ngay).days * 1440
        a2, b2 = _khoang_phut(_gio(r.GioBatDau), _gio(r.GioKetThuc))
        if a1 < b2 + lech and a2 + lech < b1:
            return "Nhan vien da co ca lam viec trung gio trong ngay nay", 409
    return None


def _dich_loi_lich(e):
    if "UQ_LichLamViec_NV_Ca_Ngay" in str(e):
        return "Nhan vien da duoc xep vao ca nay trong ngay", 409
    return "Du lieu lich lam viec khong hop le", 400


def tao_lich(body):
    if not isinstance(body, dict):
        return loi(MSG_BODY_SAI)
    nv_id = _id(body.get("nhan_vien_id"))
    if not nv_id:
        return loi("Nhan vien khong ton tai", 404)
    ca_id = _id(body.get("ca_lam_viec_id"))
    if not ca_id:
        return loi("Ca lam viec khong ton tai", 404)
    ngay = _ngay(body.get("ngay_lam"))
    if not ngay:
        return loi("Ngay lam khong hop le (YYYY-MM-DD)")
    if ngay < datetime.date.today():
        return loi("Khong the xep lich cho ngay da qua")
    ghi_chu, ok = _chuoi(body.get("ghi_chu"), 255)
    if not ok:
        return loi("Ghi chu khong hop le")
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        err = _kiem_tra_xep(cur, nv_id, ca_id, ngay)
        if err:
            conn.rollback()
            return loi(*err)
        try:
            cur.execute(
                "INSERT INTO dbo.LichLamViec (NhanVienID, CaLamViecID, NgayLam, TrangThai, GhiChu, NgayTao) "
                "OUTPUT INSERTED.LichLamViecID VALUES (?, ?, ?, 'DA_XEP', ?, SYSDATETIME())",
                (nv_id, ca_id, ngay, ghi_chu),
            )
            lich_id = cur.fetchval()
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_lich(e))
        conn.commit()
        return _doc_lich(cur, lich_id), None


def cap_nhat_lich(lich_id, body):
    """Doi ca / ngay (chi khi lich con DA_XEP), doi trang thai (cham cong / huy), ghi chu."""
    if not isinstance(body, dict) or not body:
        return loi("Khong co gi de cap nhat")
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM dbo.LichLamViec WITH (UPDLOCK, HOLDLOCK) WHERE LichLamViecID = ?", (lich_id,))
        cu = fetch_one(cur)
        if not cu:
            conn.rollback()
            return loi("Lich lam viec khong ton tai", 404)
        if cu["TrangThai"] == "DA_HUY":
            conn.rollback()
            return loi("Lich da huy, khong the sua. Hay xep lich moi", 409)

        ca_id, ngay = cu["CaLamViecID"], cu["NgayLam"]
        doi_xep = False
        if "ca_lam_viec_id" in body:
            ca_id = _id(body["ca_lam_viec_id"])
            if not ca_id:
                conn.rollback()
                return loi("Ca lam viec khong ton tai", 404)
            doi_xep = doi_xep or ca_id != cu["CaLamViecID"]
        if "ngay_lam" in body:
            ngay = _ngay(body["ngay_lam"])
            if not ngay:
                conn.rollback()
                return loi("Ngay lam khong hop le (YYYY-MM-DD)")
            doi_xep = doi_xep or ngay != cu["NgayLam"]

        trang_thai = cu["TrangThai"]
        if "trang_thai" in body:
            trang_thai = body["trang_thai"].strip().upper() if isinstance(body["trang_thai"], str) else ""
            if trang_thai not in TRANG_THAI_LICH:
                conn.rollback()
                return loi("Trang thai lich khong hop le")
        if trang_thai in ("DA_LAM", "VANG") and ngay > datetime.date.today():
            conn.rollback()
            return loi("Chua den ngay lam, chua the cham cong", 409)

        ghi_chu = cu["GhiChu"]
        if "ghi_chu" in body:
            ghi_chu, ok = _chuoi(body["ghi_chu"], 255)
            if not ok:
                conn.rollback()
                return loi("Ghi chu khong hop le")

        if doi_xep:
            if cu["TrangThai"] != "DA_XEP":
                conn.rollback()
                return loi("Lich da cham cong, khong the doi ca hoac ngay", 409)
            if ngay < datetime.date.today():
                conn.rollback()
                return loi("Khong the xep lich cho ngay da qua")
            err = _kiem_tra_xep(cur, cu["NhanVienID"], ca_id, ngay, lich_id)
            if err:
                conn.rollback()
                return loi(*err)
        try:
            cur.execute(
                "UPDATE dbo.LichLamViec SET CaLamViecID = ?, NgayLam = ?, TrangThai = ?, GhiChu = ?, "
                "NgayCapNhat = SYSDATETIME() WHERE LichLamViecID = ?",
                (ca_id, ngay, trang_thai, ghi_chu, lich_id),
            )
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_lich(e))
        conn.commit()
        return _doc_lich(cur, lich_id), None
