"""Logic nghiep vu module reports: bao cao va thong ke (Sprint 4). Chi doc, khong ghi.

Quy uoc so lieu:
- Khoang ngay [tu_ngay, den_ngay] tinh ca 2 dau (YYYY-MM-DD), mac dinh 7 ngay gan nhat,
  toi da 366 ngay.
- Doanh thu thu duoc = tong SoTien cac giao dich da thu (THANH_CONG / HOAN_MOT_PHAN /
  DA_HOAN_TIEN) theo ThoiGianThanhToan. Tien hoan tinh theo NgayHoanTien.
  Doanh thu thuan = thu duoc - da hoan.
- Mon ban chay, so don: chi tinh don khong bi huy, theo ThoiGianDat.
- Chi phi nhap hang: phieu DA_NHAN theo NgayXacNhan.
- Loi tra ve dang (None, (thong_bao, ma_http)).
"""

import datetime
from contextlib import closing
from decimal import Decimal

from api.orders.service import TT_DA_THU, loi
from database.connection import fetch_all, fetch_one, get_connection

SO_NGAY_MAC_DINH = 7
SO_NGAY_TOI_DA = 366
_DA_THU_SQL = "(" + ", ".join(f"'{t}'" for t in TT_DA_THU) + ")"


def _khoang(tu_ngay="", den_ngay=""):
    """-> ((tu, den_cuoi_ngay_exclusive, tu_date, den_date), None) hoac loi."""
    try:
        den = datetime.date.fromisoformat(den_ngay.strip()) if (den_ngay or "").strip() else datetime.date.today()
        tu = (datetime.date.fromisoformat(tu_ngay.strip()) if (tu_ngay or "").strip()
              else den - datetime.timedelta(days=SO_NGAY_MAC_DINH - 1))
    except (ValueError, AttributeError):
        return loi("Ngay khong hop le (YYYY-MM-DD)")
    if tu > den:
        return loi("Ngay bat dau phai truoc hoac bang ngay ket thuc")
    if (den - tu).days + 1 > SO_NGAY_TOI_DA:
        return loi(f"Khoang thoi gian toi da {SO_NGAY_TOI_DA} ngay")
    bat_dau = datetime.datetime.combine(tu, datetime.time())
    ket_thuc = datetime.datetime.combine(den + datetime.timedelta(days=1), datetime.time())
    return (bat_dau, ket_thuc, tu, den), None


def _nhom_sql(cot, nhom):
    if nhom == "month":
        return f"DATEFROMPARTS(YEAR({cot}), MONTH({cot}), 1)"
    return f"CAST({cot} AS DATE)"


def _gioi_han(gia_tri, mac_dinh=10, toi_da=50):
    try:
        return min(toi_da, max(1, int(gia_tri or mac_dinh)))
    except (TypeError, ValueError):
        return mac_dinh


def _bao(khoang, **du_lieu):
    return {"TuNgay": khoang[2], "DenNgay": khoang[3], **du_lieu}


# ---------- 71. Doanh thu ----------
def _so_lieu_doanh_thu(cur, bd, kt):
    cur.execute(
        "SELECT COUNT(*) AS SoDonDaThu, COALESCE(SUM(p.SoTien), 0) AS DoanhThu, "
        "COALESCE(SUM(d.GiamGia), 0) AS TongGiamGia, COALESCE(SUM(d.TongTien), 0) AS TongTruocGiam "
        f"FROM dbo.ThanhToan p JOIN dbo.DonHang d ON d.DonHangID = p.DonHangID "
        f"WHERE p.TrangThai IN {_DA_THU_SQL} AND p.ThoiGianThanhToan >= ? AND p.ThoiGianThanhToan < ?",
        (bd, kt),
    )
    tong = fetch_one(cur)
    cur.execute(
        "SELECT COUNT(*) AS SoLanHoan, COALESCE(SUM(SoTienHoan), 0) AS TienHoan FROM dbo.HoanTien "
        "WHERE TrangThai = 'HOAN_THANH' AND NgayHoanTien >= ? AND NgayHoanTien < ?",
        (bd, kt),
    )
    tong.update(fetch_one(cur))
    tong["DoanhThuThuan"] = Decimal(tong["DoanhThu"]) - Decimal(tong["TienHoan"])
    tong["GiaTriTrungBinhDon"] = (
        (Decimal(tong["DoanhThu"]) / tong["SoDonDaThu"]).quantize(Decimal("1")) if tong["SoDonDaThu"] else Decimal("0")
    )
    return tong


