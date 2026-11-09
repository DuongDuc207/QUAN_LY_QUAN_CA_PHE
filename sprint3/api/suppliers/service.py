"""Logic nghiep vu module suppliers: NhaCungCap, PhieuNhap, ChiTietPhieuNhap (Sprint 3).

Nguyen tac:
- Tien luon do backend tinh (QD02): ThanhTien = SoLuong x DonGiaNhap lam tron 2 so le
  (ROUND_HALF_UP), TongTien = tong ThanhTien. Moi so tien client gui ngoai don gia bi bo qua.
- Tao / sua phieu KHONG dong vao ton kho. Chi xac nhan (cong) va huy phieu da nhan (tru)
  moi doi ton, va CHI qua api.inventory.ledger.ghi_bien_dong (QD06).
- Moi thao tac ghi nam trong 1 giao dich: loi o giua thi rollback het. Khoa dong phieu
  (UPDLOCK, HOLDLOCK) truoc, sau do khoa nguyen lieu theo NguyenLieuID tang dan de tranh deadlock.
- Du lieu phieu khong bao gio bi xoa (QD08), chi doi trang thai.
- Loi tra ve dang (None, (thong_bao, ma_http)).
"""

import datetime
import re
import uuid
from contextlib import closing
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import pyodbc

from api.inventory import ledger
from api.orders.service import loi
from database.connection import fetch_all, fetch_one, get_connection

TOI_DA_DONG = 100
SO_LUONG_DONG_TOI_DA = Decimal("1000000")
DON_GIA_TOI_DA = Decimal("1000000000")
# DECIMAL(18,2): toi da 16 chu so phan nguyen.
TONG_TIEN_TOI_DA = Decimal("9999999999999999.99")
_HAI_SO = Decimal("0.01")

_RE_SDT = re.compile(r"[0-9+ .\-]{8,15}")
_RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

MSG_BODY_SAI = "Du lieu gui len khong hop le"


# ---------- Tien ich ----------
def _id(gia_tri):
    """So nguyen duong cho khoa chinh; None neu khong hop le."""
    if isinstance(gia_tri, bool) or gia_tri is None:
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


