"""Logic nghiep vu module promotions: KhuyenMai, SuDungKhuyenMai (Sprint 4).

Nguyen tac:
- So tien giam luon tinh o backend tu tong tien don trong CSDL (QD02), lam tron toi dong.
  PHAN_TRAM: TongTien x GiaTriGiam / 100, toi da GiamToiDa (neu co). SO_TIEN: GiaTriGiam.
  Khong bao gio giam qua TongTien.
- Moi don toi da 1 khuyen mai (UQ_SuDungKhuyenMai_DonHangID).
- Luot da dung = so don CHUA HUY dang gan khuyen mai. Khi ap ma: khoa dong KhuyenMai
  (UPDLOCK, HOLDLOCK) roi moi dem luot -> 2 quay ap cung luc khong vuot SoLuongSuDung.
- Khuyen mai khong bi xoa, chi bat / tat (giu lich su don cu).
- Loi tra ve dang (None, (thong_bao, ma_http)).
"""

import datetime
import re
from contextlib import closing
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import pyodbc

from api.orders.service import loi
from database.connection import fetch_all, fetch_one, get_connection

LOAI_GIAM = ("PHAN_TRAM", "SO_TIEN")
TINH_TRANG = ("SAP_DIEN_RA", "DANG_DIEN_RA", "HET_LUOT", "DA_KET_THUC", "DA_TAT")
TIEN_TOI_DA = Decimal("1000000000")
LUOT_TOI_DA = 1000000
_RE_MA = re.compile(r"[A-Z0-9_-]{3,50}")
_DONG = Decimal("1")

MSG_BODY_SAI = "Du lieu gui len khong hop le"

# Luot da dung: don chua huy.
SO_LUOT_SQL = (
    "(SELECT COUNT(*) FROM dbo.SuDungKhuyenMai s JOIN dbo.DonHang d ON d.DonHangID = s.DonHangID "
    " WHERE s.KhuyenMaiID = k.KhuyenMaiID AND d.TrangThai <> 'DA_HUY')"
)
TINH_TRANG_SQL = (
    "CASE WHEN k.TrangThai = 0 THEN 'DA_TAT' "
    "WHEN SYSDATETIME() < k.NgayBatDau THEN 'SAP_DIEN_RA' "
    "WHEN SYSDATETIME() > k.NgayKetThuc THEN 'DA_KET_THUC' "
    f"WHEN k.SoLuongSuDung IS NOT NULL AND {SO_LUOT_SQL} >= k.SoLuongSuDung THEN 'HET_LUOT' "
    "ELSE 'DANG_DIEN_RA' END"
)
KM_SELECT = (
    f"SELECT k.*, {SO_LUOT_SQL} AS SoLuotDaDung, {TINH_TRANG_SQL} AS TinhTrang FROM dbo.KhuyenMai k"
)


