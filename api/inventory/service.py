"""Logic nghiep vu module inventory: nguyen lieu, ton kho, cong thuc pha che (Sprint 3, API 39-53).

Nguyen tac:
- MOI thay doi SoLuongTon chi di qua api.inventory.ledger.ghi_bien_dong (QD06). Module nay
  khong UPDATE SoLuongTon truc tiep; NguyenLieu chi duoc tao voi ton = 0, ton ban dau
  duoc ghi nhu mot giao dich DIEU_CHINH.
- Moi thao tac ghi nhieu bang nam trong 1 giao dich. _giao_dich() luon rollback khi thoat
  ma chua commit, nen moi nhanh tra loi som deu khong de lai du lieu do dang.
- Khoa dong UPDLOCK, HOLDLOCK truoc khi doc-roi-ghi (nguyen lieu, mon, don hang).
  Nhieu nguyen lieu trong 1 giao dich luon duoc khoa / ghi theo NguyenLieuID tang dan.
- So luong do backend tinh va kiem tra (ledger.so_luong), khong tin so client gui (QD02).
- Loi tra ve dang (None, (thong_bao, ma_http)) qua ham loi() cua module orders.
"""

import datetime
import json
import re
from contextlib import contextmanager
from decimal import Decimal
from functools import wraps

import pyodbc

from api.inventory import ledger
from api.orders.service import loi
from database.connection import fetch_all, fetch_one, get_connection

TEN_TOI_DA = 150
DON_VI_TOI_DA = 30
LY_DO_TOI_DA = 500
SO_DONG_TOI_DA = 100
SO_LUONG_DONG_TOI_DA = Decimal("1000000")
ID_TOI_DA = 2147483647
TRANG_PHAI_TOI_DA = 1000000
GIAO_DICH_GAN_NHAT = 20

TINH_TRANG = ("DU", "SAP_HET", "HET")
# Don chi duoc tru kho khi da bat dau pha che.
TRANG_THAI_TRU_KHO = ("DANG_PHA_CHE", "HOAN_THANH")

# Trang thai kho tinh o backend: HET = 0; SAP_HET = 0 < ton <= muc toi thieu; con lai DU.
TINH_TRANG_SQL = (
    "CASE WHEN n.SoLuongTon = 0 THEN 'HET' "
    "WHEN n.SoLuongTon <= n.MucTonToiThieu THEN 'SAP_HET' ELSE 'DU' END"
)
SO_MON_SQL = "(SELECT COUNT(*) FROM dbo.CongThuc c WHERE c.NguyenLieuID = n.NguyenLieuID)"
LS_SELECT = (
    "SELECT l.*, n.TenNguyenLieu, n.DonViTinh, t.HoTen AS NguoiThucHien, "
    "d.MaDonHang, p.MaPhieuNhap "
    "FROM dbo.LichSuKho l "
    "JOIN dbo.NguyenLieu n ON n.NguyenLieuID = l.NguyenLieuID "
    "LEFT JOIN dbo.TaiKhoan t ON t.TaiKhoanID = l.TaiKhoanID "
    "LEFT JOIN dbo.DonHang d ON d.DonHangID = l.DonHangID "
    "LEFT JOIN dbo.PhieuNhap p ON p.PhieuNhapID = l.PhieuNhapID"
)


# ---------- Ha tang ----------
@contextmanager
def _giao_dich():
    """Mo ket noi + cursor; thoat ma chua commit thi rollback (an toan cho moi nhanh tra loi som)."""
    conn = get_connection()
    try:
        yield conn, conn.cursor()
    finally:
        try:
            conn.rollback()
        except pyodbc.Error:
            pass
        conn.close()


def _bao_ve(ham):
    """Deadlock (nan nhan bi chon) -> 409 de client thu lai thay vi loi 500."""

    @wraps(ham)
    def wrapper(*args, **kwargs):
        try:
            return ham(*args, **kwargs)
        except pyodbc.Error as e:
            if e.args and str(e.args[0]) == "40001":
                return loi("He thong dang ban, vui long thu lai", 409)
            raise

    return wrapper


