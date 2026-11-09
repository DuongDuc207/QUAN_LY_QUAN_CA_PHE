"""So cai kho: MOI thay doi ton kho deu di qua day (QD06).

ghi_bien_dong() khoa dong NguyenLieu, kiem tra khong am, cap nhat SoLuongTon va ghi
LichSuKho trong CUNG giao dich cua nguoi goi. Ham nay khong commit / rollback:
nguoi goi tu commit khi xong, rollback khi gap loi.
Loi tra ve dang (None, (thong_bao, ma_http)) giong cac service khac.
"""

from decimal import Decimal, InvalidOperation

LOAI_GIAO_DICH = ("NHAP_HANG", "HUY_NHAP", "XUAT_KHO", "TIEU_HAO", "DIEU_CHINH")
# Loai chi duoc giam kho / chi duoc tang kho. DIEU_CHINH tang giam deu duoc.
LOAI_GIAM = ("HUY_NHAP", "XUAT_KHO", "TIEU_HAO")
LOAI_CAN_LY_DO = ("DIEU_CHINH", "XUAT_KHO")

SO_LUONG_TOI_DA = Decimal("1000000000")
_BA_SO = Decimal("0.001")


def so_luong(gia_tri):
    """Doi sang Decimal 3 chu so thap phan; None neu khong phai so huu han."""
    if isinstance(gia_tri, bool) or gia_tri in (None, ""):
        return None
    try:
        so = Decimal(str(gia_tri).strip()).quantize(_BA_SO)
    except (InvalidOperation, ValueError):
        return None
    return so if so.is_finite() and abs(so) <= SO_LUONG_TOI_DA else None


def ghi_bien_dong(cur, nguyen_lieu_id, tai_khoan_id, loai, thay_doi, ly_do=None,
                  don_hang_id=None, phieu_nhap_id=None):
    """Cong (thay_doi > 0) hoac tru (thay_doi < 0) ton kho mot nguyen lieu va ghi lich su."""
    if loai not in LOAI_GIAO_DICH:
        return None, ("Loai giao dich kho khong hop le", 400)
    thay_doi = so_luong(thay_doi)
    if thay_doi is None or thay_doi == 0:
        return None, ("So luong thay doi phai khac 0", 400)
    if (loai == "NHAP_HANG" and thay_doi < 0) or (loai in LOAI_GIAM and thay_doi > 0):
        return None, ("Chieu thay doi khong khop loai giao dich kho", 400)
    ly_do = ly_do.strip()[:500] if isinstance(ly_do, str) else ""
    if loai in LOAI_CAN_LY_DO and not ly_do:
        return None, ("Ly do la bat buoc", 400)

    cur.execute(
        "SELECT TenNguyenLieu, DonViTinh, SoLuongTon FROM dbo.NguyenLieu WITH (UPDLOCK, HOLDLOCK) "
        "WHERE NguyenLieuID = ?",
        (nguyen_lieu_id,),
    )
    nl = cur.fetchone()
    if not nl:
        return None, ("Nguyen lieu khong ton tai", 404)
    truoc = Decimal(nl.SoLuongTon)
    sau = truoc + thay_doi
    if sau < 0:
        return None, (
            f"Ton kho khong du: {nl.TenNguyenLieu} con {truoc:f} {nl.DonViTinh}, can {-thay_doi:f}",
            409,
        )

    cur.execute(
        "UPDATE dbo.NguyenLieu SET SoLuongTon = ?, NgayCapNhat = SYSDATETIME() WHERE NguyenLieuID = ?",
        (sau, nguyen_lieu_id),
    )
    cur.execute(
        "INSERT INTO dbo.LichSuKho (NguyenLieuID, TaiKhoanID, LoaiGiaoDich, SoLuongThayDoi, "
        "SoLuongTruoc, SoLuongSau, LyDo, DonHangID, PhieuNhapID) "
        "OUTPUT INSERTED.LichSuKhoID, INSERTED.NgayGiaoDich VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (nguyen_lieu_id, tai_khoan_id, loai, thay_doi, truoc, sau, ly_do or None, don_hang_id, phieu_nhap_id),
    )
    row = cur.fetchone()
    return {
        "LichSuKhoID": row[0],
        "NguyenLieuID": nguyen_lieu_id,
        "TenNguyenLieu": nl.TenNguyenLieu,
        "DonViTinh": nl.DonViTinh,
        "LoaiGiaoDich": loai,
        "SoLuongThayDoi": thay_doi,
        "SoLuongTruoc": truoc,
        "SoLuongSau": sau,
        "LyDo": ly_do or None,
        "NgayGiaoDich": row[1],
        "DonHangID": don_hang_id,
        "PhieuNhapID": phieu_nhap_id,
    }, None