# ---------- Tien ich ----------
def _tien(gia_tri):
    """Decimal 2 so le; None neu khong phai so."""
    if isinstance(gia_tri, bool) or gia_tri in (None, ""):
        return None
    try:
        so = Decimal(str(gia_tri).strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None
    return so if so.is_finite() else None


def _so_nguyen(gia_tri):
    if isinstance(gia_tri, bool) or gia_tri in (None, ""):
        return None
    if isinstance(gia_tri, float):
        if not gia_tri.is_integer():
            return None
        gia_tri = int(gia_tri)
    try:
        return int(str(gia_tri).strip())
    except (TypeError, ValueError):
        return None


def _thoi_gian(gia_tri):
    """'2026-10-23T08:00' | '2026-10-23 08:00:00' | '2026-10-23' -> datetime; None neu sai."""
    if not isinstance(gia_tri, str) or not gia_tri.strip():
        return None
    text = gia_tri.strip().replace(" ", "T")
    try:
        if len(text) == 10:
            return datetime.datetime.combine(datetime.date.fromisoformat(text), datetime.time())
        return datetime.datetime.fromisoformat(text).replace(tzinfo=None, microsecond=0)
    except ValueError:
        return None


def chuan_ma(gia_tri):
    """Ma khuyen mai viet hoa, bo khoang trang; None neu sai dinh dang."""
    if not isinstance(gia_tri, str):
        return None
    ma = gia_tri.strip().upper()
    return ma if _RE_MA.fullmatch(ma) else None


def _phan_trang(page, per_page):
    try:
        return max(1, int(page or 1)), min(100, max(1, int(per_page or 20)))
    except (TypeError, ValueError):
        return 1, 20


def tinh_giam(km, tong_tien):
    """So tien giam (lam tron toi dong) cho tong tien don; 0 neu chua dat toi thieu."""
    tong = Decimal(tong_tien or 0)
    if tong <= 0 or tong < Decimal(km["DonHangToiThieu"]):
        return Decimal("0")
    gia_tri = Decimal(km["GiaTriGiam"])
    if km["LoaiGiamGia"] == "PHAN_TRAM":
        giam = (tong * gia_tri / 100).quantize(_DONG, rounding=ROUND_HALF_UP)
        if km["GiamToiDa"] is not None:
            giam = min(giam, Decimal(km["GiamToiDa"]))
    else:
        giam = gia_tri
    return min(giam, tong).quantize(Decimal("0.01"))


# ---------- Doc ----------
def _doc_km(cur, km_id):
    cur.execute(f"{KM_SELECT} WHERE k.KhuyenMaiID = ?", (km_id,))
    return fetch_one(cur)


def danh_sach(tu_khoa="", tinh_trang="", page=1, per_page=20):
    where, params = " WHERE 1=1", []
    tu_khoa = (tu_khoa or "").strip()
    if tu_khoa:
        where += " AND (x.MaKhuyenMai LIKE ? OR x.TenKhuyenMai LIKE ?)"
        params += [f"%{tu_khoa}%", f"%{tu_khoa}%"]
    tinh_trang = (tinh_trang or "").strip().upper()
    if tinh_trang:
        if tinh_trang not in TINH_TRANG:
            return loi("Tinh trang khuyen mai khong hop le")
        where += " AND x.TinhTrang = ?"
        params.append(tinh_trang)
    page, per_page = _phan_trang(page, per_page)
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM ({KM_SELECT}) x{where}", params)
        total = cur.fetchval()
        cur.execute(
            f"SELECT * FROM ({KM_SELECT}) x{where} ORDER BY "
            "CASE x.TinhTrang WHEN 'DANG_DIEN_RA' THEN 0 WHEN 'SAP_DIEN_RA' THEN 1 ELSE 2 END, "
            "x.NgayBatDau DESC, x.KhuyenMaiID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            params + [(page - 1) * per_page, per_page],
        )
        return {"items": fetch_all(cur), "total": total, "page": page, "per_page": per_page}, None


def chi_tiet(km_id):
    with closing(get_connection()) as conn:
        km = _doc_km(conn.cursor(), km_id)
    if not km:
        return loi("Khuyen mai khong ton tai", 404)
    return km, None


def thong_ke_su_dung(km_id, page=1, per_page=20):
    page, per_page = _phan_trang(page, per_page)
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        km = _doc_km(cur, km_id)
        if not km:
            return loi("Khuyen mai khong ton tai", 404)
        cur.execute(
            "SELECT COUNT(*) AS SoLuot, COALESCE(SUM(s.SoTienGiam), 0) AS TongGiam, "
            "COALESCE(SUM(d.ThanhTien), 0) AS TongThuSauGiam FROM dbo.SuDungKhuyenMai s "
            "JOIN dbo.DonHang d ON d.DonHangID = s.DonHangID "
            "WHERE s.KhuyenMaiID = ? AND d.TrangThai <> 'DA_HUY'",
            (km_id,),
        )
        tong = fetch_one(cur)
        cur.execute("SELECT COUNT(*) FROM dbo.SuDungKhuyenMai WHERE KhuyenMaiID = ?", (km_id,))
        total = cur.fetchval()
        cur.execute(
            "SELECT s.SuDungKhuyenMaiID, s.DonHangID, s.SoTienGiam, s.NgaySuDung, d.MaDonHang, "
            "d.TongTien, d.ThanhTien, d.TrangThai AS TrangThaiDon FROM dbo.SuDungKhuyenMai s "
            "JOIN dbo.DonHang d ON d.DonHangID = s.DonHangID WHERE s.KhuyenMaiID = ? "
            "ORDER BY s.SuDungKhuyenMaiID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            (km_id, (page - 1) * per_page, per_page),
        )
        items = fetch_all(cur)
    con_lai = None
    if km["SoLuongSuDung"] is not None:
        con_lai = max(0, km["SoLuongSuDung"] - tong["SoLuot"])
    return {
        "KhuyenMai": km,
        "SoLuot": tong["SoLuot"],
        "TongGiam": tong["TongGiam"],
        "TongThuSauGiam": tong["TongThuSauGiam"],
        "SoLuotConLai": con_lai,
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }, None


# ---------- Kiem tra dau vao ----------
def _chuan_hoa(body, cu=None):
    """Kiem tra du lieu tao / sua. cu = ban ghi hien tai khi sua (truong khong gui giu nguyen)."""
    if not isinstance(body, dict):
        return None, MSG_BODY_SAI
    cu = cu or {}
    gui = lambda k: k in body  # noqa: E731

    ma = chuan_ma(body.get("ma_khuyen_mai")) if gui("ma_khuyen_mai") or not cu else cu["MaKhuyenMai"]
    if not ma:
        return None, "Ma khuyen mai phai tu 3 den 50 ky tu, chi gom chu, so, dau gach"

    ten = body.get("ten_khuyen_mai") if gui("ten_khuyen_mai") or not cu else cu["TenKhuyenMai"]
    ten = ten.strip()[:150] if isinstance(ten, str) else ""
    if not ten:
        return None, "Ten khuyen mai la bat buoc"

    loai = body.get("loai_giam_gia") if gui("loai_giam_gia") or not cu else cu["LoaiGiamGia"]
    loai = (loai or "").strip().upper() if isinstance(loai, str) else ""
    if loai not in LOAI_GIAM:
        return None, "Loai giam gia khong hop le"

    gia_tri = _tien(body.get("gia_tri_giam")) if gui("gia_tri_giam") or not cu else Decimal(cu["GiaTriGiam"])
    if gia_tri is None or gia_tri <= 0:
        return None, "Gia tri giam phai lon hon 0"
    if loai == "PHAN_TRAM" and gia_tri > 100:
        return None, "Giam theo phan tram chi tu 0 den 100"
    if loai == "SO_TIEN" and gia_tri > TIEN_TOI_DA:
        return None, "Gia tri giam qua lon"

    if gui("don_hang_toi_thieu") or not cu:
        raw = body.get("don_hang_toi_thieu")
        toi_thieu = Decimal("0") if raw in (None, "") else _tien(raw)
    else:
        toi_thieu = Decimal(cu["DonHangToiThieu"])
    if toi_thieu is None or toi_thieu < 0 or toi_thieu > TIEN_TOI_DA:
        return None, "Don hang toi thieu khong hop le"

    if gui("giam_toi_da") or not cu:
        raw = body.get("giam_toi_da")
        giam_toi_da = None if raw in (None, "") else _tien(raw)
        if raw not in (None, "") and (giam_toi_da is None or giam_toi_da <= 0 or giam_toi_da > TIEN_TOI_DA):
            return None, "Muc giam toi da khong hop le"
    else:
        giam_toi_da = cu["GiamToiDa"]
    if loai == "SO_TIEN":
        giam_toi_da = None  # chi co nghia voi giam phan tram

    if gui("so_luong_su_dung") or not cu:
        raw = body.get("so_luong_su_dung")
        so_luot = None if raw in (None, "") else _so_nguyen(raw)
        if raw not in (None, "") and (so_luot is None or not 1 <= so_luot <= LUOT_TOI_DA):
            return None, "So luot su dung phai la so nguyen tu 1"
    else:
        so_luot = cu["SoLuongSuDung"]

    bat_dau = _thoi_gian(body.get("ngay_bat_dau")) if gui("ngay_bat_dau") or not cu else cu["NgayBatDau"]
    ket_thuc = _thoi_gian(body.get("ngay_ket_thuc")) if gui("ngay_ket_thuc") or not cu else cu["NgayKetThuc"]
    if not bat_dau or not ket_thuc:
        return None, "Thoi gian ap dung khong hop le"
    if ket_thuc <= bat_dau:
        return None, "Ngay ket thuc phai sau ngay bat dau"

    trang_thai = cu.get("TrangThai", True)
    if gui("trang_thai"):
        if not isinstance(body["trang_thai"], bool):
            return None, "Trang thai phai la true hoac false"
        trang_thai = body["trang_thai"]

    return {
        "ma": ma, "ten": ten, "loai": loai, "gia_tri": gia_tri, "toi_thieu": toi_thieu,
        "giam_toi_da": giam_toi_da, "so_luot": so_luot, "bat_dau": bat_dau,
        "ket_thuc": ket_thuc, "trang_thai": trang_thai,
    }, None


def _dich_loi_trung(e):
    if "UQ_KhuyenMai_MaKhuyenMai" in str(e):
        return "Ma khuyen mai da ton tai", 409
    return "Du lieu khuyen mai khong hop le", 400


# ---------- Ghi ----------
def tao(body):
    d, err = _chuan_hoa(body)
    if err:
        return loi(err)
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO dbo.KhuyenMai (MaKhuyenMai, TenKhuyenMai, LoaiGiamGia, GiaTriGiam, "
                "DonHangToiThieu, GiamToiDa, SoLuongSuDung, NgayBatDau, NgayKetThuc, TrangThai, NgayTao) "
                "OUTPUT INSERTED.KhuyenMaiID VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSDATETIME())",
                (d["ma"], d["ten"], d["loai"], d["gia_tri"], d["toi_thieu"], d["giam_toi_da"],
                 d["so_luot"], d["bat_dau"], d["ket_thuc"], 1 if d["trang_thai"] else 0),
            )
            km_id = cur.fetchval()
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_trung(e))
        conn.commit()
        return _doc_km(cur, km_id), None