def doanh_thu(tu_ngay="", den_ngay="", nhom="day"):
    khoang, err = _khoang(tu_ngay, den_ngay)
    if err:
        return None, err
    nhom = (nhom or "day").strip().lower()
    if nhom not in ("day", "month"):
        return loi("Cach nhom khong hop le (day hoac month)")
    bd, kt = khoang[0], khoang[1]
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        tong = _so_lieu_doanh_thu(cur, bd, kt)
        ky_tt = _nhom_sql("p.ThoiGianThanhToan", nhom)
        ky_ht = _nhom_sql("NgayHoanTien", nhom)
        cur.execute(
            f"SELECT {ky_tt} AS Ky, COUNT(*) AS SoDon, SUM(p.SoTien) AS DoanhThu FROM dbo.ThanhToan p "
            f"WHERE p.TrangThai IN {_DA_THU_SQL} AND p.ThoiGianThanhToan >= ? AND p.ThoiGianThanhToan < ? "
            f"GROUP BY {ky_tt}",
            (bd, kt),
        )
        theo_ky = {r["Ky"]: {"Ky": r["Ky"], "SoDon": r["SoDon"], "DoanhThu": r["DoanhThu"],
                             "TienHoan": Decimal("0")} for r in fetch_all(cur)}
        cur.execute(
            f"SELECT {ky_ht} AS Ky, SUM(SoTienHoan) AS TienHoan FROM dbo.HoanTien "
            "WHERE TrangThai = 'HOAN_THANH' AND NgayHoanTien >= ? AND NgayHoanTien < ? "
            f"GROUP BY {ky_ht}",
            (bd, kt),
        )
        for r in fetch_all(cur):
            theo_ky.setdefault(r["Ky"], {"Ky": r["Ky"], "SoDon": 0, "DoanhThu": Decimal("0")})["TienHoan"] = r["TienHoan"]
    # Du ky (ke ca ky khong ban duoc) de bieu do khong bi hut.
    ds, ky = [], khoang[2] if nhom == "day" else khoang[2].replace(day=1)
    while ky <= khoang[3]:
        dong = theo_ky.get(ky, {"Ky": ky, "SoDon": 0, "DoanhThu": Decimal("0"), "TienHoan": Decimal("0")})
        dong["DoanhThuThuan"] = Decimal(dong["DoanhThu"]) - Decimal(dong["TienHoan"])
        ds.append(dong)
        if nhom == "day":
            ky += datetime.timedelta(days=1)
        else:
            ky = (ky.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    return _bao(khoang, Nhom=nhom, TongQuan=tong, TheoKy=ds), None


# ---------- 72. Don hang ----------
def don_hang(tu_ngay="", den_ngay=""):
    khoang, err = _khoang(tu_ngay, den_ngay)
    if err:
        return None, err
    bd, kt = khoang[0], khoang[1]
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT TrangThai, COUNT(*) AS SoDon, COALESCE(SUM(ThanhTien), 0) AS GiaTri FROM dbo.DonHang "
            "WHERE ThoiGianDat >= ? AND ThoiGianDat < ? GROUP BY TrangThai",
            (bd, kt),
        )
        theo_tt = fetch_all(cur)
        cur.execute(
            "SELECT CAST(ThoiGianDat AS DATE) AS Ngay, COUNT(*) AS SoDon, "
            "SUM(CASE WHEN TrangThai = 'DA_HUY' THEN 1 ELSE 0 END) AS SoDonHuy FROM dbo.DonHang "
            "WHERE ThoiGianDat >= ? AND ThoiGianDat < ? GROUP BY CAST(ThoiGianDat AS DATE) ORDER BY Ngay",
            (bd, kt),
        )
        theo_ngay = fetch_all(cur)
        cur.execute(
            "SELECT DATEPART(HOUR, ThoiGianDat) AS Gio, COUNT(*) AS SoDon FROM dbo.DonHang "
            "WHERE ThoiGianDat >= ? AND ThoiGianDat < ? AND TrangThai <> 'DA_HUY' "
            "GROUP BY DATEPART(HOUR, ThoiGianDat) ORDER BY Gio",
            (bd, kt),
        )
        theo_gio = fetch_all(cur)
    tong = sum(r["SoDon"] for r in theo_tt)
    huy = sum(r["SoDon"] for r in theo_tt if r["TrangThai"] == "DA_HUY")
    return _bao(
        khoang,
        TongQuan={"TongDon": tong, "SoDonHuy": huy, "SoDonKhongHuy": tong - huy,
                  "TiLeHuy": round(huy * 100 / tong, 1) if tong else 0},
        TheoTrangThai=theo_tt, TheoNgay=theo_ngay, TheoGio=theo_gio,
    ), None