def _tien(gia_tri):
    """Doi sang Decimal 2 chu so thap phan (ROUND_HALF_UP); None neu khong hop le."""
    if isinstance(gia_tri, bool) or gia_tri in (None, ""):
        return None
    try:
        so = Decimal(str(gia_tri).strip()).quantize(_HAI_SO, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None
    return so if so.is_finite() else None


def _like(text):
    """Chuoi tim kiem LIKE an toan (thoat % _ [ ). Dung kem ESCAPE '\\'."""
    text = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_").replace("[", "\\[")
    return f"%{text}%"


def _phan_trang(page, per_page):
    try:
        return max(1, int(page or 1)), min(100, max(1, int(per_page or 20)))
    except (TypeError, ValueError):
        return 1, 20


def _chuan_ghi_chu(gia_tri):
    """(gia_tri_da_chuan_hoa, hop_le). None / rong -> None."""
    if gia_tri is None:
        return None, True
    if not isinstance(gia_tri, str):
        return None, False
    return gia_tri.strip()[:500] or None, True


def _giao_dich(thao_tac, doc):
    """Chay thao_tac(cur) -> (ket_qua, loi) trong 1 giao dich.

    Co loi hoac ngoai le: rollback het. Thanh cong: commit roi doc(cur, ket_qua).
    """
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        try:
            ket_qua, err = thao_tac(cur)
        except pyodbc.Error as e:
            conn.rollback()
            if "40001" in str(e):  # nan nhan deadlock
                return loi("He thong dang ban, vui long thu lai", 409)
            raise
        except BaseException:
            conn.rollback()
            raise
        if err:
            conn.rollback()
            return None, err
        conn.commit()
        return doc(cur, ket_qua), None


# =====================================================================
# NHA CUNG CAP
# =====================================================================
NCC_SELECT = (
    "SELECT n.*, (SELECT COUNT(*) FROM dbo.PhieuNhap p WHERE p.NhaCungCapID = n.NhaCungCapID) "
    "AS SoPhieuNhap FROM dbo.NhaCungCap n"
)


def danh_sach_ncc(tu_khoa="", trang_thai="", page=1, per_page=20):
    where, params = " WHERE 1=1", []
    tu_khoa = (tu_khoa or "").strip()[:100]
    if tu_khoa:
        where += (
            " AND (n.TenNhaCungCap LIKE ? ESCAPE '\\' OR n.SoDienThoai LIKE ? ESCAPE '\\' "
            "OR n.Email LIKE ? ESCAPE '\\')"
        )
        params += [_like(tu_khoa)] * 3
    trang_thai = (trang_thai or "").strip().lower()
    if trang_thai == "active":
        where += " AND n.TrangThai = 1"
    elif trang_thai == "inactive":
        where += " AND n.TrangThai = 0"
    elif trang_thai:
        return loi("Trang thai loc khong hop le (active hoac inactive)")
    page, per_page = _phan_trang(page, per_page)

    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM dbo.NhaCungCap n{where}", params)
        total = cur.fetchval()
        cur.execute(
            f"{NCC_SELECT}{where} ORDER BY n.TenNhaCungCap, n.NhaCungCapID "
            "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            params + [(page - 1) * per_page, per_page],
        )
        return {"items": fetch_all(cur), "total": total, "page": page, "per_page": per_page}, None


def _doc_ncc_day_du(cur, ncc_id):
    cur.execute(f"{NCC_SELECT} WHERE n.NhaCungCapID = ?", (ncc_id,))
    ncc = fetch_one(cur)
    if not ncc:
        return None
    cur.execute(
        "SELECT COUNT(*) AS TongSoPhieu, "
        "COALESCE(SUM(CASE WHEN TrangThai = 'DA_NHAN' THEN TongTien ELSE 0 END), 0) AS TongTienDaNhan "
        "FROM dbo.PhieuNhap WHERE NhaCungCapID = ?",
        (ncc_id,),
    )
    ncc.update(fetch_one(cur))
    cur.execute(
        f"{PHIEU_SELECT} WHERE p.NhaCungCapID = ? ORDER BY p.PhieuNhapID DESC "
        "OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY",
        (ncc_id,),
    )
    ncc["PhieuGanNhat"] = fetch_all(cur)
    return ncc


def chi_tiet_ncc(ncc_id):
    with closing(get_connection()) as conn:
        ncc = _doc_ncc_day_du(conn.cursor(), ncc_id)
        if not ncc:
            return loi("Nha cung cap khong ton tai", 404)
        return ncc, None


def _chuan_hoa_ncc(data, bat_buoc_ten):
    """Chi lay truong co mat trong data. Tra ve ({cot: gia_tri}, None) hoac (None, thong_bao)."""
    cot = {}
    if bat_buoc_ten or "ten_nha_cung_cap" in data:
        ten = data.get("ten_nha_cung_cap")
        ten = ten.strip()[:150] if isinstance(ten, str) else ""
        if not ten:
            return None, "Ten nha cung cap la bat buoc"
        cot["TenNhaCungCap"] = ten
    if "so_dien_thoai" in data:
        v = data["so_dien_thoai"]
        if v is None or (isinstance(v, str) and not v.strip()):
            cot["SoDienThoai"] = None
        elif isinstance(v, str) and _RE_SDT.fullmatch(v.strip()):
            cot["SoDienThoai"] = v.strip()
        else:
            return None, "So dien thoai khong hop le (8-15 ky tu gom so, +, dau cach, ., -)"
    if "email" in data:
        v = data["email"]
        if v is None or (isinstance(v, str) and not v.strip()):
            cot["Email"] = None
        elif isinstance(v, str) and len(v.strip()) <= 255 and _RE_EMAIL.fullmatch(v.strip()):
            cot["Email"] = v.strip()
        else:
            return None, "Email khong hop le"
    if "dia_chi" in data:
        v = data["dia_chi"]
        if v is None:
            cot["DiaChi"] = None
        elif isinstance(v, str):
            cot["DiaChi"] = v.strip()[:255] or None
        else:
            return None, "Dia chi khong hop le"
    return cot, None


def _dich_loi_ncc(e):
    if "UQ_NhaCungCap_TenNhaCungCap" in str(e):
        return "Nha cung cap da ton tai", 409
    return "Du lieu nha cung cap khong hop le", 400


def tao_ncc(data):
    if not isinstance(data, dict):
        return loi(MSG_BODY_SAI)
    cot, err = _chuan_hoa_ncc(data, bat_buoc_ten=True)
    if err:
        return loi(err)
    cot.setdefault("SoDienThoai", None)
    cot.setdefault("Email", None)
    cot.setdefault("DiaChi", None)

    def thao_tac(cur):
        try:
            cur.execute(
                "INSERT INTO dbo.NhaCungCap (TenNhaCungCap, SoDienThoai, Email, DiaChi, TrangThai) "
                "OUTPUT INSERTED.NhaCungCapID VALUES (?, ?, ?, ?, 1)",
                (cot["TenNhaCungCap"], cot["SoDienThoai"], cot["Email"], cot["DiaChi"]),
            )
        except pyodbc.IntegrityError as e:
            return loi(*_dich_loi_ncc(e))
        return cur.fetchval(), None

    return _giao_dich(thao_tac, _doc_ncc_day_du)


def cap_nhat_ncc(ncc_id, data):
    if not isinstance(data, dict):
        return loi(MSG_BODY_SAI)
    cot, err = _chuan_hoa_ncc(data, bat_buoc_ten=False)
    if err:
        return loi(err)
    if "trang_thai" in data:
        if not isinstance(data["trang_thai"], bool):
            return loi("Trang thai phai la true hoac false")
        cot["TrangThai"] = data["trang_thai"]
    if not cot:
        return loi("Khong co gi de cap nhat")

    def thao_tac(cur):
        cur.execute(
            "SELECT NhaCungCapID FROM dbo.NhaCungCap WITH (UPDLOCK, HOLDLOCK) WHERE NhaCungCapID = ?",
            (ncc_id,),
        )
        if not cur.fetchone():
            return loi("Nha cung cap khong ton tai", 404)
        # Ten cot lay tu danh sach co dinh trong _chuan_hoa_ncc, gia tri di qua dau ?.
        set_sql = ", ".join(f"{c} = ?" for c in cot)
        try:
            cur.execute(
                f"UPDATE dbo.NhaCungCap SET {set_sql}, NgayCapNhat = SYSDATETIME() WHERE NhaCungCapID = ?",
                (*cot.values(), ncc_id),
            )
        except pyodbc.IntegrityError as e:
            return loi(*_dich_loi_ncc(e))
        return ncc_id, None

    return _giao_dich(thao_tac, _doc_ncc_day_du)


# =====================================================================
# PHIEU NHAP
# =====================================================================
PHIEU_SELECT = (
    "SELECT p.*, n.TenNhaCungCap, t.HoTen AS NguoiLap, x.HoTen AS NguoiXacNhan, "
    "(SELECT COUNT(*) FROM dbo.ChiTietPhieuNhap c WHERE c.PhieuNhapID = p.PhieuNhapID) AS SoDong "
    "FROM dbo.PhieuNhap p "
    "JOIN dbo.NhaCungCap n ON n.NhaCungCapID = p.NhaCungCapID "
    "LEFT JOIN dbo.TaiKhoan t ON t.TaiKhoanID = p.TaiKhoanID "
    "LEFT JOIN dbo.TaiKhoan x ON x.TaiKhoanID = p.TaiKhoanXacNhanID"
)
TRANG_THAI_PHIEU = ("NHAP", "DA_NHAN", "DA_HUY")


def danh_sach_phieu(trang_thai="", ncc_id="", tu_khoa="", tu_ngay="", den_ngay="", page=1, per_page=20):
    where, params = " WHERE 1=1", []
    trang_thai = (trang_thai or "").strip().upper()
    if trang_thai:
        if trang_thai not in TRANG_THAI_PHIEU:
            return loi("Trang thai phieu nhap khong hop le")
        where += " AND p.TrangThai = ?"
        params.append(trang_thai)
    if ncc_id not in (None, ""):
        ncc_id = _id(ncc_id)
        if ncc_id is None:
            return loi("Nha cung cap khong hop le")
        where += " AND p.NhaCungCapID = ?"
        params.append(ncc_id)
    tu_khoa = (tu_khoa or "").strip()[:50]
    if tu_khoa:
        where += " AND p.MaPhieuNhap LIKE ? ESCAPE '\\'"
        params.append(_like(tu_khoa))
    try:
        if tu_ngay:
            tu = datetime.date.fromisoformat(tu_ngay.strip())
            where += " AND p.NgayNhap >= ?"
            params.append(tu)
        if den_ngay:
            den = datetime.date.fromisoformat(den_ngay.strip()) + datetime.timedelta(days=1)
            where += " AND p.NgayNhap < ?"
            params.append(den)
    except (ValueError, OverflowError):
        return loi("Ngay khong hop le (YYYY-MM-DD)")
    page, per_page = _phan_trang(page, per_page)

    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM dbo.PhieuNhap p{where}", params)
        total = cur.fetchval()
        cur.execute(
            f"{PHIEU_SELECT}{where} ORDER BY p.PhieuNhapID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            params + [(page - 1) * per_page, per_page],
        )
        return {"items": fetch_all(cur), "total": total, "page": page, "per_page": per_page}, None


def _doc_phieu_day_du(cur, phieu_id):
    cur.execute(f"{PHIEU_SELECT} WHERE p.PhieuNhapID = ?", (phieu_id,))
    phieu = fetch_one(cur)
    if not phieu:
        return None
    cur.execute(
        "SELECT c.*, nl.TenNguyenLieu, nl.DonViTinh FROM dbo.ChiTietPhieuNhap c "
        "JOIN dbo.NguyenLieu nl ON nl.NguyenLieuID = c.NguyenLieuID "
        "WHERE c.PhieuNhapID = ? ORDER BY c.ChiTietPhieuNhapID",
        (phieu_id,),
    )
    phieu["ChiTiet"] = fetch_all(cur)
    phieu["DuocSua"] = phieu["TrangThai"] == "NHAP"
    return phieu


def chi_tiet_phieu(phieu_id):
    with closing(get_connection()) as conn:
        phieu = _doc_phieu_day_du(conn.cursor(), phieu_id)
        if not phieu:
            return loi("Phieu nhap khong ton tai", 404)
        return phieu, None


def _chuan_hoa_items(items):
    """Tra ve (danh_sach_dong, tong_tien, None) hoac (None, None, thong_bao)."""
    if not isinstance(items, list) or not items:
        return None, None, "Phieu nhap phai co it nhat 1 dong"
    if len(items) > TOI_DA_DONG:
        return None, None, f"Phieu nhap toi da {TOI_DA_DONG} dong"
    dong_list, da_co, tong = [], set(), Decimal("0")
    for raw in items:
        if not isinstance(raw, dict):
            return None, None, "Danh sach nguyen lieu khong hop le"
        nl_id = _id(raw.get("nguyen_lieu_id"))
        if nl_id is None:
            return None, None, "Nguyen lieu khong hop le"
        sl = ledger.so_luong(raw.get("so_luong"))
        if sl is None or sl <= 0 or sl > SO_LUONG_DONG_TOI_DA:
            return None, None, f"So luong phai lon hon 0 va khong qua {SO_LUONG_DONG_TOI_DA:f}"
        gia = _tien(raw.get("don_gia_nhap"))
        if gia is None or gia < 0 or gia > DON_GIA_TOI_DA:
            return None, None, f"Don gia nhap phai tu 0 den {DON_GIA_TOI_DA:f}"
        if nl_id in da_co:
            return None, None, "Nguyen lieu bi trung trong phieu nhap"
        da_co.add(nl_id)
        thanh_tien = (sl * gia).quantize(_HAI_SO, rounding=ROUND_HALF_UP)
        tong += thanh_tien
        dong_list.append({"nguyen_lieu_id": nl_id, "so_luong": sl, "don_gia": gia, "thanh_tien": thanh_tien})
    if tong > TONG_TIEN_TOI_DA:
        return None, None, "Tong tien phieu nhap qua lon"
    return dong_list, tong, None


def _kiem_tra_ncc(cur, ncc_id):
    """Nha cung cap phai ton tai va dang hop tac. Giu khoa chia se toi het giao dich."""
    cur.execute(
        "SELECT TenNhaCungCap, TrangThai FROM dbo.NhaCungCap WITH (HOLDLOCK) WHERE NhaCungCapID = ?",
        (ncc_id,),
    )
    ncc = cur.fetchone()
    if not ncc:
        return "Nha cung cap khong ton tai", 404
    if not ncc.TrangThai:
        return "Nha cung cap da ngung hop tac", 400
    return None


def _kiem_tra_nguyen_lieu(cur, dong_list):
    """Moi nguyen lieu phai ton tai va dang dung. Duyet theo ID tang dan."""
    for nl_id in sorted(d["nguyen_lieu_id"] for d in dong_list):
        cur.execute(
            "SELECT TenNguyenLieu, TrangThai FROM dbo.NguyenLieu WITH (HOLDLOCK) WHERE NguyenLieuID = ?",
            (nl_id,),
        )
        nl = cur.fetchone()
        if not nl:
            return "Nguyen lieu khong ton tai", 404
        if not nl.TrangThai:
            return f"Nguyen lieu {nl.TenNguyenLieu} da ngung su dung", 400
    return None


def _them_dong(cur, phieu_id, dong_list):
    for d in dong_list:
        cur.execute(
            "INSERT INTO dbo.ChiTietPhieuNhap (PhieuNhapID, NguyenLieuID, SoLuong, DonGiaNhap, ThanhTien) "
            "VALUES (?, ?, ?, ?, ?)",
            (phieu_id, d["nguyen_lieu_id"], d["so_luong"], d["don_gia"], d["thanh_tien"]),
        )


def _khoa_phieu(cur, phieu_id):
    cur.execute(
        "SELECT * FROM dbo.PhieuNhap WITH (UPDLOCK, HOLDLOCK) WHERE PhieuNhapID = ?", (phieu_id,)
    )
    return fetch_one(cur)


def tao_phieu(tai_khoan_id, data):
    if not isinstance(data, dict):
        return loi(MSG_BODY_SAI)
    ncc_id = _id(data.get("nha_cung_cap_id"))
    if ncc_id is None:
        return loi("Nha cung cap khong hop le")
    dong_list, tong, err = _chuan_hoa_items(data.get("items"))
    if err:
        return loi(err)
    ghi_chu, hop_le = _chuan_ghi_chu(data.get("ghi_chu"))
    if not hop_le:
        return loi("Ghi chu khong hop le")

    def thao_tac(cur):
        err = _kiem_tra_ncc(cur, ncc_id) or _kiem_tra_nguyen_lieu(cur, dong_list)
        if err:
            return None, err
        # Ma tam de qua rang buoc UNIQUE, doi sang ma that ngay sau khi co ID.
        cur.execute(
            "INSERT INTO dbo.PhieuNhap (NhaCungCapID, TaiKhoanID, MaPhieuNhap, TongTien, TrangThai, GhiChu) "
            "OUTPUT INSERTED.PhieuNhapID, INSERTED.NgayNhap VALUES (?, ?, ?, 0, 'NHAP', ?)",
            (ncc_id, tai_khoan_id, "TMP" + uuid.uuid4().hex[:20], ghi_chu),
        )
        phieu_id, ngay = cur.fetchone()
        _them_dong(cur, phieu_id, dong_list)
        cur.execute(
            "UPDATE dbo.PhieuNhap SET MaPhieuNhap = ?, TongTien = ? WHERE PhieuNhapID = ?",
            (f"PN{ngay:%y%m%d}-{phieu_id:05d}", tong, phieu_id),
        )
        return phieu_id, None

    return _giao_dich(thao_tac, _doc_phieu_day_du)


def cap_nhat_phieu(phieu_id, data):
    if not isinstance(data, dict):
        return loi(MSG_BODY_SAI)
    co_ncc, co_ghi_chu, co_items = "nha_cung_cap_id" in data, "ghi_chu" in data, "items" in data
    if not (co_ncc or co_ghi_chu or co_items):
        return loi("Khong co gi de cap nhat")
    ncc_id = ghi_chu = dong_list = tong = None
    if co_ncc:
        ncc_id = _id(data["nha_cung_cap_id"])
        if ncc_id is None:
            return loi("Nha cung cap khong hop le")
    if co_ghi_chu:
        ghi_chu, hop_le = _chuan_ghi_chu(data["ghi_chu"])
        if not hop_le:
            return loi("Ghi chu khong hop le")
    if co_items:
        dong_list, tong, err = _chuan_hoa_items(data["items"])
        if err:
            return loi(err)

    def thao_tac(cur):
        phieu = _khoa_phieu(cur, phieu_id)
        if not phieu:
            return loi("Phieu nhap khong ton tai", 404)
        if phieu["TrangThai"] != "NHAP":
            return loi("Phieu da xac nhan hoac da huy, khong the sua", 409)
        if co_ncc and ncc_id != phieu["NhaCungCapID"]:
            err = _kiem_tra_ncc(cur, ncc_id)
            if err:
                return None, err
        if co_items:
            err = _kiem_tra_nguyen_lieu(cur, dong_list)
            if err:
                return None, err
            cur.execute("DELETE FROM dbo.ChiTietPhieuNhap WHERE PhieuNhapID = ?", (phieu_id,))
            _them_dong(cur, phieu_id, dong_list)
        cur.execute(
            "UPDATE dbo.PhieuNhap SET NhaCungCapID = ?, GhiChu = ?, NgayCapNhat = SYSDATETIME(), "
            "TongTien = (SELECT COALESCE(SUM(ThanhTien), 0) FROM dbo.ChiTietPhieuNhap WHERE PhieuNhapID = ?) "
            "WHERE PhieuNhapID = ?",
            (
                ncc_id if co_ncc else phieu["NhaCungCapID"],
                ghi_chu if co_ghi_chu else phieu["GhiChu"],
                phieu_id,
                phieu_id,
            ),
        )
        return phieu_id, None

    return _giao_dich(thao_tac, _doc_phieu_day_du)


def _doc_dong_theo_nguyen_lieu(cur, phieu_id):
    cur.execute(
        "SELECT NguyenLieuID, SoLuong FROM dbo.ChiTietPhieuNhap WHERE PhieuNhapID = ? "
        "ORDER BY NguyenLieuID",
        (phieu_id,),
    )
    return fetch_all(cur)


def xac_nhan_phieu(phieu_id, tai_khoan_id):
    """NHAP -> DA_NHAN: cong ton tung dong qua so cai kho. Toan bo hoac khong."""

    def thao_tac(cur):
        # Khoa phieu truoc: 2 luong cung xac nhan thi luong sau thay DA_NHAN va bi tu choi.
        phieu = _khoa_phieu(cur, phieu_id)
        if not phieu:
            return loi("Phieu nhap khong ton tai", 404)
        if phieu["TrangThai"] == "DA_NHAN":
            return loi("Phieu da duoc xac nhan truoc do", 409)
        if phieu["TrangThai"] == "DA_HUY":
            return loi("Phieu da huy, khong the xac nhan", 409)
        dong_list = _doc_dong_theo_nguyen_lieu(cur, phieu_id)
        if not dong_list:
            return loi("Phieu nhap khong co dong nao")
        ly_do = f"Nhap hang theo phieu {phieu['MaPhieuNhap']}"
        for dong in dong_list:  # NguyenLieuID tang dan
            cur.execute(
                "SELECT TenNguyenLieu, TrangThai FROM dbo.NguyenLieu WITH (UPDLOCK, HOLDLOCK) "
                "WHERE NguyenLieuID = ?",
                (dong["NguyenLieuID"],),
            )
            nl = cur.fetchone()
            if not nl:
                return loi("Nguyen lieu khong ton tai", 404)
            if not nl.TrangThai:
                return loi(f"Nguyen lieu {nl.TenNguyenLieu} da ngung su dung, khong the nhan hang", 409)
            _, err = ledger.ghi_bien_dong(
                cur, dong["NguyenLieuID"], tai_khoan_id, "NHAP_HANG", dong["SoLuong"], ly_do,
                phieu_nhap_id=phieu_id,
            )
            if err:
                return None, err
        cur.execute(
            "UPDATE dbo.PhieuNhap SET TrangThai = 'DA_NHAN', NgayXacNhan = SYSDATETIME(), "
            "TaiKhoanXacNhanID = ?, NgayCapNhat = SYSDATETIME() WHERE PhieuNhapID = ?",
            (tai_khoan_id, phieu_id),
        )
        return phieu_id, None

    return _giao_dich(thao_tac, _doc_phieu_day_du)


def huy_phieu(phieu_id, tai_khoan_id, ly_do, duoc_huy_da_nhan=False):
    """NHAP -> DA_HUY (khong dong ton). DA_NHAN -> DA_HUY chi khi duoc_huy_da_nhan, tru lai ton."""
    ly_do = ly_do.strip()[:500] if isinstance(ly_do, str) else ""
    if not ly_do:
        return loi("Ly do huy la bat buoc")

    def thao_tac(cur):
        phieu = _khoa_phieu(cur, phieu_id)
        if not phieu:
            return loi("Phieu nhap khong ton tai", 404)
        if phieu["TrangThai"] == "DA_HUY":
            return loi("Phieu da huy truoc do", 409)
        if phieu["TrangThai"] == "DA_NHAN":
            if not duoc_huy_da_nhan:
                return loi("Khong co quyen huy phieu da xac nhan", 403)
            noi_dung = f"Huy phieu nhap {phieu['MaPhieuNhap']}: {ly_do}"
            for dong in _doc_dong_theo_nguyen_lieu(cur, phieu_id):  # NguyenLieuID tang dan
                _, err = ledger.ghi_bien_dong(
                    cur, dong["NguyenLieuID"], tai_khoan_id, "HUY_NHAP", -Decimal(dong["SoLuong"]),
                    noi_dung, phieu_nhap_id=phieu_id,
                )
                if err:
                    return None, err
        cur.execute(
            "UPDATE dbo.PhieuNhap SET TrangThai = 'DA_HUY', LyDoHuy = ?, NgayCapNhat = SYSDATETIME() "
            "WHERE PhieuNhapID = ?",
            (ly_do, phieu_id),
        )
        return phieu_id, None

    return _giao_dich(thao_tac, _doc_phieu_day_du)