def cap_nhat(km_id, body):
    if not isinstance(body, dict) or not body:
        return loi("Khong co gi de cap nhat")
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT KhuyenMaiID FROM dbo.KhuyenMai WITH (UPDLOCK, HOLDLOCK) WHERE KhuyenMaiID = ?", (km_id,))
        if not cur.fetchone():
            conn.rollback()
            return loi("Khuyen mai khong ton tai", 404)
        cu = _doc_km(cur, km_id)
        d, err = _chuan_hoa(body, cu)
        if err:
            conn.rollback()
            return loi(err)
        cur.execute("SELECT COUNT(*) FROM dbo.SuDungKhuyenMai WHERE KhuyenMaiID = ?", (km_id,))
        da_gan = cur.fetchval()
        # Ma da in tren hoa don / da phat cho khach -> khong doi nua.
        if da_gan and d["ma"] != cu["MaKhuyenMai"]:
            conn.rollback()
            return loi("Khuyen mai da duoc su dung, khong the doi ma", 409)
        if d["so_luot"] is not None and d["so_luot"] < cu["SoLuotDaDung"]:
            conn.rollback()
            return loi("So luot su dung khong duoc nho hon so luot da dung", 409)
        try:
            cur.execute(
                "UPDATE dbo.KhuyenMai SET MaKhuyenMai = ?, TenKhuyenMai = ?, LoaiGiamGia = ?, GiaTriGiam = ?, "
                "DonHangToiThieu = ?, GiamToiDa = ?, SoLuongSuDung = ?, NgayBatDau = ?, NgayKetThuc = ?, "
                "TrangThai = ?, NgayCapNhat = SYSDATETIME() WHERE KhuyenMaiID = ?",
                (d["ma"], d["ten"], d["loai"], d["gia_tri"], d["toi_thieu"], d["giam_toi_da"],
                 d["so_luot"], d["bat_dau"], d["ket_thuc"], 1 if d["trang_thai"] else 0, km_id),
            )
        except pyodbc.IntegrityError as e:
            conn.rollback()
            return loi(*_dich_loi_trung(e))
        conn.commit()
        return _doc_km(cur, km_id), None