# ---------- 73. Mon ban chay ----------
def mon_ban_chay(tu_ngay="", den_ngay="", gioi_han=10):
    khoang, err = _khoang(tu_ngay, den_ngay)
    if err:
        return None, err
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT TOP (?) c.MonID, MAX(c.TenMon) AS TenMon, SUM(c.SoLuong) AS SoLuong, "
            "SUM(c.ThanhTien) AS DoanhThu, COUNT(DISTINCT c.DonHangID) AS SoDon "
            "FROM dbo.ChiTietDonHang c JOIN dbo.DonHang d ON d.DonHangID = c.DonHangID "
            "WHERE d.TrangThai <> 'DA_HUY' AND d.ThoiGianDat >= ? AND d.ThoiGianDat < ? "
            "GROUP BY c.MonID ORDER BY SUM(c.SoLuong) DESC, SUM(c.ThanhTien) DESC, c.MonID",
            (_gioi_han(gioi_han), khoang[0], khoang[1]),
        )
        return _bao(khoang, items=fetch_all(cur)), None


# ---------- 74. Thanh toan ----------
def thanh_toan(tu_ngay="", den_ngay=""):
    khoang, err = _khoang(tu_ngay, den_ngay)
    if err:
        return None, err
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT PhuongThuc, TrangThai, COUNT(*) AS SoGiaoDich, SUM(SoTien) AS SoTien FROM dbo.ThanhToan "
            "WHERE NgayTao >= ? AND NgayTao < ? GROUP BY PhuongThuc, TrangThai ORDER BY PhuongThuc, TrangThai",
            (khoang[0], khoang[1]),
        )
        chi_tiet = fetch_all(cur)
    theo_pt = {}
    for r in chi_tiet:
        pt = theo_pt.setdefault(r["PhuongThuc"], {"PhuongThuc": r["PhuongThuc"], "SoGiaoDich": 0,
                                                  "SoDaThu": 0, "TienDaThu": Decimal("0")})
        pt["SoGiaoDich"] += r["SoGiaoDich"]
        if r["TrangThai"] in TT_DA_THU:
            pt["SoDaThu"] += r["SoGiaoDich"]
            pt["TienDaThu"] += Decimal(r["SoTien"])
    return _bao(khoang, TheoPhuongThuc=list(theo_pt.values()), ChiTiet=chi_tiet), None