def _la_trung(e):
    text = str(e)
    return "2627" in text or "2601" in text or "UNIQUE" in text.upper()


# ---------- Kiem tra dau vao ----------
def _la_id(gia_tri):
    return isinstance(gia_tri, int) and not isinstance(gia_tri, bool) and 1 <= gia_tri <= ID_TOI_DA


def _id(gia_tri):
    """ID duong trong khoang INT; chap nhan so nguyen hoac chuoi chu so. None neu sai."""
    if isinstance(gia_tri, bool):
        return None
    if isinstance(gia_tri, int):
        n = gia_tri
    elif isinstance(gia_tri, str) and re.fullmatch(r"[0-9]{1,10}", gia_tri.strip()):
        n = int(gia_tri.strip())
    else:
        return None
    return n if 1 <= n <= ID_TOI_DA else None


def _chuoi(gia_tri, toi_da):
    """Chuoi da cat khoang trang va cat theo do dai cot; None neu khong phai chuoi hoac rong."""
    if not isinstance(gia_tri, str):
        return None
    return gia_tri.strip()[:toi_da] or None


def _phan_trang(page, per_page):
    try:
        page = min(TRANG_PHAI_TOI_DA, max(1, int(page or 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = min(100, max(1, int(per_page or 20)))
    except (TypeError, ValueError):
        per_page = 20
    return page, per_page


def _like(tu_khoa):
    """Escape ky tu dac biet cua LIKE de tim dung chuoi nguoi dung go."""
    an_toan = tu_khoa.replace("[", "[[]").replace("%", "[%]").replace("_", "[_]")
    return f"%{an_toan}%"


def _ngay(gia_tri):
    """YYYY-MM-DD nghiem ngat; None neu sai."""
    if not isinstance(gia_tri, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", gia_tri):
        return None
    try:
        return datetime.date.fromisoformat(gia_tri)
    except ValueError:
        return None


def _chuoi_so(so):
    return f"{so:f}"


# ---------- Doc nguyen lieu ----------
def _doc_nl(cur, nl_id):
    cur.execute(
        f"SELECT n.*, {TINH_TRANG_SQL} AS TinhTrangKho, {SO_MON_SQL} AS SoMonDungNguyenLieu "
        "FROM dbo.NguyenLieu n WHERE n.NguyenLieuID = ?",
        (nl_id,),
    )
    return fetch_one(cur)


def _tra_cuu_nl(q, status, tinh_trang, page, per_page):
    where, params = " WHERE 1=1", []
    q = (q or "").strip()[:TEN_TOI_DA]
    if q:
        where += " AND n.TenNguyenLieu LIKE ?"
        params.append(_like(q))
    if status == "active":
        where += " AND n.TrangThai = 1"
    elif status == "inactive":
        where += " AND n.TrangThai = 0"
    if tinh_trang:
        where += f" AND {TINH_TRANG_SQL} = ?"
        params.append(tinh_trang)
    page, per_page = _phan_trang(page, per_page)
    with _giao_dich() as (conn, cur):
        cur.execute(f"SELECT COUNT(*) FROM dbo.NguyenLieu n{where}", params)
        total = cur.fetchval()
        cur.execute(
            f"SELECT n.*, {TINH_TRANG_SQL} AS TinhTrangKho FROM dbo.NguyenLieu n{where} "
            "ORDER BY n.TenNguyenLieu, n.NguyenLieuID OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            params + [(page - 1) * per_page, per_page],
        )
        items = fetch_all(cur)
    return {"items": items, "total": total, "page": page, "per_page": per_page}, None


# 39
def danh_sach_nguyen_lieu(q="", status="", page=1, per_page=20):
    status = (status or "").strip().lower()
    if status not in ("", "active", "inactive"):
        return loi("Trang thai khong hop le (active hoac inactive)")
    return _tra_cuu_nl(q, status, "", page, per_page)


# 41
def chi_tiet_nguyen_lieu(nl_id):
    if not _la_id(nl_id):
        return loi("Nguyen lieu khong ton tai", 404)
    with _giao_dich() as (conn, cur):
        nl = _doc_nl(cur, nl_id)
        if not nl:
            return loi("Nguyen lieu khong ton tai", 404)
        return nl, None


# 40
@_bao_ve
def tao_nguyen_lieu(tai_khoan_id, data):
    ten = _chuoi(data.get("ten_nguyen_lieu"), TEN_TOI_DA)
    if not ten:
        return loi("Ten nguyen lieu la bat buoc")
    don_vi = _chuoi(data.get("don_vi_tinh"), DON_VI_TOI_DA)
    if not don_vi:
        return loi("Don vi tinh la bat buoc")
    muc = Decimal(0)
    if data.get("muc_ton_toi_thieu") is not None:
        muc = ledger.so_luong(data.get("muc_ton_toi_thieu"))
        if muc is None or muc < 0:
            return loi("Muc ton toi thieu khong hop le")
    ton_dau = Decimal(0)
    if data.get("so_luong_ton_ban_dau") is not None:
        ton_dau = ledger.so_luong(data.get("so_luong_ton_ban_dau"))
        if ton_dau is None or ton_dau < 0:
            return loi("So luong ton ban dau khong hop le")

    with _giao_dich() as (conn, cur):
        cur.execute("SELECT 1 FROM dbo.NguyenLieu WHERE TenNguyenLieu = ?", (ten,))
        if cur.fetchone():
            return loi("Ten nguyen lieu da ton tai", 409)
        try:
            # Ton luon bat dau tu 0; ton ban dau di qua so cai (QD06).
            cur.execute(
                "INSERT INTO dbo.NguyenLieu (TenNguyenLieu, DonViTinh, SoLuongTon, MucTonToiThieu) "
                "OUTPUT INSERTED.NguyenLieuID VALUES (?, ?, 0, ?)",
                (ten, don_vi, muc),
            )
        except pyodbc.IntegrityError as e:
            if _la_trung(e):
                return loi("Ten nguyen lieu da ton tai", 409)
            return loi("Du lieu nguyen lieu khong hop le")
        nl_id = cur.fetchone()[0]
        if ton_dau > 0:
            _, err = ledger.ghi_bien_dong(
                cur, nl_id, tai_khoan_id, "DIEU_CHINH", ton_dau, "Ton kho ban dau"
            )
            if err:
                return None, err
        conn.commit()
        return _doc_nl(cur, nl_id), None


# 42
@_bao_ve
def cap_nhat_nguyen_lieu(nl_id, data):
    moi = {}
    if "ten_nguyen_lieu" in data:
        ten = _chuoi(data.get("ten_nguyen_lieu"), TEN_TOI_DA)
        if not ten:
            return loi("Ten nguyen lieu khong hop le")
        moi["TenNguyenLieu"] = ten
    if "don_vi_tinh" in data:
        don_vi = _chuoi(data.get("don_vi_tinh"), DON_VI_TOI_DA)
        if not don_vi:
            return loi("Don vi tinh khong hop le")
        moi["DonViTinh"] = don_vi
    if "muc_ton_toi_thieu" in data:
        muc = ledger.so_luong(data.get("muc_ton_toi_thieu"))
        if muc is None or muc < 0:
            return loi("Muc ton toi thieu khong hop le")
        moi["MucTonToiThieu"] = muc
    if not moi:
        return loi("Khong co gi de cap nhat")
    if not _la_id(nl_id):
        return loi("Nguyen lieu khong ton tai", 404)

    with _giao_dich() as (conn, cur):
        cur.execute(
            "SELECT TenNguyenLieu, DonViTinh FROM dbo.NguyenLieu WITH (UPDLOCK, HOLDLOCK) "
            "WHERE NguyenLieuID = ?",
            (nl_id,),
        )
        hien_tai = cur.fetchone()
        if not hien_tai:
            return loi("Nguyen lieu khong ton tai", 404)
        if "TenNguyenLieu" in moi:
            cur.execute(
                "SELECT 1 FROM dbo.NguyenLieu WHERE TenNguyenLieu = ? AND NguyenLieuID <> ?",
                (moi["TenNguyenLieu"], nl_id),
            )
            if cur.fetchone():
                return loi("Ten nguyen lieu da ton tai", 409)
        if "DonViTinh" in moi and moi["DonViTinh"] != hien_tai.DonViTinh:
            cur.execute(
                "SELECT CASE WHEN EXISTS (SELECT 1 FROM dbo.LichSuKho WHERE NguyenLieuID = ?) "
                "OR EXISTS (SELECT 1 FROM dbo.CongThuc WHERE NguyenLieuID = ?) THEN 1 ELSE 0 END",
                (nl_id, nl_id),
            )
            if cur.fetchval():
                return loi(
                    "Nguyen lieu da co lich su kho hoac nam trong cong thuc, khong the doi don vi tinh",
                    409,
                )
        set_sql = ", ".join(f"{cot} = ?" for cot in moi)
        try:
            cur.execute(
                f"UPDATE dbo.NguyenLieu SET {set_sql}, NgayCapNhat = SYSDATETIME() WHERE NguyenLieuID = ?",
                list(moi.values()) + [nl_id],
            )
        except pyodbc.IntegrityError as e:
            if _la_trung(e):
                return loi("Ten nguyen lieu da ton tai", 409)
            return loi("Du lieu nguyen lieu khong hop le")
        conn.commit()
        return _doc_nl(cur, nl_id), None


# 43
@_bao_ve
def doi_trang_thai_nguyen_lieu(nl_id, data):
    if data.get("dang_dung") is None:
        return loi("Thieu truong dang_dung")
    if not isinstance(data["dang_dung"], bool):
        return loi("dang_dung phai la true hoac false")
    if not _la_id(nl_id):
        return loi("Nguyen lieu khong ton tai", 404)
    with _giao_dich() as (conn, cur):
        cur.execute(
            "UPDATE dbo.NguyenLieu SET TrangThai = ?, NgayCapNhat = SYSDATETIME() WHERE NguyenLieuID = ?",
            (data["dang_dung"], nl_id),
        )
        if cur.rowcount == 0:
            return loi("Nguyen lieu khong ton tai", 404)
        conn.commit()
        return _doc_nl(cur, nl_id), None


# ---------- Ton kho ----------
# 44
def danh_sach_ton_kho(q="", tinh_trang="", status="", page=1, per_page=20):
    tinh_trang = (tinh_trang or "").strip().upper()
    if tinh_trang and tinh_trang not in TINH_TRANG:
        return loi("Tinh trang kho khong hop le (DU, SAP_HET hoac HET)")
    status = (status or "").strip().lower() or "active"
    if status not in ("active", "inactive", "all"):
        return loi("Trang thai khong hop le (active, inactive hoac all)")
    return _tra_cuu_nl(q, status, tinh_trang, page, per_page)


# 45
def danh_sach_sap_het():
    """Nguyen lieu dang dung ma HET hoac SAP_HET: het truoc, roi ti le ton/muc tang dan."""
    with _giao_dich() as (conn, cur):
        cur.execute(
            f"SELECT n.*, {TINH_TRANG_SQL} AS TinhTrangKho, "
            "CASE WHEN n.MucTonToiThieu > n.SoLuongTon THEN n.MucTonToiThieu - n.SoLuongTon ELSE 0 END "
            "AS CanNhapThem "
            "FROM dbo.NguyenLieu n WHERE n.TrangThai = 1 AND n.SoLuongTon <= n.MucTonToiThieu "
            "ORDER BY CASE WHEN n.SoLuongTon = 0 THEN 0 ELSE 1 END, "
            "CASE WHEN n.SoLuongTon = 0 THEN 0 "
            "     ELSE CAST(n.SoLuongTon AS FLOAT) / CAST(NULLIF(n.MucTonToiThieu, 0) AS FLOAT) END, "
            "CASE WHEN n.MucTonToiThieu > n.SoLuongTon THEN n.MucTonToiThieu - n.SoLuongTon ELSE 0 END DESC, "
            "n.TenNguyenLieu, n.NguyenLieuID"
        )
        return fetch_all(cur), None


# 46
def lich_su_kho(nguyen_lieu_id="", loai="", tu_ngay="", den_ngay="", page=1, per_page=20):
    where, params = " WHERE 1=1", []
    nguyen_lieu_id = (nguyen_lieu_id or "").strip()
    if nguyen_lieu_id:
        nl_id = _id(nguyen_lieu_id)
        if not nl_id:
            return loi("Nguyen lieu khong hop le")
        where += " AND l.NguyenLieuID = ?"
        params.append(nl_id)
    loai = (loai or "").strip().upper()
    if loai:
        if loai not in ledger.LOAI_GIAO_DICH:
            return loi("Loai giao dich khong hop le")
        where += " AND l.LoaiGiaoDich = ?"
        params.append(loai)
    tu, den = None, None
    if (tu_ngay or "").strip():
        tu = _ngay(tu_ngay.strip())
        if not tu:
            return loi("Ngay khong hop le")
        where += " AND l.NgayGiaoDich >= ?"
        params.append(tu)
    if (den_ngay or "").strip():
        den = _ngay(den_ngay.strip())
        if not den or den == datetime.date.max:
            return loi("Ngay khong hop le")
        # den_ngay tinh het ngay: lay den het 23:59:59 cua ngay do.
        where += " AND l.NgayGiaoDich < ?"
        params.append(den + datetime.timedelta(days=1))
    if tu and den and tu > den:
        return loi("Khoang ngay khong hop le")
    page, per_page = _phan_trang(page, per_page)
    with _giao_dich() as (conn, cur):
        cur.execute(f"SELECT COUNT(*) FROM dbo.LichSuKho l{where}", params)
        total = cur.fetchval()
        cur.execute(
            f"{LS_SELECT}{where} ORDER BY l.NgayGiaoDich DESC, l.LichSuKhoID DESC "
            "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            params + [(page - 1) * per_page, per_page],
        )
        items = fetch_all(cur)
    return {"items": items, "total": total, "page": page, "per_page": per_page}, None


# 47
@_bao_ve
def dieu_chinh_ton_kho(tai_khoan_id, data):
    nl_id = _id(data.get("nguyen_lieu_id"))
    if not nl_id:
        return loi("Nguyen lieu khong hop le")
    thuc_te = ledger.so_luong(data.get("so_luong_thuc_te"))
    if thuc_te is None or thuc_te < 0:
        return loi("So luong thuc te khong hop le")
    ly_do = _chuoi(data.get("ly_do"), LY_DO_TOI_DA)
    if not ly_do:
        return loi("Ly do la bat buoc")

    with _giao_dich() as (conn, cur):
        # Khoa dong truoc de chenh lech tinh tren ton dang giu, khong bi ai chen vao giua.
        cur.execute(
            "SELECT SoLuongTon FROM dbo.NguyenLieu WITH (UPDLOCK, HOLDLOCK) WHERE NguyenLieuID = ?",
            (nl_id,),
        )
        dong = cur.fetchone()
        if not dong:
            return loi("Nguyen lieu khong ton tai", 404)
        chenh_lech = thuc_te - Decimal(dong.SoLuongTon)
        if chenh_lech == 0:
            return loi("Ton kho khong thay doi")
        giao_dich, err = ledger.ghi_bien_dong(
            cur, nl_id, tai_khoan_id, "DIEU_CHINH", chenh_lech, ly_do
        )
        if err:
            return None, err
        conn.commit()
        return {"LichSuKho": giao_dich, "NguyenLieu": _doc_nl(cur, nl_id)}, None


# 48
@_bao_ve
def xuat_kho(tai_khoan_id, data):
    nl_id = _id(data.get("nguyen_lieu_id"))
    if not nl_id:
        return loi("Nguyen lieu khong hop le")
    so = ledger.so_luong(data.get("so_luong"))
    if so is None or so <= 0:
        return loi("So luong xuat phai lon hon 0")
    ly_do = _chuoi(data.get("ly_do"), LY_DO_TOI_DA)
    if not ly_do:
        return loi("Ly do la bat buoc")

    with _giao_dich() as (conn, cur):
        giao_dich, err = ledger.ghi_bien_dong(cur, nl_id, tai_khoan_id, "XUAT_KHO", -so, ly_do)
        if err:
            return None, err
        conn.commit()
        return {"LichSuKho": giao_dich, "NguyenLieu": _doc_nl(cur, nl_id)}, None


# 49
def ton_kho_nguyen_lieu(nl_id):
    if not _la_id(nl_id):
        return loi("Nguyen lieu khong ton tai", 404)
    with _giao_dich() as (conn, cur):
        nl = _doc_nl(cur, nl_id)
        if not nl:
            return loi("Nguyen lieu khong ton tai", 404)
        cur.execute(
            f"SELECT TOP {GIAO_DICH_GAN_NHAT} * FROM ({LS_SELECT} WHERE l.NguyenLieuID = ?) x "
            "ORDER BY x.NgayGiaoDich DESC, x.LichSuKhoID DESC",
            (nl_id,),
        )
        nl["GiaoDichGanNhat"] = fetch_all(cur)
        return nl, None


# ---------- Cong thuc ----------
def _dong_cong_thuc(cur, mon_id):
    cur.execute(
        "SELECT c.NguyenLieuID, n.TenNguyenLieu, n.DonViTinh, c.SoLuongCan, n.SoLuongTon, "
        "n.TrangThai AS NguyenLieuDangDung "
        "FROM dbo.CongThuc c JOIN dbo.NguyenLieu n ON n.NguyenLieuID = c.NguyenLieuID "
        "WHERE c.MonID = ? ORDER BY c.NguyenLieuID",
        (mon_id,),
    )
    return fetch_all(cur)


def _doc_cong_thuc(cur, mon_id):
    cur.execute("SELECT MonID, TenMon, GiaBan FROM dbo.Mon WHERE MonID = ?", (mon_id,))
    mon = fetch_one(cur)
    if not mon:
        return None
    items = _dong_cong_thuc(cur, mon_id)
    # So phan pha duoc = min(floor(ton / can)) tren cac dong; null neu chua co cong thuc.
    mon["items"] = items
    mon["SoPhanLamDuoc"] = (
        min(int(Decimal(r["SoLuongTon"]) // Decimal(r["SoLuongCan"])) for r in items) if items else None
    )
    return mon


def _anh_chup(dong_list):
    """Mang JSON {NguyenLieuID, TenNguyenLieu, DonViTinh, SoLuongCan} luu vao CongThucLichSu."""
    return json.dumps(
        [
            {
                "NguyenLieuID": r["NguyenLieuID"],
                "TenNguyenLieu": r["TenNguyenLieu"],
                "DonViTinh": r["DonViTinh"],
                "SoLuongCan": _chuoi_so(Decimal(r["SoLuongCan"])),
            }
            for r in dong_list
        ],
        ensure_ascii=False,
    )


# 50
def xem_cong_thuc(mon_id):
    if not _la_id(mon_id):
        return loi("Mon khong ton tai", 404)
    with _giao_dich() as (conn, cur):
        cong_thuc = _doc_cong_thuc(cur, mon_id)
        if not cong_thuc:
            return loi("Mon khong ton tai", 404)
        return cong_thuc, None


# 51
@_bao_ve
def luu_cong_thuc(tai_khoan_id, mon_id, data):
    items = data.get("items")
    if not isinstance(items, list):
        return loi("Danh sach nguyen lieu khong hop le")
    if len(items) > SO_DONG_TOI_DA:
        return loi(f"Cong thuc toi da {SO_DONG_TOI_DA} nguyen lieu")
    moi = {}
    for raw in items:
        if not isinstance(raw, dict):
            return loi("Danh sach nguyen lieu khong hop le")
        nl_id = _id(raw.get("nguyen_lieu_id"))
        if not nl_id:
            return loi("Nguyen lieu khong hop le")
        can = ledger.so_luong(raw.get("so_luong_can"))
        if can is None or can <= 0 or can > SO_LUONG_DONG_TOI_DA:
            return loi(f"So luong can phai lon hon 0 va khong qua {SO_LUONG_DONG_TOI_DA:f}")
        if nl_id in moi:
            return loi("Nguyen lieu bi trung trong cong thuc")
        moi[nl_id] = can
    ly_do = _chuoi(data.get("ly_do"), LY_DO_TOI_DA)
    if not _la_id(mon_id):
        return loi("Mon khong ton tai", 404)

    with _giao_dich() as (conn, cur):
        cur.execute("SELECT MonID FROM dbo.Mon WITH (UPDLOCK, HOLDLOCK) WHERE MonID = ?", (mon_id,))
        if not cur.fetchone():
            return loi("Mon khong ton tai", 404)
        cu = _dong_cong_thuc(cur, mon_id)
        cu_map = {r["NguyenLieuID"]: Decimal(r["SoLuongCan"]) for r in cu}

        # Khoa nguyen lieu theo thu tu ID tang dan (cung thu tu voi cac luong khac).
        thong_tin = {}
        for nl_id in sorted(moi):
            cur.execute(
                "SELECT NguyenLieuID, TenNguyenLieu, DonViTinh, TrangThai FROM dbo.NguyenLieu "
                "WITH (UPDLOCK, HOLDLOCK) WHERE NguyenLieuID = ?",
                (nl_id,),
            )
            nl = fetch_one(cur)
            if not nl:
                return loi("Nguyen lieu khong ton tai", 404)
            # Nguyen lieu moi them phai dang dung; dong da co trong cong thuc thi giu duoc.
            if nl_id not in cu_map and not nl["TrangThai"]:
                return loi(f"Nguyen lieu {nl['TenNguyenLieu']} da ngung dung")
            thong_tin[nl_id] = nl

        if cu_map == moi:
            return loi("Khong co gi de cap nhat")

        for nl_id in sorted(set(cu_map) - set(moi)):
            cur.execute("DELETE FROM dbo.CongThuc WHERE MonID = ? AND NguyenLieuID = ?", (mon_id, nl_id))
        for nl_id in sorted(moi):
            if nl_id in cu_map:
                if cu_map[nl_id] != moi[nl_id]:
                    cur.execute(
                        "UPDATE dbo.CongThuc SET SoLuongCan = ?, NgayCapNhat = SYSDATETIME() "
                        "WHERE MonID = ? AND NguyenLieuID = ?",
                        (moi[nl_id], mon_id, nl_id),
                    )
            else:
                cur.execute(
                    "INSERT INTO dbo.CongThuc (MonID, NguyenLieuID, SoLuongCan, NgayCapNhat) "
                    "VALUES (?, ?, ?, SYSDATETIME())",
                    (mon_id, nl_id, moi[nl_id]),
                )
        sau = [
            {
                "NguyenLieuID": nl_id,
                "TenNguyenLieu": thong_tin[nl_id]["TenNguyenLieu"],
                "DonViTinh": thong_tin[nl_id]["DonViTinh"],
                "SoLuongCan": moi[nl_id],
            }
            for nl_id in sorted(moi)
        ]
        cur.execute(
            "INSERT INTO dbo.CongThucLichSu (MonID, TaiKhoanID, TruocJson, SauJson, LyDo) "
            "VALUES (?, ?, ?, ?, ?)",
            (mon_id, tai_khoan_id, _anh_chup(cu), _anh_chup(sau), ly_do),
        )
        conn.commit()
        return _doc_cong_thuc(cur, mon_id), None


# 52
def lich_su_cong_thuc(mon_id, page=1, per_page=20):
    if not _la_id(mon_id):
        return loi("Mon khong ton tai", 404)
    page, per_page = _phan_trang(page, per_page)
    with _giao_dich() as (conn, cur):
        cur.execute("SELECT 1 FROM dbo.Mon WHERE MonID = ?", (mon_id,))
        if not cur.fetchone():
            return loi("Mon khong ton tai", 404)
        cur.execute("SELECT COUNT(*) FROM dbo.CongThucLichSu WHERE MonID = ?", (mon_id,))
        total = cur.fetchval()
        cur.execute(
            "SELECT h.CongThucLichSuID, h.NgayThayDoi, t.HoTen AS NguoiThayDoi, h.LyDo, "
            "h.TruocJson, h.SauJson "
            "FROM dbo.CongThucLichSu h LEFT JOIN dbo.TaiKhoan t ON t.TaiKhoanID = h.TaiKhoanID "
            "WHERE h.MonID = ? ORDER BY h.NgayThayDoi DESC, h.CongThucLichSuID DESC "
            "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            (mon_id, (page - 1) * per_page, per_page),
        )
        items = []
        for r in fetch_all(cur):
            truoc, sau = r.pop("TruocJson"), r.pop("SauJson")
            r["Truoc"] = json.loads(truoc) if truoc else []
            r["Sau"] = json.loads(sau) if sau else []
            items.append(r)
    return {"items": items, "total": total, "page": page, "per_page": per_page}, None


# 53
@_bao_ve
def tru_kho_theo_don(tai_khoan_id, data):
    """Tru kho theo cong thuc x so luong mon cua don. Toan bo hoac khong."""
    don_hang_id = _id(data.get("don_hang_id"))
    if not don_hang_id:
        return loi("Don hang khong hop le")

    with _giao_dich() as (conn, cur):
        # Khoa dong don: 2 yeu cau cung luc cho 1 don xep hang, yeu cau sau thay don da tru kho.
        cur.execute(
            "SELECT DonHangID, MaDonHang, TrangThai FROM dbo.DonHang WITH (UPDLOCK, HOLDLOCK) "
            "WHERE DonHangID = ?",
            (don_hang_id,),
        )
        don = cur.fetchone()
        if not don:
            return loi("Don hang khong ton tai", 404)
        if don.TrangThai == "DA_HUY":
            return loi("Don hang da huy, khong the tru kho", 409)
        if don.TrangThai not in TRANG_THAI_TRU_KHO:
            return loi("Don hang chua o buoc pha che, khong the tru kho", 409)
        cur.execute(
            "SELECT 1 FROM dbo.LichSuKho WHERE DonHangID = ? AND LoaiGiaoDich = 'TIEU_HAO'",
            (don_hang_id,),
        )
        if cur.fetchone():
            return loi("Don nay da duoc tru kho", 409)

        cur.execute(
            "SELECT DISTINCT ct.TenMon FROM dbo.ChiTietDonHang ct "
            "WHERE ct.DonHangID = ? AND NOT EXISTS (SELECT 1 FROM dbo.CongThuc c WHERE c.MonID = ct.MonID) "
            "ORDER BY ct.TenMon",
            (don_hang_id,),
        )
        mon_chua_co = [r.TenMon for r in cur.fetchall()]
        # Gop theo nguyen lieu, tang dan theo ID de tranh deadlock giua cac don.
        cur.execute(
            "SELECT c.NguyenLieuID, SUM(ct.SoLuong * c.SoLuongCan) AS TongCan "
            "FROM dbo.ChiTietDonHang ct JOIN dbo.CongThuc c ON c.MonID = ct.MonID "
            "WHERE ct.DonHangID = ? GROUP BY c.NguyenLieuID ORDER BY c.NguyenLieuID",
            (don_hang_id,),
        )
        can_tru = [(r.NguyenLieuID, Decimal(r.TongCan)) for r in cur.fetchall()]
        if not can_tru:
            return loi("Don khong co mon nao co cong thuc, khong co gi de tru kho")

        chi_tiet = []
        for nl_id, tong in can_tru:
            giao_dich, err = ledger.ghi_bien_dong(
                cur, nl_id, tai_khoan_id, "TIEU_HAO", -tong,
                f"Tieu hao cho don {don.MaDonHang}", don_hang_id=don_hang_id,
            )
            if err:
                return None, err
            chi_tiet.append(giao_dich)
        conn.commit()
        return {
            "DonHangID": don_hang_id,
            "MaDonHang": don.MaDonHang,
            "ChiTiet": chi_tiet,
            "MonChuaCoCongThuc": mon_chua_co,
        }, None