def doi_trang_thai(km_id, trang_thai):
    if not isinstance(trang_thai, bool):
        return loi("Trang thai phai la true hoac false")
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE dbo.KhuyenMai SET TrangThai = ?, NgayCapNhat = SYSDATETIME() WHERE KhuyenMaiID = ?",
            (1 if trang_thai else 0, km_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return loi("Khuyen mai khong ton tai", 404)
        conn.commit()
        return _doc_km(cur, km_id), None


# ---------- Ap dung vao don (goi tu orders.service, trong giao dich cua don) ----------
def _kiem_tra_dung_duoc(cur, km, don_hang_id=None):
    """Loi (thong_bao, ma) neu ma khong dung duoc luc nay; None neu dung duoc."""
    if not km:
        return "Ma khuyen mai khong ton tai", 404
    if not km["TrangThai"]:
        return "Khuyen mai dang tam tat", 409
    cur.execute("SELECT SYSDATETIME()")
    bay_gio = cur.fetchval()
    if bay_gio < km["NgayBatDau"]:
        return "Khuyen mai chua den thoi gian ap dung", 409
    if bay_gio > km["NgayKetThuc"]:
        return "Khuyen mai da het han", 409
    if km["SoLuongSuDung"] is not None:
        cur.execute(
            "SELECT COUNT(*) FROM dbo.SuDungKhuyenMai s JOIN dbo.DonHang d ON d.DonHangID = s.DonHangID "
            "WHERE s.KhuyenMaiID = ? AND d.TrangThai <> 'DA_HUY' AND (? IS NULL OR s.DonHangID <> ?)",
            (km["KhuyenMaiID"], don_hang_id, don_hang_id),
        )
        if cur.fetchval() >= km["SoLuongSuDung"]:
            return "Khuyen mai da het luot su dung", 409
    return None


def _kiem_tra_toi_thieu(km, tong_tien):
    if Decimal(tong_tien) < Decimal(km["DonHangToiThieu"]):
        return f"Don hang chua dat gia tri toi thieu ({Decimal(km['DonHangToiThieu']):,.0f}) de dung khuyen mai", 409
    return None


def ap_vao_don(cur, don_hang_id, ma, tong_tien):
    """Gan / thay / go khuyen mai cua don. ma rong -> go. Tra ve loi hoac None.

    Goi trong giao dich cua don (don da bi khoa). So tien giam do _tinh_lai_tien cap nhat sau.
    """
    if ma in (None, ""):
        cur.execute("DELETE FROM dbo.SuDungKhuyenMai WHERE DonHangID = ?", (don_hang_id,))
        return None
    ma = chuan_ma(ma)
    if not ma:
        return "Ma khuyen mai khong ton tai", 404
    cur.execute("SELECT * FROM dbo.KhuyenMai WITH (UPDLOCK, HOLDLOCK) WHERE MaKhuyenMai = ?", (ma,))
    km = fetch_one(cur)
    err = _kiem_tra_dung_duoc(cur, km, don_hang_id) or _kiem_tra_toi_thieu(km, tong_tien)
    if err:
        return err
    giam = tinh_giam(km, tong_tien)
    cur.execute("SELECT KhuyenMaiID FROM dbo.SuDungKhuyenMai WHERE DonHangID = ?", (don_hang_id,))
    co_san = cur.fetchone()
    if co_san:
        cur.execute(
            "UPDATE dbo.SuDungKhuyenMai SET KhuyenMaiID = ?, SoTienGiam = ?, "
            "NgaySuDung = CASE WHEN KhuyenMaiID = ? THEN NgaySuDung ELSE SYSDATETIME() END "
            "WHERE DonHangID = ?",
            (km["KhuyenMaiID"], giam, km["KhuyenMaiID"], don_hang_id),
        )
    else:
        cur.execute(
            "INSERT INTO dbo.SuDungKhuyenMai (KhuyenMaiID, DonHangID, SoTienGiam, NgaySuDung) "
            "VALUES (?, ?, ?, SYSDATETIME())",
            (km["KhuyenMaiID"], don_hang_id, giam),
        )
    return None


def tinh_lai_giam(cur, don_hang_id, tong_tien):
    """So tien giam moi cua don sau khi doi mon. (giam, bi_go).

    Don khong con dat toi thieu -> go khuyen mai (bi_go=True), giam = 0.
    """
    cur.execute(
        "SELECT k.* FROM dbo.SuDungKhuyenMai s JOIN dbo.KhuyenMai k ON k.KhuyenMaiID = s.KhuyenMaiID "
        "WHERE s.DonHangID = ?",
        (don_hang_id,),
    )
    km = fetch_one(cur)
    if not km:
        return Decimal("0"), False
    giam = tinh_giam(km, tong_tien)
    if giam <= 0:
        cur.execute("DELETE FROM dbo.SuDungKhuyenMai WHERE DonHangID = ?", (don_hang_id,))
        return Decimal("0"), True
    cur.execute("UPDATE dbo.SuDungKhuyenMai SET SoTienGiam = ? WHERE DonHangID = ?", (giam, don_hang_id))
    return giam, False


# ---------- 69. Kiem tra ma ----------
def kiem_tra_ma(body):
    """Kiem tra ma cho 1 don co san (don_hang_id) hoac gio hang chua tao don (items).

    Tong tien luon tinh lai tu gia trong CSDL, khong nhan so tien client gui.
    """
    if not isinstance(body, dict):
        return loi(MSG_BODY_SAI)
    ma = chuan_ma(body.get("ma_khuyen_mai"))
    if not ma:
        return loi("Ma khuyen mai khong ton tai", 404)
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        don_hang_id = body.get("don_hang_id")
        if don_hang_id not in (None, ""):
            don_hang_id = _so_nguyen(don_hang_id)
            if not don_hang_id:
                return loi("Don hang khong ton tai", 404)
            cur.execute(
                "SELECT d.DonHangID, (SELECT COALESCE(SUM(c.ThanhTien), 0) FROM dbo.ChiTietDonHang c "
                " WHERE c.DonHangID = d.DonHangID) AS Tong FROM dbo.DonHang d WHERE d.DonHangID = ?",
                (don_hang_id,),
            )
            row = cur.fetchone()
            if not row:
                return loi("Don hang khong ton tai", 404)
            tong = Decimal(row.Tong)
        else:
            items = body.get("items")
            if not isinstance(items, list) or not items:
                return loi("Can danh sach mon hoac don hang de kiem tra ma")
            tong = Decimal("0")
            for raw in items:
                if not isinstance(raw, dict):
                    return loi("Danh sach mon khong hop le")
                mon_id = _so_nguyen(raw.get("mon_id"))
                so_luong = _so_nguyen(raw.get("so_luong", 1))
                if not mon_id or so_luong is None or not 1 <= so_luong <= 999:
                    return loi("Danh sach mon khong hop le")
                cur.execute("SELECT GiaBan FROM dbo.Mon WHERE MonID = ?", (mon_id,))
                gia = cur.fetchval()
                if gia is None:
                    return loi("Mon khong ton tai", 404)
                tong += Decimal(gia) * so_luong
            don_hang_id = None

        cur.execute(f"{KM_SELECT} WHERE k.MaKhuyenMai = ?", (ma,))
        km = fetch_one(cur)
        err = _kiem_tra_dung_duoc(cur, km, don_hang_id) or _kiem_tra_toi_thieu(km, tong)
        if err:
            return loi(*err)
        giam = tinh_giam(km, tong)
        return {
            "KhuyenMai": km,
            "TongTien": tong,
            "SoTienGiam": giam,
            "ThanhTien": tong - giam,
        }, None