# ---------- 75. Huy don va hoan tien ----------
def huy_va_hoan(tu_ngay="", den_ngay=""):
    khoang, err = _khoang(tu_ngay, den_ngay)
    if err:
        return None, err
    bd, kt = khoang[0], khoang[1]
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS SoDonHuy, COALESCE(SUM(TongTien), 0) AS GiaTriDonHuy FROM dbo.DonHang "
            "WHERE TrangThai = 'DA_HUY' AND ThoiGianDat >= ? AND ThoiGianDat < ?",
            (bd, kt),
        )
        huy = fetch_one(cur)
        cur.execute(
            "SELECT TOP 10 LyDoHuy, COUNT(*) AS SoDon FROM dbo.DonHang "
            "WHERE TrangThai = 'DA_HUY' AND ThoiGianDat >= ? AND ThoiGianDat < ? "
            "GROUP BY LyDoHuy ORDER BY COUNT(*) DESC, LyDoHuy",
            (bd, kt),
        )
        ly_do = fetch_all(cur)
        cur.execute(
            "SELECT COUNT(*) AS SoLanHoan, COALESCE(SUM(SoTienHoan), 0) AS TienHoan FROM dbo.HoanTien "
            "WHERE TrangThai = 'HOAN_THANH' AND NgayHoanTien >= ? AND NgayHoanTien < ?",
            (bd, kt),
        )
        hoan = fetch_one(cur)
        cur.execute(
            "SELECT TOP 50 h.HoanTienID, h.SoTienHoan, h.LyDo, h.NgayHoanTien, d.MaDonHang, p.PhuongThuc "
            "FROM dbo.HoanTien h JOIN dbo.ThanhToan p ON p.ThanhToanID = h.ThanhToanID "
            "JOIN dbo.DonHang d ON d.DonHangID = p.DonHangID "
            "WHERE h.TrangThai = 'HOAN_THANH' AND h.NgayHoanTien >= ? AND h.NgayHoanTien < ? "
            "ORDER BY h.NgayHoanTien DESC, h.HoanTienID DESC",
            (bd, kt),
        )
        ds_hoan = fetch_all(cur)
    return _bao(khoang, HuyDon=huy, LyDoHuy=ly_do, HoanTien=hoan, DanhSachHoan=ds_hoan), None


# ---------- 76. Ton kho ----------
def ton_kho(tu_ngay="", den_ngay=""):
    """Anh chup ton hien tai + bien dong kho trong khoang (theo loai, nguyen lieu dung nhieu)."""
    khoang, err = _khoang(tu_ngay, den_ngay)
    if err:
        return None, err
    bd, kt = khoang[0], khoang[1]
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS SoNguyenLieu, "
            "SUM(CASE WHEN SoLuongTon = 0 THEN 1 ELSE 0 END) AS SoHet, "
            "SUM(CASE WHEN SoLuongTon > 0 AND SoLuongTon <= MucTonToiThieu THEN 1 ELSE 0 END) AS SoSapHet, "
            "SUM(CASE WHEN SoLuongTon > MucTonToiThieu THEN 1 ELSE 0 END) AS SoDu "
            "FROM dbo.NguyenLieu WHERE TrangThai = 1"
        )
        tong = {k: (v or 0) for k, v in fetch_one(cur).items()}
        cur.execute(
            "SELECT LoaiGiaoDich, COUNT(*) AS SoGiaoDich FROM dbo.LichSuKho "
            "WHERE NgayGiaoDich >= ? AND NgayGiaoDich < ? GROUP BY LoaiGiaoDich ORDER BY LoaiGiaoDich",
            (bd, kt),
        )
        theo_loai = fetch_all(cur)
        cur.execute(
            "SELECT n.NguyenLieuID, n.TenNguyenLieu, n.DonViTinh, n.SoLuongTon, n.MucTonToiThieu, "
            "COALESCE(SUM(CASE WHEN l.SoLuongThayDoi > 0 THEN l.SoLuongThayDoi END), 0) AS TongNhap, "
            "COALESCE(-SUM(CASE WHEN l.SoLuongThayDoi < 0 THEN l.SoLuongThayDoi END), 0) AS TongXuat "
            "FROM dbo.NguyenLieu n LEFT JOIN dbo.LichSuKho l ON l.NguyenLieuID = n.NguyenLieuID "
            "AND l.NgayGiaoDich >= ? AND l.NgayGiaoDich < ? WHERE n.TrangThai = 1 "
            "GROUP BY n.NguyenLieuID, n.TenNguyenLieu, n.DonViTinh, n.SoLuongTon, n.MucTonToiThieu "
            "ORDER BY CASE WHEN n.SoLuongTon = 0 THEN 0 WHEN n.SoLuongTon <= n.MucTonToiThieu THEN 1 ELSE 2 END, "
            "n.TenNguyenLieu",
            (bd, kt),
        )
        ds = fetch_all(cur)
    return _bao(khoang, TongQuan=tong, TheoLoai=theo_loai, items=ds), None


# ---------- 77. Chi phi nhap hang ----------
def nhap_hang(tu_ngay="", den_ngay=""):
    khoang, err = _khoang(tu_ngay, den_ngay)
    if err:
        return None, err
    bd, kt = khoang[0], khoang[1]
    dk = "p.TrangThai = 'DA_NHAN' AND p.NgayXacNhan >= ? AND p.NgayXacNhan < ?"
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT COUNT(*) AS SoPhieu, COALESCE(SUM(p.TongTien), 0) AS TongChiPhi FROM dbo.PhieuNhap p WHERE {dk}",
            (bd, kt),
        )
        tong = fetch_one(cur)
        cur.execute(
            "SELECT n.NhaCungCapID, n.TenNhaCungCap, COUNT(*) AS SoPhieu, SUM(p.TongTien) AS TongChiPhi "
            f"FROM dbo.PhieuNhap p JOIN dbo.NhaCungCap n ON n.NhaCungCapID = p.NhaCungCapID WHERE {dk} "
            "GROUP BY n.NhaCungCapID, n.TenNhaCungCap ORDER BY SUM(p.TongTien) DESC, n.TenNhaCungCap",
            (bd, kt),
        )
        theo_ncc = fetch_all(cur)
        cur.execute(
            "SELECT TOP 20 nl.NguyenLieuID, nl.TenNguyenLieu, nl.DonViTinh, SUM(c.SoLuong) AS SoLuong, "
            "SUM(c.ThanhTien) AS ChiPhi FROM dbo.ChiTietPhieuNhap c "
            "JOIN dbo.PhieuNhap p ON p.PhieuNhapID = c.PhieuNhapID "
            f"JOIN dbo.NguyenLieu nl ON nl.NguyenLieuID = c.NguyenLieuID WHERE {dk} "
            "GROUP BY nl.NguyenLieuID, nl.TenNguyenLieu, nl.DonViTinh ORDER BY SUM(c.ThanhTien) DESC",
            (bd, kt),
        )
        theo_nl = fetch_all(cur)
        cur.execute(
            "SELECT CAST(p.NgayXacNhan AS DATE) AS Ngay, COUNT(*) AS SoPhieu, SUM(p.TongTien) AS ChiPhi "
            f"FROM dbo.PhieuNhap p WHERE {dk} GROUP BY CAST(p.NgayXacNhan AS DATE) ORDER BY Ngay",
            (bd, kt),
        )
        theo_ngay = fetch_all(cur)
    return _bao(khoang, TongQuan=tong, TheoNhaCungCap=theo_ncc, TheoNguyenLieu=theo_nl,
                TheoNgay=theo_ngay), None


# ---------- 78. Hieu qua khuyen mai ----------
def khuyen_mai(tu_ngay="", den_ngay=""):
    khoang, err = _khoang(tu_ngay, den_ngay)
    if err:
        return None, err
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT k.KhuyenMaiID, k.MaKhuyenMai, k.TenKhuyenMai, k.LoaiGiamGia, k.GiaTriGiam, "
            "COUNT(*) AS SoLuot, SUM(s.SoTienGiam) AS TongGiam, SUM(d.TongTien) AS TongTruocGiam, "
            "SUM(d.ThanhTien) AS TongSauGiam FROM dbo.SuDungKhuyenMai s "
            "JOIN dbo.DonHang d ON d.DonHangID = s.DonHangID "
            "JOIN dbo.KhuyenMai k ON k.KhuyenMaiID = s.KhuyenMaiID "
            "WHERE d.TrangThai <> 'DA_HUY' AND d.ThoiGianDat >= ? AND d.ThoiGianDat < ? "
            "GROUP BY k.KhuyenMaiID, k.MaKhuyenMai, k.TenKhuyenMai, k.LoaiGiamGia, k.GiaTriGiam "
            "ORDER BY COUNT(*) DESC, SUM(s.SoTienGiam) DESC",
            (khoang[0], khoang[1]),
        )
        ds = fetch_all(cur)
        cur.execute(
            "SELECT COUNT(*) FROM dbo.DonHang WHERE TrangThai <> 'DA_HUY' AND ThoiGianDat >= ? AND ThoiGianDat < ?",
            (khoang[0], khoang[1]),
        )
        tong_don = cur.fetchval()
    so_luot = sum(r["SoLuot"] for r in ds)
    return _bao(khoang, TongQuan={
        "SoDonDungKhuyenMai": so_luot,
        "TongDon": tong_don,
        "TiLeDung": round(so_luot * 100 / tong_don, 1) if tong_don else 0,
        "TongGiam": sum((Decimal(r["TongGiam"]) for r in ds), Decimal("0")),
    }, items=ds), None


# ---------- 79. Tong quan ----------
def tong_quan(tu_ngay="", den_ngay=""):
    khoang, err = _khoang(tu_ngay, den_ngay)
    if err:
        return None, err
    bd, kt = khoang[0], khoang[1]
    with closing(get_connection()) as conn:
        cur = conn.cursor()
        dt = _so_lieu_doanh_thu(cur, bd, kt)
        cur.execute(
            "SELECT COUNT(*) AS TongDon, SUM(CASE WHEN TrangThai = 'DA_HUY' THEN 1 ELSE 0 END) AS SoDonHuy "
            "FROM dbo.DonHang WHERE ThoiGianDat >= ? AND ThoiGianDat < ?",
            (bd, kt),
        )
        don = {k: (v or 0) for k, v in fetch_one(cur).items()}
        cur.execute(
            "SELECT COALESCE(SUM(TongTien), 0) FROM dbo.PhieuNhap "
            "WHERE TrangThai = 'DA_NHAN' AND NgayXacNhan >= ? AND NgayXacNhan < ?",
            (bd, kt),
        )
        chi_phi = cur.fetchval()
        cur.execute(
            "SELECT COUNT(*) FROM dbo.NguyenLieu WHERE TrangThai = 1 AND SoLuongTon <= MucTonToiThieu"
        )
        sap_het = cur.fetchval()
    top, _ = mon_ban_chay(tu_ngay, den_ngay, 5)
    return _bao(
        khoang,
        DoanhThu=dt["DoanhThu"], TienHoan=dt["TienHoan"], DoanhThuThuan=dt["DoanhThuThuan"],
        TongGiamGia=dt["TongGiamGia"], SoDonDaThu=dt["SoDonDaThu"],
        GiaTriTrungBinhDon=dt["GiaTriTrungBinhDon"], TongDon=don["TongDon"], SoDonHuy=don["SoDonHuy"],
        ChiPhiNhapHang=chi_phi, NguyenLieuCanNhap=sap_het, MonBanChay=top["items"],
    ), None
